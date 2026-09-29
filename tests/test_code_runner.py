import subprocess
import unittest
from unittest.mock import MagicMock, patch

from src.services.code_runner import _build_command, run_code


class CodeRunnerTests(unittest.TestCase):
    def test_command_applies_isolation_limits(self):
        command = _build_command("python", "submission-test")

        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("--pids-limit", command)
        self.assertEqual("coderank-python:latest", command[-1])

    def test_rejects_unsupported_language(self):
        with self.assertRaisesRegex(ValueError, "não suportada"):
            run_code("javascript", "console.log('oi')")

    def test_rejects_empty_source(self):
        with self.assertRaisesRegex(ValueError, "Digite algum código"):
            run_code("python", "   ")

    @patch("src.services.code_runner.subprocess.Popen")
    def test_returns_container_output(self, popen):
        process = MagicMock()
        process.communicate.return_value = (b"ok\n", b"")
        process.returncode = 0
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertTrue(result.succeeded)
        self.assertEqual("ok\n", result.stdout)
        process.communicate.assert_called_once_with(b"print('ok')", timeout=5)

    @patch("src.services.code_runner.subprocess.Popen")
    def test_translates_docker_daemon_error(self, popen):
        process = MagicMock()
        process.communicate.return_value = (
            b"",
            b"failed to connect to the docker API at npipe:////./pipe/docker_engine",
        )
        process.returncode = 125
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertFalse(result.succeeded)
        self.assertIn("Docker Desktop está indisponível", result.stderr)

    @patch("src.services.code_runner.subprocess.Popen")
    def test_translates_docker_permission_error(self, popen):
        process = MagicMock()
        process.communicate.return_value = (
            b"",
            b"permission denied while trying to connect to the docker API",
        )
        process.returncode = 1
        popen.return_value = process

        result = run_code("python", "print('ok')")

        self.assertIn("Docker Desktop está indisponível", result.stderr)

    @patch("src.services.code_runner.subprocess.run")
    @patch("src.services.code_runner.subprocess.Popen")
    def test_removes_container_after_timeout(self, popen, run):
        process = MagicMock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired("docker", 5),
            (b"", b""),
        ]
        popen.return_value = process

        result = run_code("python", "while True: pass")

        self.assertTrue(result.timed_out)
        self.assertEqual(124, result.exit_code)
        self.assertIn("Tempo limite", result.stderr)
        self.assertEqual("rm", run.call_args.args[0][1])


if __name__ == "__main__":
    unittest.main()
