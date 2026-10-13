import io
import subprocess
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pifr.commands.ssh import _remove_remote_temp_dir
from pifr.main import cli


class CleanupWarningTests(unittest.TestCase):
    def test_pull_keeps_transfer_error_when_cleanup_fails(self):
        def run(command, *_args):
            if command[:3] == ["ssh", "remote", "umask"]:
                return subprocess.CompletedProcess(command, 7, "", "save failed")
            if command[:3] == ["ssh", "remote", "rm"]:
                return subprocess.CompletedProcess(command, 42, "", "permission denied")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("pifr.commands.ssh._run_command", side_effect=run):
            result = CliRunner().invoke(cli, ["pull", "remote", "alpine"])

        self.assertEqual(result.exit_code, 7, result.output)
        self.assertIn("Saving image failed", result.output)
        self.assertIn("Warning: Removing remote temporary directory failed: permission denied", result.output)

    def test_push_succeeds_when_cleanup_fails(self):
        def run(command, *_args):
            if command[:3] == ["docker", "save", "-o"]:
                Path(command[3]).write_bytes(b"archive")
            elif command[0] == "gzip":
                source = Path(command[-1])
                source.rename(source.with_suffix(".tar.gz"))
            elif command[:3] == ["ssh", "remote", "rm"]:
                return subprocess.CompletedProcess(command, 42, "", "permission denied")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("pifr.commands.ssh._run_command", side_effect=run):
            result = CliRunner().invoke(cli, ["push", "alpine", "remote"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Warning: Removing remote temporary directory failed: permission denied", result.output)

    def test_missing_ssh_during_cleanup_is_a_warning(self):
        output = io.StringIO()
        with patch("pifr.commands.ssh._run_command", side_effect=FileNotFoundError("ssh not found")), redirect_stderr(output):
            _remove_remote_temp_dir("remote", "/tmp/pifr-test", False)

        self.assertIn("Warning: Removing remote temporary directory failed: Command not found: ssh", output.getvalue())
