from itertools import chain
import json
from pathlib import Path
import subprocess
from typing import Iterable, Protocol
from concurrent import futures
import pickle

from returns.context import RequiresContextIOResultE
from returns.io import IOResultE
from returns.iterables import Fold
from returns.pipeline import flow
from returns.pointfree import bind, map_

from pybuildc.domain.compiler import (
    CompileCommand,
    _create_path,
    compile,
    compile_all_obj_files,
    compile_all_test_files,
    link_exe,
    link_shared,
    link_static,
)


class _BuilderConfig(Protocol):
    name: str
    src: Path
    tests: Path
    build: Path
    bin: str

    cache: dict[Path, float]

    verbose: bool


def _needs_recompilation(cache: dict[Path, float], file: Path):
    return cache.get(file, 0) < file.stat().st_mtime


def _build_command_run(
    cmd: CompileCommand,
) -> IOResultE[Path]:
    try:
        if subprocess.run(cmd.command).returncode != 0:
            return IOResultE.from_failure(Exception(cmd.command))
    except FileNotFoundError as e:
        e.add_note(f"Command '{cmd.command[0]}' not found!")
        raise
    return IOResultE.from_value(cmd.output_path)


def _build_command_run_with_context(cmd: CompileCommand):
    def inner(config: _BuilderConfig):
        if _needs_recompilation(config.cache, cmd.input_files[0]):
            return RequiresContextIOResultE.from_ioresult(_build_command_run(cmd))
        else:
            return RequiresContextIOResultE.from_value(cmd.output_path)

    return RequiresContextIOResultE[Path, _BuilderConfig].ask().bind(inner)


def _build_command_run_all_with_context(
    cmds: Iterable[CompileCommand],
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    def inner(_: _BuilderConfig):
        return Fold.collect(
            map(_build_command_run_with_context, cmds),
            RequiresContextIOResultE.from_value(()),
        ) or RequiresContextIOResultE.from_failure(
            ValueError("Something went wrong while executing all commands")
        )

    return RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig].ask().bind(inner)


def _build_command_run_all_concurrent(
    cmds: Iterable[CompileCommand],
) -> IOResultE[tuple[Path, ...]]:
    with futures.ProcessPoolExecutor() as executor:
        commands = futures.as_completed(
            (executor.submit(_build_command_run, cmd) for cmd in cmds)
        )
        return Fold.collect(
            tuple(map(lambda p: p.result(), commands)),
            IOResultE.from_value(()),
        ) or IOResultE.from_failure(
            Exception("Something went wrong while processing commands asynchronously")
        )


def _build_command_run_all_concurrent_with_context(
    cmds: Iterable[CompileCommand],
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    return (
        RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]
        .ask()
        .bind(
            lambda _: RequiresContextIOResultE.from_ioresult(
                _build_command_run_all_concurrent(cmds)
            )
        )
    )


def _register_file_in_cache(
    cmds: Iterable[CompileCommand],
) -> RequiresContextIOResultE[Iterable[CompileCommand], _BuilderConfig]:
    def _inner_register_file_in_cache(context: _BuilderConfig):
        cache = {}
        for cmd in cmds:
            if cmd.input_files[0].suffix == ".c":
                cache[cmd.input_files[0]] = cmd.input_files[0].stat().st_mtime
            yield cmd

        with (context.build / "cache").open("wb") as f:
            pickle.dump(cache, f)

    return (
        RequiresContextIOResultE[Iterable[CompileCommand], _BuilderConfig]
        .ask()
        .map(_inner_register_file_in_cache)
    )


def display_with_context(
    cmds: Iterable[CompileCommand],
) -> RequiresContextIOResultE[Iterable[CompileCommand], _BuilderConfig]:
    def _inner_display_with_context(context: _BuilderConfig):
        for cmd in cmds:
            print(f"Building: {cmd.output_path.relative_to(context.build)}")
            if context.verbose:
                print(" ".join(cmd.command))
            yield cmd

    return (
        RequiresContextIOResultE[Iterable[CompileCommand], _BuilderConfig]
        .ask()
        .map(_inner_display_with_context)
    )


def _build_obj_files(
    src_files: tuple[Path, ...],
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    def _inner_build_obj_files(_: _BuilderConfig):
        return flow(
            src_files,
            compile_all_obj_files,
            RequiresContextIOResultE.from_context,  # Needed because the function above returns a "RequiresContext"
            bind(display_with_context),
            bind(_register_file_in_cache),
            bind(
                _build_command_run_all_concurrent_with_context
                if len(src_files) > 10
                else _build_command_run_all_with_context
            ),
        )

    return (
        RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]
        .ask()
        .bind(_inner_build_obj_files)
    )


def _build_bin_file(
    obj_files: Iterable[Path],
) -> RequiresContextIOResultE[Path, _BuilderConfig]:
    def _inner_build_bin_file(context: _BuilderConfig):
        return flow(
            obj_files,
            link_shared
            if context.bin == "shared"
            else link_static
            if context.bin == "static"
            else link_exe,
            RequiresContextIOResultE.from_context,  # Needed because the function above returns a "RequiresContext"
            bind(_build_command_run_with_context),
        )

    return (
        RequiresContextIOResultE[Path, _BuilderConfig].ask().bind(_inner_build_bin_file)
    )


def build_bin(
    context: _BuilderConfig,
) -> IOResultE[Path]:
    return flow(
        tuple(context.src.rglob("*.c")),
        _build_obj_files,
        bind(_build_bin_file),
    )(context)


def _build_test_files(
    obj_files: CompileCommand,
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    def _inner(context: _BuilderConfig):
        def strip_main(lib_name):
            new_name = _create_path(
                context.build,
                "tests",
                f"{lib_name.with_suffix('').name}-test.a",
            )

            subprocess.run(
                [
                    "objcopy",
                    "--redefine-sym",
                    f"main={context.name}_main",
                    str(lib_name),
                    str(new_name),
                ]
            )
            return new_name

        return flow(
            obj_files,
            _build_command_run,
            map_(strip_main),
            bind(compile_all_test_files),
            RequiresContextIOResultE.from_context,  # Needed because "compile_all_test_files()" returns a "RequiresContext"
            bind(_build_command_run_all_concurrent_with_context),
        )

    return RequiresContextIOResultE[Path, _BuilderConfig].ask().bind(_inner)


def build_test_files(context) -> IOResultE[tuple[Path, ...]]:
    return flow(
        tuple(context.src.rglob("*.c")),
        _build_obj_files,
        bind(link_static),
        RequiresContextIOResultE.from_context,  # Needed because "compile_all_test_files()" returns a "RequiresContext"
        bind(_build_test_files),
    )(context)


def build_compile_commands(context):
    compile_commands = list()

    for file in chain(context.src.rglob("*.c"), context.tests.rglob("*-test.c")):
        command = compile([file], context.build / file.with_suffix(".o").name)(context)

        compile_commands.append(
            {
                "file": str(file.relative_to(context.project)),
                "directory": str(context.project),
                "arguments": command.command,
            }
        )

    with open(
        _create_path(context.project, ".build", "compile_commands.json"), "w"
    ) as f:
        json.dump(compile_commands, f)

    return context
