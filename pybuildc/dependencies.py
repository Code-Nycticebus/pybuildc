from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Dependency:
    t: str
    library_name: str | None = None
    library_dir: Path | None = None
    include_dirs: tuple[Path] = field(default_factory=tuple)


def load_dependencies(config) -> tuple[tuple[str, ...], tuple[str, ...]]:
    for dep, c in config.items():
        pass
    return (), ()
