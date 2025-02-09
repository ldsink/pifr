import click

from pifr.commands.host import get_ssh_host_info, rich_print_hosts


@click.group()
def cli():
    """Pull docker image from remote host."""


@cli.command(name="list")
def list_hosts():
    """列出主机 list hosts"""
    if hosts := get_ssh_host_info():
        rich_print_hosts(hosts)
    else:
        click.echo(click.style("No hosts found in ~/.ssh/config", fg="red"))


if __name__ == "__main__":
    cli()
