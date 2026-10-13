import shlex
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from pifr.commands.ssh import validate_host


@dataclass
class HostInfo:
    name: str
    hostname: str | None = None
    user: str | None = None
    port: str | None = None


def get_ssh_host_info() -> list[HostInfo]:
    """Read literal aliases without executing SSH Match commands."""
    ssh_config_path = Path.home() / ".ssh" / "config"
    if not ssh_config_path.is_file():
        return []

    directives: list[tuple[str, list[str]]] = []
    _read_directives(ssh_config_path, ssh_config_path.parent, directives, set())
    aliases: dict[str, HostInfo] = {}
    for key, values in directives:
        if key == "host":
            for name in values:
                try:
                    validate_host(name)
                except click.BadParameter:
                    continue
                aliases.setdefault(name, HostInfo(name))

    for host in aliases.values():
        active = True
        for key, values in directives:
            if key == "host":
                active = _matches_host(host.name, values)
            elif key == "match":
                active = _matches_condition(host.name, values)
            elif active and key in {"hostname", "user", "port"} and values and getattr(host, key) is None:
                setattr(host, key, values[0])
    return list(aliases.values())


def _matches_host(alias: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(alias.lower(), pattern.lower()) for pattern in patterns if not pattern.startswith("!")) and not any(
        fnmatchcase(alias.lower(), pattern[1:].lower()) for pattern in patterns if pattern.startswith("!")
    )


def _matches_condition(alias: str, criteria: list[str]) -> bool:
    if len(criteria) == 1 and criteria[0].lower() == "all":
        return True
    if len(criteria) == 2 and criteria[0].lower() in {"host", "originalhost"}:
        return _matches_host(alias, criteria[1].split(","))
    return False


def _read_directives(config_path: Path, config_dir: Path, directives: list[tuple[str, list[str]]], stack: set[Path]) -> None:
    resolved_path = config_path.resolve()
    if resolved_path in stack:
        return
    stack.add(resolved_path)
    try:
        with config_path.open("r") as file:
            for line in file:
                try:
                    parts = shlex.split(line, comments=True)
                except ValueError:
                    continue
                if not parts:
                    continue
                key, separator, first_value = parts[0].partition("=")
                values = ([first_value] if separator and first_value else []) + parts[1:]
                if values and values[0].startswith("="):
                    values[0] = values[0][1:]
                    if not values[0]:
                        values = values[1:]
                key = key.lower()

                if key == "include":
                    for value in values:
                        pattern = Path(value).expanduser()
                        if not pattern.is_absolute():
                            pattern = config_dir / pattern
                        root = Path(pattern.anchor)
                        for path in sorted(root.glob(str(pattern.relative_to(root)))):
                            if path.is_file():
                                _read_directives(path, config_dir, directives, stack)
                else:
                    directives.append((key, values))
    finally:
        stack.remove(resolved_path)


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
        table.add_row(host.name, host.hostname or "", host.port or "", host.user or "")
    # 使用 Console 对象打印表格
    console.print(table)
