from dataclasses import dataclass
from pathlib import Path

Args = tuple[str, ...]
Cmd = tuple[str, ...]


@dataclass(frozen=True)
class CompilerEntity:
    cc: str
    cflags: Args
    lib_flags: Args
    includes: Args


@dataclass(frozen=True)
class CommandEntity:
    output_path: Path
    command: Cmd


@dataclass(frozen=True)
class BuildStructure:
    project: Path
    build: Path
    src: Path
    bin: Path
    test: Path
