import re
import shlex
import subprocess
import sys
import uuid

import click

_NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
_DOMAIN_COMPONENT = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
_HOST = rf"(?:{_DOMAIN_COMPONENT}(?:\.{_DOMAIN_COMPONENT})*|\[[A-Fa-f0-9:]+\])"
_IMAGE_NAME = re.compile(rf"(?:{_HOST}(?::[0-9]+)?/)?{_NAME_COMPONENT}(?:/{_NAME_COMPONENT})*\Z")
_TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}\Z")
_DIGEST = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_+.][A-Za-z][A-Za-z0-9]*)*:[A-Fa-f0-9]{32,}\Z")
_ALLOWED_CHARACTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/@+-[]")


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
    image = validate_image_name(image)

    click.echo(
        click.style("Pulling image ") + click.style(image, fg="cyan") + click.style(" at ") + click.style(host, fg="cyan") + click.style("...")
    )
    _ssh_run(["ssh", host, "docker", "pull", shlex.quote(image)], "Pulling image done", "Pulling image failed", verbose)

    image_path = f"/tmp/{uuid.uuid4().hex[:7]}.tar.gz"

    click.echo(click.style("Saving image ") + click.style(image, fg="cyan") + click.style(f" to {image_path}..."))
    _ssh_run(
        ["ssh", host, "set", "-o", "pipefail", "&&", "docker", "save", shlex.quote(image), "|", "gzip", ">", image_path],
        "Saving image done",
        "Saving image failed",
        verbose,
    )

    click.echo(click.style("Copying ") + click.style(image_path, fg="cyan") + click.style(f" from {host} to local..."))
    _ssh_run(["scp", f"{host}:{image_path}", image_path], "Copying image done", "Copying image failed", verbose)

    click.echo(click.style("Removing ") + click.style(image_path, fg="cyan") + click.style(" at remote host..."))
    _ssh_run(["ssh", host, "rm", image_path], f"Removing {image_path} success", f"Removing {image_path} error", verbose)

    click.echo(click.style("Loading ") + click.style(image_path, fg="cyan") + click.style(" to local docker..."))
    _ssh_run(["docker", "load", "-i", image_path], "Loading image done", "Loading image failed", verbose)

    click.echo(click.style("Removing ") + click.style(image_path, fg="cyan") + click.style(" at local..."))
    _ssh_run(["rm", image_path], f"Removing {image_path} success", f"Removing {image_path} error", verbose)


def ssh_push_image(image: str, host: str, verbose: bool = False):
    """Push docker image to remote host"""
    image = validate_image_name(image)

    tar_path = f"/tmp/{uuid.uuid4().hex[:7]}.tar"

    click.echo(click.style("Saving image ") + click.style(image, fg="cyan") + click.style(f" to {tar_path}..."))
    _ssh_run(["docker", "save", "-o", tar_path, image], "Saving image done", "Saving image failed", verbose)

    gz_path = f"{tar_path}.gz"
    click.echo(click.style("Compressing ") + click.style(tar_path, fg="cyan") + click.style(f" to {gz_path}..."))
    _ssh_run(["gzip", "-f", tar_path], "Compressing done", "Compressing failed", verbose)

    click.echo(click.style("Copying ") + click.style(gz_path, fg="cyan") + click.style(f" to {host}..."))
    _ssh_run(["scp", gz_path, f"{host}:{gz_path}"], "Copying image done", "Copying image failed", verbose)

    click.echo(click.style("Loading image ") + click.style(image, fg="cyan") + click.style(f" at {host}..."))
    _ssh_run(["ssh", host, "docker", "load", "-i", gz_path], "Loading image done", "Loading image failed", verbose)

    click.echo(click.style("Removing ") + click.style(gz_path, fg="cyan") + click.style(" at local..."))
    _ssh_run(["rm", gz_path], f"Removing {gz_path} success", f"Removing {gz_path} error", verbose)

    click.echo(click.style("Removing ") + click.style(gz_path, fg="cyan") + click.style(f" at {host}..."))
    _ssh_run(["ssh", host, "rm", gz_path], f"Removing {gz_path} success", f"Removing {gz_path} error", verbose)


def _ssh_run(cmd: list[str], success: str, fail: str, verbose: bool = False):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        click.echo(click.style(fail, fg="red"))
        click.echo(click.style(f"Command not found: {cmd[0]}", fg="red"))
        sys.exit(1)
    if result.returncode != 0:
        click.echo(click.style(fail, fg="red"))
        click.echo(click.style(result.stderr, fg="red"))
        sys.exit(result.returncode)
    if verbose and result.stdout:
        click.echo(click.style(result.stdout))
    click.echo(click.style(success, fg="green") + click.style(" ✅\n"))
