from dataclasses import dataclass
from pathlib import Path
import pickle
from collections import defaultdict
from typing import Iterable

from returns.io import IOResultE

from pybuildc.domain.config import load_config


def get_project_structure(directory: Path):
    return {
        "project": directory,
        "src": Path(directory, "src"),
        "tests": Path(directory, "tests"),
    }


def get_cache(directory: Path, target: str) -> dict[Path, float]:
    cache_file = directory / ".build" / target / "cache"
    try:
        with cache_file.open("rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return dict()


def build_dep_tree(src: Path, files: Iterable[Path]) -> dict[Path, set]:
    deps = defaultdict(set)
    search_text = "#include"
    for file in files:
        with file.open("r") as f:
            for line in f.readlines():
                index = line.find(search_text)
                if index != -1:
                    index = line.find('"', index)
                    if index != -1:
                        include = line[index + 1 : -2]
                        dep_file = next(src.rglob(Path(include).name), None)
                        if dep_file:
                            deps[file].add(dep_file)
    return deps


def has_dep_that_changed(
    file: Path, deps: dict[Path, set], has_changed: set[Path]
) -> bool:
    if deps[file].intersection(has_changed):
        return True
    for dep in deps[file]:
        if has_dep_that_changed(dep, deps, has_changed):
            return True
    return False


def collect_cache(directory: Path, build_dir: Path, target: str) -> set[Path]:
    cache_file = build_dir / target / "cache"
    cache_dict: dict[Path, float]
    try:
        with cache_file.open("rb") as f:
            cache_dict = pickle.load(f)
    except FileNotFoundError:
        cache_dict = dict()

    src_path = directory / "src"
    files = list(src_path.rglob("*.[h|c]"))

    config_file = directory / "pybuildc.toml"
    if cache_dict.get(config_file, 0) < config_file.stat().st_mtime:
        return set(files)

    changed_files = {
        file for file in files if cache_dict.get(file, 0) < file.stat().st_mtime
    }
    dep_tree = build_dep_tree(src_path, files)

    need_recompilation = set()
    for file in filter(lambda file: file.name.endswith(".c"), files):
        if has_dep_that_changed(file, dep_tree, changed_files) or file in changed_files:
            need_recompilation.add(file)

    return need_recompilation


@dataclass()
class BuildContext:
    name: str
    version: str
    verbose: bool

    release: bool

    bin: str

    cc: str
    cflags: tuple[str, ...]
    include_flags: tuple[Path, ...]
    library_flags: tuple[tuple[Path, str], ...]
    build_scripts: tuple[Path, ...]

    project: Path
    build: Path
    src: Path
    tests: Path

    cache: set[Path]

    @classmethod
    def create_from_config(
        cls, directory: Path, build_directory: Path, release: bool, verbose: bool
    ) -> IOResultE:
        target = "release" if release else "debug"
        return load_config(Path(directory, "pybuildc.toml")).map(
            lambda config: cls(
                include_flags=config["deps"].get("include_flags", ())
                + (Path(directory, "src"),),
                library_flags=config["deps"]["library_flags"],
                build_scripts=config["deps"]["build_scripts"],
                cache=collect_cache(directory, build_directory, target),
                verbose=verbose,
                release=release,
                build=build_directory / target,
                **config["project"],
                **get_project_structure(directory),
            )
        )
