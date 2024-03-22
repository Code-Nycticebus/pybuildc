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


class Scripts(TypedDict):
    class Cmd(TypedDict):
        cmd: str
        args: list[str]
        
    build: list[Cmd]


class Config(TypedDict):
    pybuildc: Project
    deps: dict[str, DepConfig]
    scripts: Scripts
    exe: dict[str, str]


def config_load(filename: Path) -> Config:
    return Config(**tomllib.loads(filename.read_text()))  # type: ignore
