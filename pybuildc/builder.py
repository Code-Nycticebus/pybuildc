from collections.abc import Iterable
from pathlib import Path
import pickle
import subprocess
from typing import Dict
from concurrent import futures
import itertools

import toml

from returns.io import IOResultE, IOFailure, IOSuccess, impure_safe
from returns.iterables import Fold
from returns.curry import partial
from returns.pipeline import flow
from returns.pointfree import bind

from pybuildc.domain.entities import BuildConfig, BuildFiles, Dependencies
from pybuildc.domain.services import Compiler, Cmd, BuildContext


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


def load_cache(directory: Path) -> Dict[Path, float]:
    cache_file = Path(directory, "cache_mtime.pkl")
    if not cache_file.exists():
        return dict()

    return pickle.loads(cache_file.read_bytes())


def save_cache(directory: Path, cache_mtime: Dict[Path, float]):
    cache_file = Path(directory, "cache_mtime.pkl")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(pickle.dumps(cache_mtime))


def include_file_changed(
    cache_mtime: Dict[Path, float], include_files: Iterable[Path]
) -> bool:
    return any(
        tuple(
            filter(partial(file_changed, cache_mtime), include_files),
        )
    )


def file_changed(cache_mtime: Dict[Path, float], file: Path) -> bool:
    if cache_mtime.get(file, 0.0) < (t := file.stat().st_mtime):
        cache_mtime[file] = t
        return True
    return False


def collect_flags(
    dependency: Dict[str, Dict[str, Iterable[str]]], key: str
) -> tuple[str, ...]:
    """Collects flags from dictionary structure"""
    return tuple(
        itertools.chain(*map(lambda val: val.get(key, tuple()), dependency.values())),
    )


def process_cmds(cmds: Iterable[Cmd]) -> IOResultE[Iterable[Cmd]]:
    with futures.ProcessPoolExecutor() as executor:
        commands = futures.as_completed((executor.submit(execute, cmd) for cmd in cmds))
        return Fold.collect(
            map(lambda p: p.result(), commands),
            IOSuccess(()),
        ) or IOFailure(Exception("process_cmds failed in unkown ways"))


def create_context(directory: Path, debug: bool) -> IOResultE[BuildContext]:
    target = "debug" if debug else "release"
    build_directory = Path(directory, ".build", target)

    config_file = Path(directory, "pybuildc.toml")
    match load_config(config_file):
        case IOSuccess(c):
            config = c.unwrap()
        case e:
            return e  # type: ignore
    cache_mtime: Dict[Path, float] = load_cache(build_directory)

    build_files = BuildFiles(
        directory,
        Path(directory, ".build", target),
        tuple(Path(directory, "src").rglob("*.c")),
        tuple(Path(directory, "src").rglob("*.h")),
    )

    dependency_config = config.get("dependencies", dict())

    build_config = BuildConfig(
        target,
        config["project"]["version"],
        directory.name,
        dependency_config,
    )

    cc = Compiler.create(
        cc=config["project"].get("cc", "gcc"),
        libraries=collect_flags(build_config.dependencies, "include"),
        includes=(
            f"-I{Path(directory, 'src').absolute()}",
            *collect_flags(build_config.dependencies, "lib"),
        ),
        debug=debug,
    )

    bin_file = create_bin_path(build_directory, build_config)

    return IOResultE.from_value(
        BuildContext(
            build_config,
            cache_mtime,
            build_files,
            bin_file,
            cc,
        )
    )


def create_bin_path(build_directory: Path, config: BuildConfig) -> Path:
    exe_file = Path(
        build_directory,
        "bin",
        f"""{config.project_name}-{config.target}-{config.version}""",
    )
    exe_file.parent.mkdir(parents=True, exist_ok=True)
    return exe_file


def builder(context: BuildContext) -> IOResultE[BuildContext]:
    def execute_build_commands(cmds: tuple[Cmd]) -> IOResultE[None]:
        res = process_cmds(cmds[:-1])
        if isinstance(res, IOFailure):
            return res

        res = execute(cmds[-1])
        if isinstance(res, IOFailure):
            return res

        return IOSuccess(None)

    return flow(
        context,
        create_compile_commands,
        execute_build_commands,
        lambda _: context,
    )


def build(directory: Path, debug: bool) -> IOResultE[BuildContext]:
    def save_cache_with_context(context: BuildContext):
        save_cache(context.files.build_directory, context.cache)
        return context

    return flow(
        create_context(directory, debug),
        bind(builder),
        save_cache_with_context,
    )


def create_compile_commands(
    context: BuildContext,
) -> tuple[Cmd, ...]:
    includes_changed = include_file_changed(context.cache, context.files.include_files)
    return flow(
        display(
            filter(
                lambda file: file_changed(context.cache, file) or includes_changed,
                context.files.src_files,
            )
        ),
        lambda compile_files: map(
            partial(
                compile_to_obj_file,
                context.cc,
                context.files.directory,
                context.config.target,
            ),
            compile_files,
        ),
        lambda obj_commands: (
            *obj_commands,
            context.cc.compile(
                map(
                    partial(
                        convert_to_obj_file,
                        context.files.directory,
                        context.config.target,
                    ),
                    context.files.src_files,
                ),
                context.bin_file,
            ),
        ),
    )
