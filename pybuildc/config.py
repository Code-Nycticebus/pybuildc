from pathlib import Path
from typing import Literal, TypedDict

import tomllib

from pybuildc.types import Mode


class Project(TypedDict):
    name: str
    cflags: list[str]


class DepConfig(TypedDict):
    type: Literal["pybuildc", "static"]
    mode: Mode
    dir: str
    L: Path
    l: str
    I: list[Path]
    cflags: list[str]


class Cmd(TypedDict):
    cmd: str
    args: list[str]


class Scripts(TypedDict):
    build: list[Cmd]


class Config(TypedDict):
    pybuildc: Project
    libs: dict[str, DepConfig]
    scripts: Scripts
    exe: dict[str, str]
    dll: dict[str, str]


def config_load(filename: Path) -> Config:
    return Config(**tomllib.loads(filename.read_text()))  # type: ignore
