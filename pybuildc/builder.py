from collections.abc import Iterable
from pathlib import Path
import pickle
import subprocess
from typing import Dict

import toml

from returns.io import IOResultE, IOFailure, IOSuccess, impure_safe
from returns.iterables import Fold
from returns.curry import partial

from pybuildc.domain.services import Compiler, Cmd

Cache = Dict[Path, float]


def display(files: Iterable[Path]):
    for file in files:
        print(f"  [BUILDING] {file}")
        yield file


@impure_safe
def execute(cmd: Cmd):
    subprocess.run(cmd, check=True)


def convert_to_obj_file(project_directory, file: Path) -> Path:
    obj_file = Path(
        project_directory,
        ".build",
        "obj",
        file.with_suffix(".o").relative_to(Path(project_directory, "src")),
    )
    obj_file.parent.mkdir(parents=True, exist_ok=True)
    return obj_file


def compile_to_obj_file(cc: Compiler, project_directory: Path, obj_file: Path) -> Cmd:
    return cc.compile(
        [obj_file], convert_to_obj_file(project_directory, obj_file), obj=True
    )


@impure_safe
def load_config(config_file: Path):
    return toml.loads(config_file.read_text())


def load_cache(directory: Path) -> Cache:
    cache_file = Path(directory, ".build", "cache_mtime.pkl")
    if not cache_file.exists():
        return dict()

    return pickle.loads(cache_file.read_bytes())


def save_cache(directory: Path, cache_mtime: Cache):
    cache_file = Path(directory, ".build", "cache_mtime.pkl")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(pickle.dumps(cache_mtime))


def include_file_changed(cache_mtime: Cache, include_files: Iterable[Path]) -> bool:
    return any(
        tuple(
            filter(partial(file_changed, cache_mtime), include_files),
        )
    )


def file_changed(cache_mtime: Cache, file: Path) -> bool:
    if cache_mtime.get(file, 0.0) < (t := file.stat().st_mtime):
        cache_mtime[file] = t
        return True
    return False


def collect_flags(
    dependecies: Dict[str, Dict[str, list[str]]], key: str
) -> tuple[str, ...]:
    return sum(
        (*(tuple(val[key]) for val in dependecies.values() if key in val),), tuple()
    )




# TODO should return a tuple of Cmds!
def build(directory: Path, debug: bool) -> IOResultE[Path]:
    config_file = Path(directory, "pybuildc.toml")
    match load_config(config_file):
        case IOSuccess(c):
            config = c.unwrap()
        case e:
            return e.map(lambda _: Path())

    cache_mtime: Cache = load_cache(directory)

    dependecies = config.get("dependecies", dict())

    cc = Compiler.create(
        cc=config["project"].get("cc", "$(cc)"),
        libraries=collect_flags(dependecies, "lib"),
        includes=(
            f"-I{Path(directory, 'src').absolute()}",
            *collect_flags(dependecies, "include"),
        ),
        debug=debug,
    )

    exe_file = Path(directory, ".build", "bin", config["project"]["name"])
    exe_file.parent.mkdir(parents=True, exist_ok=True)

    res = Fold.collect_all(map(execute, builder(directory, cache_mtime, cc, exe_file)), IOSuccess(()))
    match res:
        case IOFailure():
            return res

    save_cache(directory, cache_mtime)
    return IOSuccess(exe_file)


def builder(directory: Path, cache_mtime: Dict[Path, float], cc: Compiler, exe_file: Path) -> tuple[Cmd, ...]:
    src_files = tuple(Path(directory, "src").rglob("*.c"))
    include_files = tuple(Path(directory, "src").rglob("*.h"))
    includes_changed = include_file_changed(cache_mtime, include_files)
    compile_files = display(
        filter(
            lambda file: file_changed(cache_mtime, file) or includes_changed, src_files
        )
    )
    build_commands = map(partial(compile_to_obj_file, cc, directory), compile_files)

    obj_files = tuple(map(partial(convert_to_obj_file, directory), src_files))

    return (*build_commands, cc.compile(obj_files, exe_file))
