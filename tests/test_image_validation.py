import unittest
from pathlib import Path
from unittest.mock import patch

import click
from click.testing import CliRunner

from pifr.commands.ssh import validate_image_name
from pifr.main import cli


class ImageValidationTests(unittest.TestCase):
    def test_valid_image_references(self):
        digest = "a" * 64
        for image in (
            "alpine",
            "alpine:latest",
            "my-registry.example:5000/team/my_image:Release-1",
            "[::1]:5000/team/image:tag",
            f"alpine@sha256:{digest}",
            f"example.com/team/image:tag@sha256:{digest}",
        ):
            with self.subTest(image=image):
                self.assertEqual(validate_image_name(image), image)

    def test_invalid_image_references_explain_the_reason(self):
        cases = {
            "": "cannot be empty",
            "alpine; touch /tmp/marker": "Invalid character ';'",
            "alpine$(id)": "Invalid character '$'",
            "alpine latest": "Invalid character ' '",
            "Team/image": "Repository path must be lowercase",
            "team//image": "Invalid repository name",
            "alpine:": "Invalid tag",
            "alpine@sha256:abc": "Invalid digest",
            "--help": "Invalid repository name",
        }
        for image, reason in cases.items():
            with self.subTest(image=image), self.assertRaises(click.BadParameter) as error:
                validate_image_name(image)
            self.assertIn(reason, str(error.exception))

    def test_invalid_image_stops_before_external_commands(self):
        runner = CliRunner()
        with patch("pifr.commands.ssh._ssh_run") as run:
            for args in (("pull", "remote", "alpine; touch /tmp/marker"), ("push", "alpine; touch /tmp/marker", "remote")):
                with self.subTest(args=args):
                    result = runner.invoke(cli, args)
                    self.assertEqual(result.exit_code, 2)
                    self.assertIn("Invalid character ';'", result.output)
            run.assert_not_called()

    def test_remote_image_is_shell_quoted(self):
        def copy_remote_archive(command, *_args):
            if command[0] == "scp":
                Path(command[-1]).write_bytes(b"archive")

        with patch("pifr.commands.ssh._ssh_run", side_effect=copy_remote_archive) as run:
            result = CliRunner().invoke(cli, ("pull", "remote", "[::1]:5000/team/image:tag"))
        self.assertEqual(result.exit_code, 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][-1], "'[::1]:5000/team/image:tag'")
        self.assertEqual(commands[2][11], "'[::1]:5000/team/image:tag'")


if __name__ == "__main__":
    unittest.main()
