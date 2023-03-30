from collections.abc import Iterable
from pathlib import Path
import pickle
import subprocess
from typing import Dict
from concurrent import futures

import toml

from returns.io import IOResultE, IOFailure, IOSuccess, impure_safe
from returns.iterables import Fold
from returns.curry import partial
from pybuildc.domain.entities import BuildConfig, BuildFiles, Dependecies

from pybuildc.domain.services import Compiler, Cmd, BuildContext

Cache = Dict[Path, float]

def display(files: Iterable[Path]):
    for file in files:
        print(f"  [BUILDING] {file}")
        yield file


@impure_safe
def execute(cmd: Cmd) -> Cmd:
    subprocess.run(cmd, check=True)
    return cmd


def convert_to_obj_file(project_directory: Path, target: str, file: Path) -> Path:
    obj_file = Path(
        project_directory,
        ".build",
        target,
        "obj",
        file.relative_to(Path(project_directory, "src")).with_suffix(".o"),
    )
    obj_file.parent.mkdir(parents=True, exist_ok=True)
    return obj_file


def compile_to_obj_file(
    cc: Compiler, project_directory: Path, target: str, obj_file: Path
) -> Cmd:
    return cc.compile(
        [obj_file], convert_to_obj_file(project_directory, target, obj_file), obj=True
    )


@impure_safe
def load_config(config_file: Path):
    return toml.loads(config_file.read_text())


def load_cache(directory: Path) -> Cache:
    cache_file = Path(directory, "cache_mtime.pkl")
    if not cache_file.exists():
        return dict()

    return pickle.loads(cache_file.read_bytes())


def save_cache(directory: Path, cache_mtime: Cache):
    cache_file = Path(directory, "cache_mtime.pkl")
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
    """Collects flags from dictionary structure"""
    return sum(
        (*(tuple(val[key]) for val in dependecies.values() if key in val),), tuple()
    )


def process_cmds(cmds: Iterable[Cmd]) -> IOResultE[Iterable[Cmd]]:
    with futures.ProcessPoolExecutor() as executor:
        done, _ = futures.wait(
               (executor.submit(execute, cmd) for cmd in cmds)
        )
        return Fold.collect(
            map(futures.Future.result, done),
            IOSuccess(()),
        ) or IOFailure(Exception("Somehow process_cmds failed!"))


def build(directory: Path, debug: bool) -> IOResultE[Path]:
    target = "debug" if debug else "release"
    build_directory = Path(directory, ".build", target)

    config_file = Path(directory, "pybuildc.toml")
    match load_config(config_file):
        case IOSuccess(c):
            config = c.unwrap()
        case e:
            return e.map(lambda _: Path())

    cache_mtime: Cache = load_cache(build_directory)

    build_directory = Path(directory, ".build", target)

    dependecy_config = config.get("dependecies", dict())
    dependecies = Dependecies(
        directory.name, 
        config.get("version", "0.0.0"),
        collect_flags(dependecy_config, "include"),
        collect_flags(dependecy_config, "lib"),
    )

    cc = Compiler.create(
        cc=config["project"].get("cc", "gcc"),
        libraries=dependecies.inc_flags,
        includes=(
            f"-I{Path(directory, 'src').absolute()}",
            *dependecies.lib_flags,
        ),
        debug=debug,
    )

    exe_file = Path(
        build_directory,
        "bin",
        f"""{config["project"]["name"]}-{target}-{config['project']['version']}""",
    )
    exe_file.parent.mkdir(parents=True, exist_ok=True)

    build_files = BuildFiles(
        directory,
        Path(directory, ".build", target),
        tuple(Path(directory, "src").rglob("*.c")),
        tuple(Path(directory, "src").rglob("*.h")),
    )

    build_config = BuildConfig(
        target,
        directory.name,
        dependecies,
    )

    context = BuildContext(
        config=build_config,
        cache=cache_mtime,
        files=build_files, 
    )

    obj_cmds, binary_cmd = builder(context, cc, exe_file)

    res: IOResultE[Iterable[Cmd]] = process_cmds(obj_cmds)
    match res:
        case IOFailure():
            return res

    res2 = execute(binary_cmd)
    match res2:
        case IOFailure():
            return res2

    save_cache(build_directory, cache_mtime)
    return IOSuccess(exe_file)


def builder(
    context: BuildContext,
    cc: Compiler,
    exe_file: Path,
) -> tuple[tuple[Cmd, ...], Cmd]:
    includes_changed = include_file_changed(
        context.cache, 
        context.files.include_files
    )
    compile_files = display(
        filter(
            lambda file: file_changed(context.cache, file) or includes_changed, context.files.src_files
        )
    )
    obj_cmds = tuple(
        map(partial(compile_to_obj_file, cc, context.files.directory, context.config.target), compile_files)
    )
    obj_files = map(partial(convert_to_obj_file, context.files.directory, context.config.target), context.files.src_files)
    return obj_cmds, cc.compile(obj_files, exe_file)
