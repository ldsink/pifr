import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pifr.commands.host import get_ssh_host_info
from pifr.main import cli


class HostTests(unittest.TestCase):
    def test_list_preserves_ports_even_when_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / ".ssh"
            config_dir.mkdir()
            (config_dir / "config").write_text("Host valid\n  Port 2222\nHost invalid\n  Port not-a-number\n")

            with patch("pifr.commands.host.Path.home", return_value=Path(directory)):
                hosts = get_ssh_host_info()
                result = CliRunner().invoke(cli, ["list"])

        self.assertEqual([host.port for host in hosts], ["2222", "not-a-number"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("2222", result.output)
        self.assertIn("not-a-number", result.output)

    def test_list_resolves_includes_patterns_and_first_values(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / ".ssh"
            extra_dir = config_dir / "extra"
            extra_dir.mkdir(parents=True)
            (extra_dir / "hosts.conf").write_text("Host included\n  HostName included.example\n")
            (config_dir / "config").write_text(
                "Include extra/*.conf\nhost mixed\n  HostName mixed.example\nHost alpha beta\n  User first\nHost alpha\n  User second\nHost *\n  Port 2222\nMatch host mixed\n  User matched\n"
            )

            with patch("pifr.commands.host.Path.home", return_value=Path(directory)):
                hosts = get_ssh_host_info()

        self.assertEqual([host.name for host in hosts], ["included", "mixed", "alpha", "beta"])
        self.assertEqual([host.hostname for host in hosts], ["included.example", "mixed.example", None, None])
        self.assertEqual([host.user for host in hosts], [None, "matched", "first", "first"])
        self.assertEqual([host.port for host in hosts], ["2222"] * 4)

    def test_list_does_not_execute_match_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            config_dir = Path(directory) / ".ssh"
            config_dir.mkdir()
            marker = Path(directory) / "match-ran"
            (config_dir / "config").write_text(f'Host safe\n  User owner\nMatch exec "touch {marker}"\n  User attacker\n')

            with patch("pifr.commands.host.Path.home", return_value=Path(directory)):
                hosts = get_ssh_host_info()

            self.assertFalse(marker.exists())
        self.assertEqual([(host.name, host.user) for host in hosts], [("safe", "owner")])
