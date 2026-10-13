import stat
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pifr.main import cli


class TempPermissionsTests(unittest.TestCase):
    def test_pull_uses_private_directories_and_files(self):
        inspected = {}

        def run(command, *_args):
            if command[0] == "scp":
                Path(command[-1]).write_bytes(b"archive")
            elif command[:3] == ["docker", "load", "-i"]:
                archive = Path(command[-1])
                inspected["file_mode"] = stat.S_IMODE(archive.stat().st_mode)
                inspected["directory_mode"] = stat.S_IMODE(archive.parent.stat().st_mode)
                inspected["directory"] = archive.parent

        with patch("pifr.commands.ssh._ssh_run", side_effect=run) as mocked:
            result = CliRunner().invoke(cli, ("pull", "remote", "alpine:latest"))

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(inspected["file_mode"], 0o600)
        self.assertEqual(inspected["directory_mode"], 0o700)
        self.assertFalse(inspected["directory"].exists())
        commands = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(commands[1][2:6], ["mkdir", "-m", "700", "--"])
        self.assertEqual(commands[2][2:5], ["umask", "077", "&&"])
        self.assertEqual(commands[-1][2:5], ["rm", "-r", "--"])

    def test_push_restricts_local_and_remote_archives(self):
        inspected = {}

        def run(command, *_args):
            if command[:3] == ["docker", "save", "-o"]:
                archive = Path(command[3])
                archive.write_bytes(b"archive")
                inspected["directory"] = archive.parent
            elif command[0] == "gzip":
                source = Path(command[-1])
                inspected["tar_mode"] = stat.S_IMODE(source.stat().st_mode)
                source.rename(source.with_suffix(".tar.gz"))
            elif command[0] == "scp":
                archive = Path(command[1])
                inspected["compressed_mode"] = stat.S_IMODE(archive.stat().st_mode)
                inspected["directory_mode"] = stat.S_IMODE(archive.parent.stat().st_mode)

        with patch("pifr.commands.ssh._ssh_run", side_effect=run) as mocked:
            result = CliRunner().invoke(cli, ("push", "alpine:latest", "remote"))

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(inspected["tar_mode"], 0o600)
        self.assertEqual(inspected["compressed_mode"], 0o600)
        self.assertEqual(inspected["directory_mode"], 0o700)
        self.assertFalse(inspected["directory"].exists())
        commands = [call.args[0] for call in mocked.call_args_list]
        self.assertEqual(commands[2][2:6], ["mkdir", "-m", "700", "--"])
        self.assertEqual(commands[-3][:5], ["ssh", "remote", "chmod", "600", "--"])
        self.assertEqual(commands[-3][-1], f"{commands[2][-1]}/image.tar.gz")
        self.assertEqual(commands[-1][2:5], ["rm", "-r", "--"])

    def test_failure_removes_private_directories(self):
        local_directory = None

        def run(command, *_args):
            nonlocal local_directory
            if command[0] == "scp":
                local_directory = Path(command[-1]).parent
                raise SystemExit(1)

        with patch("pifr.commands.ssh._ssh_run", side_effect=run) as mocked:
            result = CliRunner().invoke(cli, ("pull", "remote", "alpine:latest"))

        self.assertEqual(result.exit_code, 1)
        self.assertFalse(local_directory.exists())
        self.assertEqual(mocked.call_args_list[-1].args[0][2:5], ["rm", "-r", "--"])


if __name__ == "__main__":
    unittest.main()
