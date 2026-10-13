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

[English](README.md) · [简体中文](README.zh-CN.md)

Pull docker image from remote host, or push local image to remote host

## Install

It is recommended to run directly with [**uvx**][1]. [_How to install uv?_][2]

> uvx pifr

## Usage

List hosts from your SSH configuration:

> pifr list

Pull an image through a host

> pifr pull <host_name> <image_name>

> pifr pull remote-host hello-world

Push a local image to a remote host

> pifr push <image_name> <host_name>

> pifr push hello-world remote-host

Image names may include a registry host and port, a tag, or a digest. Invalid names are rejected before any transfer starts.

This is useful when the local machine acts as an intermediary to transfer images between two hosts that cannot reach each other directly.

To see all available commands, run `pifr --help`.

[1]: https://docs.astral.sh/uv/
[2]: https://docs.astral.sh/uv/getting-started/installation/
