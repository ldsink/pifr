import click

from pifr.commands.host import get_ssh_host_info, rich_print_hosts
from pifr.commands.ssh import ssh_pull_image


@click.group()
def cli():
    """Pull docker image from remote host."""


@cli.command(name="list")
def list_hosts():
    """列出主机 List hosts"""
    if hosts := get_ssh_host_info():
        rich_print_hosts(hosts)
    else:
        click.echo(click.style("No hosts found in ~/.ssh/config", fg="yellow"))


@cli.command(name="pull")
@click.argument("host", type=str)
@click.argument("image", type=str)
@click.option("--verbose", is_flag=True, help="Verbose output")
def pull_image(host: str, image: str, verbose: bool):
    """在主机上拉取镜像，并导入到本地 Pull image at remote host and save it to local"""
    ssh_pull_image(host, image, verbose)


if __name__ == "__main__":
    cli()
