from dataclasses import dataclass
from pathlib import Path
import pickle

from returns.io import IOResultE

from pybuildc.domain.config import load_config


def get_project_structure(directory: Path, target: str):
    return {
        "project": directory,
        "src": Path(directory, "src"),
        "build": Path(directory, ".build", target),
        "tests": Path(directory, "tests"),
    }


def get_cache(directory: Path, target: str) -> dict[Path, float]:
    cache_file = directory / ".build" / target / "cache"
    try:
        with cache_file.open("rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return dict()


@dataclass(frozen=True)
class BuildContext:
    name: str
    version: str
    verbose: bool

    release: bool

    bin: str

    cc: str
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
        cls, directory: Path, release: bool, verbose: bool
    ) -> IOResultE:
        target = "release" if release else "debug"
        return load_config(Path(directory, "pybuildc.toml")).map(
            lambda config: cls(
                include_flags=config["deps"].get("include_flags", ())
                + (f"-I{Path(directory, 'src')}",),
                library_flags=config["deps"]["library_flags"],
                cache=get_cache(directory, target),
                verbose=verbose,
                release=release,
                **config["project"],
                **get_project_structure(directory, target),
            )
        )
