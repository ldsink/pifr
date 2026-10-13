import unittest
from unittest.mock import patch

import click
from click.testing import CliRunner

from pifr.commands.ssh import validate_host
from pifr.main import cli


class HostValidationTests(unittest.TestCase):
    def test_valid_ssh_destinations(self):
        for host in ("remote", "remote-host.example", "my_host", "user@remote-host"):
            with self.subTest(host=host):
                self.assertEqual(validate_host(host), host)

    def test_invalid_destinations_explain_allowed_form(self):
        for host in ("", "-oProxyCommand=touch/tmp/marker", "user@-oProxyCommand=bad", "remote:/tmp/file", "remote host", "remote\nname"):
            with self.subTest(host=host), self.assertRaises(click.BadParameter) as error:
                validate_host(host)
            self.assertIn("SSH host alias or user@host", str(error.exception))

    def test_invalid_host_stops_before_external_commands(self):
        with patch("pifr.commands.ssh._ssh_run") as run:
            for args in (("pull", "--", "-oProxyCommand=bad", "alpine"), ("push", "--", "alpine", "-oProxyCommand=bad")):
                with self.subTest(args=args):
                    result = CliRunner().invoke(cli, args)
                    self.assertEqual(result.exit_code, 2, result.output)
                    self.assertIn("Invalid value for HOST", result.output)
            run.assert_not_called()
