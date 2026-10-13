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
