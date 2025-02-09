from pathlib import Path


def get_ssh_hosts():
    # 构建 .ssh/config 文件的完整路径
    ssh_config_path = Path.home() / ".ssh" / "config"
    hosts = []
    if ssh_config_path.exists():
        with ssh_config_path.open("r") as file:
            for line in file:
                line = line.strip()
                if line.startswith("Host "):
                    host_entry = line.split(" ")[1]
                    if " " in host_entry:
                        hosts.extend(host_entry.split())
                    else:
                        hosts.append(host_entry)
    return hosts
