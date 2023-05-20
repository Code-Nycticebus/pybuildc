from dataclasses import dataclass
from pathlib import Path

from returns.io import IOResultE

from pybuildc.domain.config import load_config


def get_project_structure(directory: Path, target: str):
    return {
        "project": directory,
        "src": Path(directory, "src"),
        "build": Path(directory, ".build", target),
        "tests": Path(directory, "tests"),
    }


@dataclass(frozen=True)
class BuildContext:
    name: str
    version: str
    verbose: bool

    cc: str
    warnings: bool
    cflags: tuple[str, ...]
    include_flags: tuple[str, ...]
    library_flags: tuple[str, ...]

    project: Path
    build: Path
    src: Path
    tests: Path

    cache: dict[Path, float]

    @classmethod
    def create_from_config(
        cls, directory: Path, target: str, verbose: bool
    ) -> IOResultE:
        return load_config(Path(directory, "pybuildc.toml")).map(
            lambda config: cls(
                include_flags=config["deps"].get("include_flags", ())
                + (f"-I{Path(directory, 'src')}",),
                library_flags=config["deps"]["library_flags"],
                cache=dict(),
                verbose=verbose,
                **config["project"],
                **get_project_structure(directory, target),
            )
        )
