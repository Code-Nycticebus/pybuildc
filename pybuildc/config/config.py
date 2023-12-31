from pathlib import Path
from dataclasses import dataclass

import toml

from .dependencies import Dependency, load_dependencies
from .cache import load_cache


@dataclass
class ConfigFile:
    name: str
    bin: str
    cc: str

    compiling_files: set[Path]
    dependencies: tuple[Dependency, ...]
    include_dirs: tuple[Path, ...]

    files: tuple[Path, ...]


def config_load(directory: Path) -> ConfigFile:
    file = toml.load(directory / "pybuildc.toml")
    deps = load_dependencies(directory, file.get("deps", {}))
    include_dirs = (
        directory / "src",
        *sum(map(lambda x: x.include_dirs, deps), ()),
    )

    return ConfigFile(
        files=tuple((directory / "src").rglob("*.[h|c]")),
        compiling_files=load_cache(directory, include_dir=include_dirs),
        dependencies=deps,
        include_dirs=include_dirs,
        **file["pybuildc"],
    )
