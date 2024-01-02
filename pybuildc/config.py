from pathlib import Path
from typing import Literal, TypedDict

import tomllib as toml

from pybuildc.types import Mode


class Project(TypedDict):
    name: str
    cc: str
    bin: Literal["exe"] | Literal["static"]
    cflags: list[str]


class DepConfig(TypedDict):
    type: Literal["pybuildc"] | Literal["static"]
    mode: Mode
    dir: str
    L: Path
    l: str
    I: list[Path]


class Config(TypedDict):
    pybuildc: Project
    deps: dict[str, DepConfig]


def config_load(filename: Path) -> Config:
    config = toml.loads(filename.read_text())
    return Config(**config)  # type: ignore
