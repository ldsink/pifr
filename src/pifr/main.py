import click
from rich.console import Console
from rich.table import Table

from pifr.commands.host import get_ssh_host_info


@click.group()
def cli():
    """Pull docker image from remote host."""


@cli.command(name="list")
def list_hosts():
    """列出主机 list hosts"""
    if not (hosts := get_ssh_host_info()):
        click.echo(click.style("No hosts found in ~/.ssh/config", fg="red"))
        return

    # 创建一个 Console 对象，用于输出表格
    console = Console()
    # 创建一个 Table 对象
    table = Table(show_header=True, header_style="bold")
    # 添加表头
    table.add_column("Host", style="green")
    table.add_column("Hostname", style="yellow")
    table.add_column("Port", style="magenta")
    table.add_column("User", style="cyan")
    # 添加表格行数据
    for host in hosts:
        table.add_row(host.name, host.hostname or "", str(host.port or ""), host.user or "")
    # 使用 Console 对象打印表格
    console.print(table)


if __name__ == "__main__":
    cli()
