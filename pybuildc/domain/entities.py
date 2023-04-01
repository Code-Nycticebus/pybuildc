from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class BuildFiles:
    directory: Path
    build_directory: Path
    src_files: tuple[Path, ...]
    include_files: tuple[Path, ...]


@dataclass(frozen=True)
class BuildConfig:
    target: str
    version: str
    project_name: str
    dependencies: Dict[str, Dict[str, Iterable[str]]]
