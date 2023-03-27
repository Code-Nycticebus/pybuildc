from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


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
    "-Wno-unused-command-line-argument",
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
    libraries: tuple[str]

    def compile(
            self,
            files: Iterable[Path],
            output: Path,
            flags: Iterable[str],
            disable_warnings=False) -> Cmd:
        return (
            self.cc,
            *map(str, files),
            *(self.warnings if not disable_warnings else ()),
            *self.libraries,
            *(self.flags + tuple(flags)),
            "-o",
            str(output),
        )

    @classmethod
    def create(
            cls,
            cc: str,
            libraries: Iterable[str],
            debug: bool):
        return cls(
            cc=cc,
            warnings=DEBUG_WARNINGS if debug else RELEASE_WARNINGS,
            flags=DEBUG_FLAGS if debug else RELEASE_FLAGS,
            libraries=tuple(libraries),
        )
