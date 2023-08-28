from dataclasses import dataclass
from pathlib import Path
import pickle

from returns.io import IOResultE

if not __name__ == "__main__":
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


def collect_cache(directory: Path, target: str) -> set[Path]:
    cache_file = directory / ".build" / target / "cache"
    cache_dict: dict[Path, float]
    try:
        with cache_file.open("rb") as f:
            cache_dict = pickle.load(f)
    except FileNotFoundError:
        cache_dict = dict()

    cache = set()
    recompile_all = False
    if any(
        cache_dict.get(file, 0) < file.stat().st_mtime
        for file in (directory / "src").rglob("*.h")
    ):
        recompile_all = True

    for file in (directory / "src").rglob("*.c"):
        if recompile_all or cache_dict.get(file, 0) < file.stat().st_mtime:
            cache.add(file)

    return cache


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

    cache: set[Path]

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
                cache=collect_cache(directory, target),
                verbose=verbose,
                release=release,
                **config["project"],
                **get_project_structure(directory, target),
            )
        )


if __name__ == "__main__":
    print("TEST")
    collect_cache(Path("../../examples/test/"), "debug")
