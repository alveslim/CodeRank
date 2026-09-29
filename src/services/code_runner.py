"""Execução local de submissões em contêineres Docker descartáveis."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
import uuid


MAX_SOURCE_BYTES = 50_000
MAX_OUTPUT_CHARS = 50_000
DEFAULT_TIMEOUT_SECONDS = 5


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
    config = SANDBOXES[language]
    return [
        docker_binary,
        "run",
        "--rm",
        "--interactive",
        "--pull",
        "never",
        "--name",
        container_name,
        "--network",
        "none",
        "--memory",
        config.memory,
        "--cpus",
        "0.5",
        "--pids-limit",
        "64",
        "--read-only",
        "--tmpfs",
        f"/tmp:rw,noexec,nosuid,size={config.tmpfs_size},mode=1777",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        config.image,
    ]


def _trim_output(output: bytes) -> str:
    text = output.decode("utf-8", errors="replace")
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n[saída truncada pelo CodeRank]"


def _friendly_stderr(stderr: bytes, language: str) -> str:
    message = _trim_output(stderr)
    normalized = message.lower()

    daemon_errors = (
        "failed to connect to the docker api",
        "cannot connect to the docker daemon",
        "permission denied while trying to connect to the docker api",
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


def run_code(
    language: str,
    source_code: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    docker_binary: str = "docker",
) -> ExecutionResult:
    """Executa código sem rede e com limites de CPU, memória, processos e tempo."""

    normalized_language = language.strip().lower()
    if normalized_language not in SANDBOXES:
        supported = ", ".join(sorted(SANDBOXES))
        raise ValueError(f"Linguagem não suportada. Use: {supported}.")

    if not source_code.strip():
        raise ValueError("Digite algum código antes de executar.")

    if len(source_code.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("O código ultrapassa o limite de 50 KB.")

    if not 1 <= timeout_seconds <= 30:
        raise ValueError("O timeout deve estar entre 1 e 30 segundos.")

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

    try:
        stdout, stderr = process.communicate(
            source_code.encode("utf-8"),
            timeout=timeout_seconds,
        )
        return ExecutionResult(
            stdout=_trim_output(stdout),
            stderr=_friendly_stderr(stderr, normalized_language),
            exit_code=process.returncode,
        )
    except subprocess.TimeoutExpired:
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
            pass
        finally:
            process.kill()
        stdout, stderr = process.communicate()
        timeout_message = f"Tempo limite de {timeout_seconds}s excedido."
        previous_error = _trim_output(stderr).strip()
        return ExecutionResult(
            stdout=_trim_output(stdout),
            stderr=f"{previous_error}\n{timeout_message}".strip(),
            exit_code=124,
            timed_out=True,
        )
