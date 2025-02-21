import subprocess
import uuid

import click


def ssh_pull_image(host: str, image: str, verbose: bool = False):
    """Pull docker image at remote host"""

    click.echo(
        click.style("Pulling image ") + click.style(image, fg="cyan") + click.style(" at ") + click.style(host, fg="cyan") + click.style("...")
    )
    _ssh_run(["ssh", host, "docker", "pull", image], "Pulling image done", "Pulling image failed", verbose)

    image_path = f"/tmp/{uuid.uuid4().hex[:7]}.tar.gz"

    click.echo(click.style("Saving image ") + click.style(image, fg="cyan") + click.style(f" to {image_path}..."))
    _ssh_run(["ssh", host, "docker", "save", image, "|", "gzip", ">", image_path], "Saving image done", "Saving image failed", verbose)

    click.echo(click.style("Copying ") + click.style(image_path, fg="cyan") + click.style(f" from {host} to local..."))
    _ssh_run(["scp", f"{host}:{image_path}", image_path], "Copying image done", "Copying image failed", verbose)

    click.echo(click.style("Removing ") + click.style(image_path, fg="cyan") + click.style(" at remote host..."))
    _ssh_run(["ssh", host, "rm", image_path], f"Removing {image_path} success", f"Removing {image_path} error", verbose)

    click.echo(click.style("Loading ") + click.style(image_path, fg="cyan") + click.style(" to local docker..."))
    _ssh_run(["docker", "load", "-i", image_path], "Loading image done", "Loading image failed", verbose)

    click.echo(click.style("Removing ") + click.style(image_path, fg="cyan") + click.style(" at local..."))
    _ssh_run(["rm", image_path], f"Removing {image_path} success", f"Removing {image_path} error", verbose)


def _ssh_run(cmd: list[str], success: str, fail: str, verbose: bool = False):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        click.echo(click.style(fail, fg="red"))
        click.echo(click.style(result.stderr, fg="red"))
        return
    if verbose and result.stdout:
        click.echo(click.style(result.stdout))
    click.echo(click.style(success, fg="green") + click.style(" ✅\n"))
