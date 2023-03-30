from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from pybuildc.domain.entities import BuildConfig, BuildFiles


Args = tuple[str, ...]
Cmd = tuple[str, ...]

RELEASE_WARNINGS: Args = (
    "-Wall",
    "-Wpedantic"
)

DEBUG_WARNINGS: Args = (
    "-Wall",
    "-Wextra",
    "-Wpedantic",
    "-Werror",
    "-Wshadow",
    "-Wnull-dereference",
    "-Wformat=2",
)

# TODO some way to disable sanitizer
DEBUG_FLAGS: Args = (
    "-ggdb",
    "-fsanitize=address,undefined,leak",
    "-fno-omit-frame-pointer",
    "-fPIC"
)

RELEASE_FLAGS: Args = (
    "-O2",
)


@dataclass(frozen=True)
class Compiler:
    cc: str
    warnings: tuple[str]
    flags: tuple[str]
    includes: tuple[str]
    libraries: tuple[str]

    def compile(
            self,
            files: Iterable[Path],
            output: Path,
            warnings: bool = True,
            obj: bool = False) -> Cmd:
        return (
            self.cc,
            *self.includes,
            *map(str, files),
            *(self.warnings if not warnings else ()),
            *self.libraries,
            *self.flags,
            *(("-c", ) if obj else ()),
            "-o",
            str(output),
        )

    @classmethod
    def create(
            cls,
            cc: str,
            includes: tuple[str, ...],
            libraries: tuple[str, ...],
            debug: bool):
        return cls(
            cc=cc,
            warnings=DEBUG_WARNINGS if debug else RELEASE_WARNINGS,
            flags=DEBUG_FLAGS if debug else RELEASE_FLAGS,
            includes=includes,
            libraries=libraries,
        )


FileMtimeCache = Dict[Path, float]

@dataclass(frozen=True)
class BuildContext:
    config: BuildConfig
    cache: FileMtimeCache
    files: BuildFiles
