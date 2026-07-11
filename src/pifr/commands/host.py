from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class HostInfo:
    name: str
    hostname: str | None = None
    user: str | None = None
    port: int | None = None


def get_ssh_host_info() -> list[HostInfo]:
    ssh_config_path = Path.home() / ".ssh" / "config"
    host, hosts = None, []

    if ssh_config_path.exists():
        with ssh_config_path.open("r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) < 2:
                    continue
                key, value = parts[0], parts[1].strip()
                if key == "Host":
                    if host:
                        hosts.append(host)
                    if value:
                        host = HostInfo(value)
                    else:
                        host = None
                elif host and key == "HostName":
                    host.hostname = value
                elif host and key == "Port":
                    host.port = int(value)
                elif host and key == "User":
                    host.user = value
        if host:
            hosts.append(host)
    return hosts


def rich_print_hosts(hosts: list[HostInfo]):
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
