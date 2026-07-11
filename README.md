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
        <img src="https://img.shields.io/pypi/v/pifr?style=flat-square" alt="Package" />
    </a>
    <a href="https://pypi.python.org/pypi/pifr">
        <img src="https://img.shields.io/pypi/pyversions/pifr?style=flat-square" />
    </a>
    <a href="https://github.com/ldsink/pifr/blob/master/LICENSE">
        <img src="https://img.shields.io/pypi/l/pifr?style=flat-square" alt="License" />
    </a>
</p>

Pull docker image from remote host, or push local image to remote host

## Install

It is recommended to install using [**pipx**][1]. [_How to install pipx?_][2]

> pipx install pifr

## Usage

Pull an image through a host

> pifr pull <host_name> <image_name>

> pifr pull remote-host hello-world

Push a local image to a remote host

> pifr push <image_name> <host_name>

> pifr push hello-world remote-host

This is useful when the local machine acts as an intermediary to transfer images between two hosts that cannot reach each other directly.

To see all of pifr's documentation, run `pifr --help`

```text
Usage: pifr [OPTIONS] COMMAND [ARGS]...

  Pull docker image from remote host, or push local image to remote host.

Options:
  --help  Show this message and exit.

Commands:
  list  列出主机 List hosts
  pull  在主机上拉取镜像，并导入到本地 Pull image at remote host and save it to local
  push  将本地镜像推送到远端主机 Push local image to remote host
```

[1]: https://github.com/pypa/pipx
[2]: https://github.com/pypa/pipx?tab=readme-ov-file#install-pipx
