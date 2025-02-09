from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class HostInfo:
    name: str
    hostname: str = None
    user: str = None
    port: int = None


def get_ssh_host_info() -> list[HostInfo]:
    # 构建 .ssh/config 文件的完整路径
    ssh_config_path = Path.home() / ".ssh" / "config"
    host, hosts = None, []

    def _extract_value(s: str) -> str:
        return s.strip().split(" ", 1)[1].strip()

    if ssh_config_path.exists():
        with ssh_config_path.open("r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # init a host data
                if line.startswith("Host "):
                    if host:
                        hosts.append(host)
                    if name := _extract_value(line):
                        host = HostInfo(name)
                    else:  # ifnore error config
                        host = None
                if host and line.startswith("HostName "):
                    host.hostname = _extract_value(line)
                elif host and line.startswith("Port "):
                    host.port = int(_extract_value(line))
                elif host and line.startswith("User "):
                    host.user = _extract_value(line)
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
