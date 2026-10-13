import re
import shlex
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import click

_NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
_DOMAIN_COMPONENT = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
_HOST = rf"(?:{_DOMAIN_COMPONENT}(?:\.{_DOMAIN_COMPONENT})*|\[[A-Fa-f0-9:]+\])"
_IMAGE_NAME = re.compile(rf"(?:{_HOST}(?::[0-9]+)?/)?{_NAME_COMPONENT}(?:/{_NAME_COMPONENT})*\Z")
_TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_DIGEST = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_+.][A-Za-z][A-Za-z0-9]*)*:[A-Fa-f0-9]{32,}\Z")
_ALLOWED_CHARACTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/@+-[]")
_SSH_HOST = re.compile(r"(?:[A-Za-z0-9_][A-Za-z0-9_.-]*@)?[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")


def validate_host(host: str) -> str:
    """Accept SSH aliases and user@host destinations without option or path syntax."""
    if not _SSH_HOST.fullmatch(host):
        raise click.BadParameter(
            "Use an SSH host alias or user@host containing letters, digits, dots, underscores, or hyphens; "
            "each part must start with a letter, digit, or underscore.",
            param_hint="HOST",
        )
    return host


def validate_image_name(image: str) -> str:
    """Validate a Docker image reference before using it in a remote command."""
    if not image:
        raise click.BadParameter("Image name cannot be empty; use a name such as alpine:latest.", param_hint="IMAGE")

    for position, character in enumerate(image, start=1):
        if character not in _ALLOWED_CHARACTERS:
            raise click.BadParameter(
                f"Invalid character {character!r} at position {position}; use a Docker image name without spaces or shell operators.",
                param_hint="IMAGE",
            )

    name_and_tag, separator, digest = image.partition("@")
    if separator and not _DIGEST.fullmatch(digest):
        raise click.BadParameter(
            "Invalid digest; use an algorithm and at least 32 hexadecimal digits, for example sha256:<64 hex digits>.", param_hint="IMAGE"
        )

    name = name_and_tag
    if ":" in name_and_tag.rsplit("/", 1)[-1]:
        name, tag = name_and_tag.rsplit(":", 1)
        if not _TAG.fullmatch(tag):
            raise click.BadParameter(
                "Invalid tag; start with a letter, digit, or underscore and use at most 128 letters, digits, underscores, dots, or hyphens.",
                param_hint="IMAGE",
            )

    first_component, _, remainder = name.partition("/")
    has_registry = bool(remainder) and (first_component == "localhost" or "." in first_component or ":" in first_component)
    repository = remainder if has_registry else name
    if any(character.isupper() for character in repository):
        raise click.BadParameter(
            "Repository path must be lowercase; uppercase letters are allowed only in the registry host or tag.", param_hint="IMAGE"
        )

    if not _IMAGE_NAME.fullmatch(name):
        raise click.BadParameter(
            "Invalid repository name; use lowercase path components separated by '/', optionally preceded by a registry host and port.",
            param_hint="IMAGE",
        )
    return image


def ssh_pull_image(host: str, image: str, verbose: bool = False):
    """Pull docker image at remote host"""
    host = validate_host(host)
    image = validate_image_name(image)

    click.echo(
        click.style("Pulling image ") + click.style(image, fg="cyan") + click.style(" at ") + click.style(host, fg="cyan") + click.style("...")
    )
    _ssh_run(["ssh", host, "docker", "pull", shlex.quote(image)], "Pulling image done", "Pulling image failed", verbose)

    remote_dir = _create_remote_temp_dir(host, verbose)
    image_path = f"{remote_dir}/image.tar.gz"
    try:
        click.echo(click.style("Saving image ") + click.style(image, fg="cyan") + click.style(f" to {image_path}..."))
        _ssh_run(
            ["ssh", host, "umask", "077", "&&", "set", "-o", "pipefail", "&&", "docker", "save", shlex.quote(image), "|", "gzip", ">", image_path],
            "Saving image done",
            "Saving image failed",
            verbose,
        )

        with tempfile.TemporaryDirectory(prefix="pifr-") as local_dir:
            local_path = Path(local_dir) / "image.tar.gz"
            click.echo(click.style("Copying ") + click.style(image_path, fg="cyan") + click.style(f" from {host} to local..."))
            _ssh_run(["scp", f"{host}:{image_path}", str(local_path)], "Copying image done", "Copying image failed", verbose)
            local_path.chmod(0o600)

            click.echo(click.style("Loading ") + click.style(str(local_path), fg="cyan") + click.style(" to local docker..."))
            _ssh_run(["docker", "load", "-i", str(local_path)], "Loading image done", "Loading image failed", verbose)
    finally:
        _remove_remote_temp_dir(host, remote_dir, verbose)


