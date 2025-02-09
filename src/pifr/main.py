import click

from pifr.commands.host import get_ssh_hosts


@click.group()
def cli():
    """Pull docker image from remote host."""


@cli.command(name="list")
def list_hosts():
    """列出主机 list hosts"""
    for host in get_ssh_hosts():
        click.echo(host)


if __name__ == "__main__":
    cli()
