"""Execução local de submissões em contêineres Docker descartáveis."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import threading
import uuid
from typing import BinaryIO


MAX_SOURCE_BYTES = 50_000
MAX_OUTPUT_BYTES = 50_000
# Mantido como alias para compatibilidade com código que importava a constante.
MAX_OUTPUT_CHARS = MAX_OUTPUT_BYTES
DEFAULT_TIMEOUT_SECONDS = 5
OUTPUT_TRUNCATED_MESSAGE = "\n[saída truncada pelo CodeRank]"


@dataclass(frozen=True)
class SandboxConfig:
    image: str
    memory: str
    tmpfs_size: str


@dataclass(frozen=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        return not self.timed_out and self.exit_code == 0


SANDBOXES = {
    "python": SandboxConfig(
        image=os.getenv("CODERANK_PYTHON_IMAGE", "coderank-python:latest"),
        memory="128m",
        tmpfs_size="64m",
    ),
    "java": SandboxConfig(
        image=os.getenv("CODERANK_JAVA_IMAGE", "coderank-java:latest"),
        memory="256m",
        tmpfs_size="128m",
    ),
}


def _build_command(
    language: str,
    container_name: str,
    docker_binary: str = "docker",
) -> list[str]:
    """Monta o comando Docker sem interpolar código do usuário no shell."""

    try:
        config = SANDBOXES[language]
    except KeyError as exc:
        raise ValueError(f"Linguagem não suportada: {language}.") from exc

    return [
        docker_binary,
        "run",
        "--rm",
        "--interactive",
        "--init",
        "--pull",
        "never",
        "--name",
        container_name,
        "--user",
        "10001:10001",
        "--network",
        "none",
        "--memory",
        config.memory,
        "--memory-swap",
        config.memory,
        "--cpus",
        "0.5",
        "--pids-limit",
        "64",
        "--ulimit",
        "nofile=64:64",
        "--read-only",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,size={config.tmpfs_size},mode=1777",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        config.image,
    ]


def _read_bounded(stream: BinaryIO, limit: int = MAX_OUTPUT_BYTES) -> tuple[bytes, bool]:
    """Drena um pipe inteiro, mas mantém em memória somente os primeiros bytes."""

    collected = bytearray()
    truncated = False

    while True:
        chunk = stream.read(8192)
        if not chunk:
            break

        remaining = limit - len(collected)
        if remaining > 0:
            collected.extend(chunk[:remaining])
        if len(chunk) > remaining:
            truncated = True

    return bytes(collected), truncated


def _trim_output(output: bytes, truncated: bool = False) -> str:
    text = output.decode("utf-8", errors="replace")
    if truncated:
        return text + OUTPUT_TRUNCATED_MESSAGE
    return text


def _friendly_stderr(
    stderr: bytes,
    language: str,
    truncated: bool = False,
) -> str:
    message = _trim_output(stderr, truncated)
    normalized = message.casefold()

    daemon_errors = (
        "failed to connect to the docker api",
        "cannot connect to the docker daemon",
        "is the docker daemon running",
        "the system cannot find the file specified",
        "o sistema não pode encontrar o arquivo especificado",
    )
    if any(error in normalized for error in daemon_errors):
        return "Docker Desktop está indisponível. Inicie o motor Docker e tente novamente."

    image_errors = (
        "pull access denied",
        "unable to find image",
        "no such image",
    )
    if any(error in normalized for error in image_errors):
        image = SANDBOXES[language].image
        return (
            f"A imagem {image} ainda não foi construída. "
            "Execute: docker compose build"
        )

    return message


def _stop_container(
    docker_binary: str,
    container_name: str,
    creation_flags: int,
) -> None:
    """Solicita ao daemon Docker a remoção do contêiner, não apenas do cliente."""

    try:
        subprocess.run(
            [docker_binary, "rm", "--force", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
            check=False,
            creationflags=creation_flags,
        )
    except (OSError, subprocess.SubprocessError):
        # O processo cliente ainda será encerrado pelo chamador.
        pass


def run_code(
    language: str,
    source_code: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    docker_binary: str = "docker",
) -> ExecutionResult:
    """Executa código sem rede, como usuário sem privilégios e com limites rígidos.

    A coleta de stdout/stderr é feita em threads que continuam drenando os pipes,
    descartando bytes excedentes. Assim, uma submissão que imprime sem parar não
    consegue fazer o processo hospedeiro acumular saída ilimitada em memória.
    """

    if not isinstance(language, str):
        raise ValueError("Informe uma linguagem suportada.")
    normalized_language = language.strip().lower()
    if normalized_language not in SANDBOXES:
        supported = ", ".join(sorted(SANDBOXES))
        raise ValueError(f"Linguagem não suportada. Use: {supported}.")

    if not isinstance(source_code, str) or not source_code.strip():
        raise ValueError("Digite algum código antes de executar.")

    source_bytes = source_code.encode("utf-8")
    if len(source_bytes) > MAX_SOURCE_BYTES:
        raise ValueError("O código ultrapassa o limite de 50 KB.")

    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, int)
        or not 1 <= timeout_seconds <= 30
    ):
        raise ValueError("O timeout deve ser um número inteiro entre 1 e 30 segundos.")

    container_name = f"coderank-run-{uuid.uuid4().hex}"
    command = _build_command(normalized_language, container_name, docker_binary)
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Docker não foi encontrado. Instale e inicie o Docker Desktop."
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            "Não foi possível iniciar o Docker. Verifique a instalação e as permissões."
        ) from exc

    captured: dict[str, tuple[bytes, bool]] = {}

    def consume_output(name: str, stream: BinaryIO | None) -> None:
        if stream is None:
            captured[name] = (b"", False)
            return
        captured[name] = _read_bounded(stream)

    readers = [
        threading.Thread(
            target=consume_output,
            args=("stdout", process.stdout),
            daemon=True,
        ),
        threading.Thread(
            target=consume_output,
            args=("stderr", process.stderr),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()

    def send_source() -> None:
        if process.stdin is None:
            return
        try:
            process.stdin.write(source_bytes)
            process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            # O contêiner pode encerrar antes de consumir toda a entrada.
            pass
        finally:
            try:
                process.stdin.close()
            except OSError:
                pass

    writer = threading.Thread(target=send_source, daemon=True)
    writer.start()

    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _stop_container(docker_binary, container_name, creation_flags)
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    finally:
        writer.join(timeout=1)
        for reader in readers:
            reader.join(timeout=3)

        # Em condições normais os pipes já chegaram ao EOF. Fechá-los também
        # evita manter descritores abertos se o cliente Docker falhar.
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                try:
                    stream.close()
                except OSError:
                    pass

    stdout_bytes, stdout_truncated = captured.get("stdout", (b"", False))
    stderr_bytes, stderr_truncated = captured.get("stderr", (b"", False))

    stdout = _trim_output(stdout_bytes, stdout_truncated)
    stderr = _friendly_stderr(
        stderr_bytes,
        normalized_language,
        stderr_truncated,
    )

    if timed_out:
        timeout_message = f"Tempo limite de {timeout_seconds}s excedido."
        stderr = f"{stderr}\n{timeout_message}".strip()

    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=124 if timed_out else (process.returncode or 0),
        timed_out=timed_out,
    )
