import io
import subprocess
import unittest
from unittest.mock import patch

from src.services.code_runner import (
    MAX_OUTPUT_BYTES,
    OUTPUT_TRUNCATED_MESSAGE,
    _build_command,
    run_code,
)


class FakeProcess:
    def __init__(self, stdout=b"ok\n", stderr=b"", returncode=0, timeout=False):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self._timeout = timeout
        self.killed = False

    def wait(self, timeout=None):
        if self._timeout and not self.killed:
            raise subprocess.TimeoutExpired("docker", timeout)
        return self.returncode

    def poll(self):
        return None if self._timeout and not self.killed else self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class CodeRunnerTests(unittest.TestCase):
    def test_command_applies_isolation_and_resource_limits(self):
        command = _build_command("python", "submission-test")

        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("--pids-limit", command)
        self.assertIn("--memory-swap", command)
        self.assertIn("--user", command)
        self.assertIn("10001:10001", command)
        self.assertIn("--security-opt", command)
        self.assertIn("--init", command)
        self.assertEqual("coderank-python:latest", command[-1])

    def test_uses_java_image_for_java(self):
        command = _build_command("java", "submission-test")
        self.assertEqual("coderank-java:latest", command[-1])

    def test_rejects_unsupported_language(self):
        with self.assertRaisesRegex(ValueError, "não suportada"):
            run_code("javascript", "console.log('oi')")

    def test_rejects_non_string_language(self):
        with self.assertRaisesRegex(ValueError, "linguagem"):
            run_code(None, "print('oi')")

    def test_rejects_empty_source(self):
        with self.assertRaisesRegex(ValueError, "Digite algum código"):
            run_code("python", "   ")

    def test_rejects_source_over_50_kb(self):
        with self.assertRaisesRegex(ValueError, "50 KB"):
            run_code("python", "x" * (MAX_OUTPUT_BYTES + 1))

    def test_rejects_invalid_timeout(self):
        for timeout in (0, 31, 1.5, True):
            with self.subTest(timeout=timeout):
                with self.assertRaisesRegex(ValueError, "timeout"):
                    run_code("python", "print('ok')", timeout_seconds=timeout)

    @patch("src.services.code_runner.subprocess.Popen")
    def test_returns_container_output(self, popen):
        process = FakeProcess()
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertTrue(result.succeeded)
        self.assertEqual("ok\n", result.stdout)
        self.assertEqual("", result.stderr)
        command = popen.call_args.args[0]
        self.assertEqual("coderank-python:latest", command[-1])
        self.assertTrue(process.stdin.closed)

    @patch("src.services.code_runner.subprocess.Popen")
    def test_caps_output_while_draining_pipe(self, popen):
        process = FakeProcess(stdout=b"x" * (MAX_OUTPUT_BYTES + 100_000))
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertLessEqual(
            len(result.stdout.encode("utf-8")),
            MAX_OUTPUT_BYTES + len(OUTPUT_TRUNCATED_MESSAGE.encode("utf-8")),
        )
        self.assertTrue(result.stdout.endswith(OUTPUT_TRUNCATED_MESSAGE))

    @patch("src.services.code_runner.subprocess.Popen")
    def test_translates_docker_daemon_error(self, popen):
        process = FakeProcess(
            stdout=b"",
            stderr=b"failed to connect to the docker API at npipe://docker_engine",
            returncode=125,
        )
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertFalse(result.succeeded)
        self.assertIn("Docker Desktop está indisponível", result.stderr)

    @patch("src.services.code_runner.subprocess.run")
    @patch("src.services.code_runner.subprocess.Popen")
    def test_removes_container_after_timeout(self, popen, docker_run):
        process = FakeProcess(stdout=b"", stderr=b"", timeout=True)
        popen.return_value = process

        result = run_code("python", "while True: pass")

        self.assertTrue(result.timed_out)
        self.assertEqual(124, result.exit_code)
        self.assertIn("Tempo limite", result.stderr)
        self.assertEqual("rm", docker_run.call_args.args[0][1])
        self.assertTrue(process.killed)

    @patch(
        "src.services.code_runner.subprocess.Popen",
        side_effect=FileNotFoundError("docker"),
    )
    def test_explains_when_docker_is_missing(self, popen):
        with self.assertRaisesRegex(RuntimeError, "Docker não foi encontrado"):
            run_code("python", "print('ok')")


if __name__ == "__main__":
    unittest.main()
