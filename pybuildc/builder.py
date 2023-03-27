from collections.abc import Iterable
from pathlib import Path
import pickle
import subprocess
from typing import Dict

import toml

from returns.io import IOResultE, IOFailure, IOSuccess, impure_safe
from returns.iterables import Fold
from returns.curry import partial

from domain.services import Compiler, Cmd

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
        file.with_suffix(".o").relative_to(Path(project_directory, "src")),)
    obj_file.parent.mkdir(parents=True, exist_ok=True)
    return obj_file


def compile_to_obj_file(cc: Compiler, project_directory: Path, obj_file: Path):
    return execute(
        cc.compile(
            [obj_file],
            convert_to_obj_file(
                project_directory,
                obj_file),
            obj=True))


@impure_safe
def load_config(directory: Path):
    with open(Path(directory, "pybuildc.toml"), "r") as f:
        return toml.load(f)


def load_cache(directory: Path) -> Cache:
    cache_file = Path(directory, ".build", "cache_mtime.pkl")
    if not cache_file.exists():
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.touch()
        return dict()

    return pickle.loads(cache_file.read_bytes())


def save_cache(directory: Path, cache_mtime: Cache):
    cache_file = Path(directory, ".build", "cache_mtime.pkl")
    cache_file.write_bytes(pickle.dumps(cache_mtime))


def include_file_changed(
        cache_mtime: Cache,
        include_files: Iterable[Path]) -> bool:
    return any(
        tuple(
            filter(
                partial(
                    file_changed,
                    cache_mtime
                ),
                include_files
            ),
        )
    )


def file_changed(cache_mtime: Cache, file: Path) -> bool:
    if cache_mtime.get(file, 0.0) < (t := file.stat().st_mtime):
        cache_mtime[file] = t
        return True
    return False


def build(directory: Path, debug: bool) -> IOResultE:
    match load_config(directory):
        case IOSuccess(c):
            config = c.unwrap()
        case e:
            return e

    cache_mtime: Cache = load_cache(directory)

    src_files = tuple(Path(directory, "src").rglob("*.c"))
    include_files = tuple(Path(directory, "src").rglob("*.h"))
    includes_changed = include_file_changed(cache_mtime, include_files)

    cc = Compiler.create(
        cc=config["project"].get("cc", "gcc"),
        libraries=config.get("dependecies", tuple()),
        includes=map(str, include_files),
        debug=debug,
    )

    obj_files = tuple(map(partial(convert_to_obj_file, directory), src_files))

   # TODO filter src files to the ones that need recompiling

    compile_files = display(filter(
        lambda file: file_changed(cache_mtime, file) or includes_changed,
        src_files
    ))

    res = Fold.collect(
        map(partial(compile_to_obj_file, cc, directory), compile_files), IOSuccess(())
    )
    match res:
        case IOFailure():
            return res

    exe_file = Path(directory, ".build", "bin", config["project"]["name"])
    exe_file.parent.mkdir(parents=True, exist_ok=True)

    match execute(cc.compile(obj_files, exe_file, warnings=False)):
        case IOSuccess():
            save_cache(directory, cache_mtime)
            return IOSuccess(exe_file)
        case e:
            return e