def ssh_push_image(image: str, host: str, verbose: bool = False):
    """Push docker image to remote host"""
    host = validate_host(host)
    image = validate_image_name(image)

    with tempfile.TemporaryDirectory(prefix="pifr-") as local_dir:
        tar_path = Path(local_dir) / "image.tar"
        click.echo(click.style("Saving image ") + click.style(image, fg="cyan") + click.style(f" to {tar_path}..."))
        _ssh_run(["docker", "save", "-o", str(tar_path), image], "Saving image done", "Saving image failed", verbose)
        tar_path.chmod(0o600)

        gz_path = tar_path.with_suffix(".tar.gz")
        click.echo(click.style("Compressing ") + click.style(str(tar_path), fg="cyan") + click.style(f" to {gz_path}..."))
        _ssh_run(["gzip", "-f", str(tar_path)], "Compressing done", "Compressing failed", verbose)
        gz_path.chmod(0o600)

        remote_dir = _create_remote_temp_dir(host, verbose)
        remote_path = f"{remote_dir}/image.tar.gz"
        try:
            click.echo(click.style("Copying ") + click.style(str(gz_path), fg="cyan") + click.style(f" to {host}..."))
            _ssh_run(["scp", str(gz_path), f"{host}:{remote_path}"], "Copying image done", "Copying image failed", verbose)
            _ssh_run(
                ["ssh", host, "chmod", "600", "--", remote_path],
                "Restricting remote image permissions done",
                "Restricting remote image permissions failed",
                verbose,
            )

            click.echo(click.style("Loading image ") + click.style(image, fg="cyan") + click.style(f" at {host}..."))
            _ssh_run(["ssh", host, "docker", "load", "-i", remote_path], "Loading image done", "Loading image failed", verbose)
        finally:
            _remove_remote_temp_dir(host, remote_dir, verbose)


def _create_remote_temp_dir(host: str, verbose: bool) -> str:
    remote_dir = f"/tmp/pifr-{uuid.uuid4().hex}"
    _ssh_run(
        ["ssh", host, "mkdir", "-m", "700", "--", remote_dir],
        "Creating remote temporary directory done",
        "Creating remote temporary directory failed",
        verbose,
    )
    return remote_dir


def _remove_remote_temp_dir(host: str, remote_dir: str, verbose: bool):
    _ssh_run(
        ["ssh", host, "rm", "-r", "--", remote_dir],
        "Removing remote temporary directory done",
        "Removing remote temporary directory failed",
        verbose,
        warn_only=True,
    )


def _ssh_run(cmd: list[str], success: str, fail: str, verbose: bool = False, *, warn_only: bool = False):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as error:
        detail = f"Command not found: {cmd[0]}" if isinstance(error, FileNotFoundError) else str(error)
        if warn_only:
            click.echo(click.style(f"Warning: {fail}: {detail}", fg="yellow"), err=True)
            return
        click.echo(click.style(fail, fg="red"))
        click.echo(click.style(detail, fg="red"))
        sys.exit(1)
    if result.returncode != 0:
        if warn_only:
            detail = result.stderr.strip()
            message = f"Warning: {fail}"
            if detail:
                message += f": {detail}"
            click.echo(click.style(message, fg="yellow"), err=True)
            return
        click.echo(click.style(fail, fg="red"))
        click.echo(click.style(result.stderr, fg="red"))
        sys.exit(result.returncode)
    if verbose and result.stdout:
        click.echo(click.style(result.stdout))
    click.echo(click.style(success, fg="green") + click.style(" ✅\n"))
