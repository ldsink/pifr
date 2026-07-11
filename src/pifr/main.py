import click

from pifr.commands.host import get_ssh_host_info, rich_print_hosts
from pifr.commands.ssh import ssh_pull_image, ssh_push_image


@click.group(epilog=("\b\nExamples:\n  pifr list\n  pifr pull remote-host alpine:latest\n  pifr push alpine:latest remote-host"))
@click.version_option(package_name="pifr", prog_name="pifr")
def cli():
    """Pull docker image from remote host, or push local image to remote host."""


@cli.command(name="list")
def list_hosts():
    """列出 SSH 配置中的主机 List hosts from ~/.ssh/config."""
    if hosts := get_ssh_host_info():
        rich_print_hosts(hosts)
    else:
        click.echo(click.style("No hosts found in ~/.ssh/config", fg="yellow"))


@cli.command(name="pull")
@click.argument("host", type=str)
@click.argument("image", type=str)
@click.option("--verbose", is_flag=True, help="Show command stdout/stderr")
def pull_image(host: str, image: str, verbose: bool):
    """在远端主机拉取镜像，保存并导入到本地 Pull image at remote host and save it to local.

    HOST is the SSH host name from ~/.ssh/config.

    IMAGE is the Docker image name, e.g. alpine:latest.
    """
    ssh_pull_image(host, image, verbose)


@cli.command(name="push")
@click.argument("image", type=str)
@click.argument("host", type=str)
@click.option("--verbose", is_flag=True, help="Show command stdout/stderr")
def push_image(image: str, host: str, verbose: bool):
    """将本地镜像保存并推送到远端主机 Push local image to remote host.

    IMAGE is the Docker image name, e.g. alpine:latest.

    HOST is the SSH host name from ~/.ssh/config.
    """
    ssh_push_image(image, host, verbose)


if __name__ == "__main__":
    cli()
