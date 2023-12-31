from pathlib import Path
from dataclasses import dataclass

import toml

from pybuildc.dependencies import load_dependencies
from pybuildc.cache import load_cache


@dataclass
class Config:
    name: str
    bin: str
    cc: str

    compiling_files: set[Path]

    lib_flags: tuple[str, ...]
    inc_flags: tuple[str, ...]

    files: tuple[Path, ...]


def config_load(directory: Path) -> Config:
    file = toml.load(directory / "pybuildc.toml")

    lib_flags, inc_flags = load_dependencies(file.get("deps"))

    return Config(
        files=tuple(directory.rglob("./src/*.[h|c]")),
        compiling_files=load_cache(directory, include_dir=(Path(directory / "src"),)),
        lib_flags=lib_flags,
        inc_flags=inc_flags,
        **file["pybuildc"],
    )
