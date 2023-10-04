from dataclasses import dataclass
from pathlib import Path
import pickle
from collections import defaultdict
from typing import Iterable

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

def build_dep_tree(files: Iterable[Path]) -> dict[Path, set]:
    deps = defaultdict(set)
    for file in files:
        text = file.read_text()
        find_text = "#include"
        index = text.find(find_text)
        index = text.find("\"", index)
        while 0 <= index:
            include_start = text[index+1:]
            end_index = include_start.find("\"")
            include = include_start[:end_index]
            deps[file].add(Path(file.parent, include)) 

            text = include_start
            index = text.find(find_text)
            index = text.find("\"", index)
    return deps 

def has_dep_that_changed(file: Path, deps: dict[Path, set], has_changed: set[Path]) -> bool:
    if deps[file].intersection(has_changed):
        return True
    for dep in deps[file]:
        if has_dep_that_changed(dep, deps, has_changed):
            return True
    return False


def collect_cache(directory: Path, target: str) -> set[Path]:
    cache_file = directory / ".build" / target / "cache"
    cache_dict: dict[Path, float]
    try:
        with cache_file.open("rb") as f:
            cache_dict = pickle.load(f)
    except FileNotFoundError:
        cache_dict = dict()


    files = list((directory / "src").rglob("*.[h|c]"))
    changed_files = {file for file in files if cache_dict.get(file, 0) < file.stat().st_mtime}
    dep_tree = build_dep_tree(files)

    need_recompilation = set()
    for file in filter(lambda file: file.name.endswith(".c"), files):
        if has_dep_that_changed(file, dep_tree, changed_files) or file in changed_files:
            print(file)
            need_recompilation.add(file)

    return need_recompilation


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
