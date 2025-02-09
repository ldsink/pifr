from dataclasses import dataclass
from pathlib import Path


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
