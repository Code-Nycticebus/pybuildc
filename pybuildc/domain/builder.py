from itertools import chain
import json
from pathlib import Path
import pickle
import subprocess
from typing import Iterable, Protocol

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

    cache: set[Path]

    verbose: bool


def _needs_recompilation(cache: set[Path], file: Path):
    return file in cache


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
        if cmd.output_path.suffix != ".o" or _needs_recompilation(
            config.cache, cmd.input_files[0]
        ):
            print(f"Building: {cmd.output_path.relative_to(config.build)}")
            if config.verbose:
                print(" ".join(cmd.command))
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


def _build_obj_files(
    src_files: tuple[Path, ...],
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    def _inner_build_obj_files(_: _BuilderConfig):
        return flow(
            src_files,
            compile_all_obj_files,
            RequiresContextIOResultE.from_context,  # Needed because the function above returns a "RequiresContext"
            bind(_build_command_run_all_with_context),
        )

    return (
        RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]
        .ask()
        .bind(_inner_build_obj_files)
    )


def _build_cache(
    binary_file: Path,
) -> RequiresContextIOResultE[Path, _BuilderConfig]:
    def _inner_build_bin_file(context: _BuilderConfig):
        cache_file = context.build / "cache"
        cache_dict = {
            file: file.stat().st_mtime for file in context.src.rglob("*.[c|h]")
        }
        cache_file.open("wb").write(pickle.dumps(cache_dict))
        return RequiresContextIOResultE.from_value(binary_file)

    return (
        RequiresContextIOResultE[Path, _BuilderConfig].ask().bind(_inner_build_bin_file)
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
        bind(_build_cache),
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
            bind(_build_command_run_all_with_context),
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
