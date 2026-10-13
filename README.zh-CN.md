```text
         _    __
 _ __   (_)  / _|  _ __
| '_ \  | | | |_  | '__|
| |_) | | | |  _| | |
| .__/  |_| |_|   |_|
|_|
```

<p style="text-align: left">
    <a href="https://pypi.python.org/pypi/pifr">
        <img src="https://img.shields.io/pypi/v/pifr?style=flat-square" alt="软件包版本" />
    </a>
    <a href="https://pypi.python.org/pypi/pifr">
        <img src="https://img.shields.io/pypi/pyversions/pifr?style=flat-square" />
    </a>
    <a href="https://github.com/ldsink/pifr/blob/master/LICENSE">
        <img src="https://img.shields.io/pypi/l/pifr?style=flat-square" alt="许可证" />
    </a>
</p>

[English](README.md) · [简体中文](README.zh-CN.md)

通过 SSH 主机拉取远端 Docker 镜像，或将本地 Docker 镜像推送到远端主机。

## 安装

推荐直接使用 [**uvx**][1] 运行。[_如何安装 uv？_][2]

> uvx pifr

## 使用方法

列出 SSH 配置中的主机：

> pifr list

通过远端主机拉取镜像：

> pifr pull <host_name> <image_name>

> pifr pull remote-host hello-world

将本地镜像推送到远端主机：

> pifr push <image_name> <host_name>

> pifr push hello-world remote-host

镜像名称可以包含仓库主机及端口、标签或摘要。名称无效时会在传输开始前提示错误。

当本地机器作为中转站，为两台无法直接互通的主机传输镜像时，这个工具也很有用。

运行 `pifr --help` 查看所有命令及其说明。

[1]: https://docs.astral.sh/uv/
[2]: https://docs.astral.sh/uv/getting-started/installation/
