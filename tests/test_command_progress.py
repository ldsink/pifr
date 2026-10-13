import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from pifr.commands.ssh import _ERROR_OUTPUT_LIMIT, _run_command, _ssh_run


class CommandProgressTests(unittest.TestCase):
    def test_verbose_output_is_streamed_before_command_finishes(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "received-output"
            script = (
                "import pathlib, sys, time\n"
                "print('ready', flush=True)\n"
                f"marker = pathlib.Path({str(marker)!r})\n"
                "for _ in range(100):\n"
                "    if marker.exists():\n"
                "        break\n"
                "    time.sleep(0.01)\n"
                "else:\n"
                "    sys.exit(9)\n"
                "print('done', flush=True)\n"
            )
            output = []

            def show(message, **_kwargs):
                output.append(message)
                if "ready" in "".join(output):
                    marker.touch()

            with patch("pifr.commands.ssh.click.echo", side_effect=show), patch("pifr.commands.ssh._COMMAND_TIMEOUT", 2):
                result = _run_command([sys.executable, "-c", script], True, "Running")

        self.assertEqual(result.returncode, 0)
        self.assertIn("done", "".join(output))

    def test_error_output_is_bounded(self):
        script = "import sys; sys.stderr.write('x' * 70000)"
        result = _run_command([sys.executable, "-c", script], False, "Running")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stderr), _ERROR_OUTPUT_LIMIT)

    def test_timeout_stops_a_stalled_command_and_reports_elapsed_time(self):
        output = io.StringIO()
        with (
            patch("pifr.commands.ssh._COMMAND_TIMEOUT", 0.2),
            patch("pifr.commands.ssh._PROGRESS_INTERVAL", 0.05),
            redirect_stderr(output),
            self.assertRaises(subprocess.TimeoutExpired),
        ):
            _run_command([sys.executable, "-c", "import time; time.sleep(5)"], False, "Running")
        self.assertIn("elapsed", output.getvalue())

    def test_scp_inherits_terminal_stderr_for_native_progress(self):
        with (
            patch("pifr.commands.ssh.sys.stderr.isatty", return_value=True),
            patch("pifr.commands.ssh.subprocess.Popen", side_effect=FileNotFoundError("scp missing")) as spawn,
            self.assertRaises(FileNotFoundError),
        ):
            _run_command(["scp", "source", "target"], False, "Copying")

        self.assertIsNone(spawn.call_args.kwargs["stderr"])
        self.assertIsNone(spawn.call_args.kwargs["stdout"])
        self.assertEqual(spawn.call_args.args[0][:3], ["scp", "-o", "ConnectTimeout=15"])

    def test_cleanup_timeout_is_only_a_warning(self):
        output = io.StringIO()
        with patch("pifr.commands.ssh._run_command", side_effect=subprocess.TimeoutExpired(["ssh"], 1)) as run, redirect_stderr(output):
            _ssh_run(["ssh", "remote", "rm"], "Removed", "Remove failed", warn_only=True)
        self.assertIn("Warning: Remove failed: timed out", output.getvalue())
        self.assertEqual(run.call_args.args[-1], 60)
