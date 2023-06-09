from pathlib import Path
import subprocess
from typing import Iterable, Protocol
from concurrent import futures

from returns.context import RequiresContextIOResultE
from returns.io import IOResultE
from returns.iterables import Fold
from returns.pipeline import flow
from returns.pointfree import bind

from pybuildc.domain.compiler import (
    CompileCommand,
    compile_all_obj_files,
    compile_all_test_files,
    link_exe,
    link_lib,
)


class _BuilderConfig(Protocol):
    src: Path
    tests: Path
    build: Path

    verbose: bool


def _build_command_run(
    cmd: CompileCommand,
) -> IOResultE[Path]:
    if subprocess.run(cmd.command).returncode != 0:
        return IOResultE.from_failure(Exception(cmd.command))
    return IOResultE.from_value(cmd.output_path)


def _build_command_run_with_context(cmd: CompileCommand):
    def inner(_: _BuilderConfig):
        return RequiresContextIOResultE.from_ioresult(_build_command_run(cmd))

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
            link_exe if Path(context.src, "main.c").exists() else link_lib,
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
    obj_files: Iterable[Path],
) -> RequiresContextIOResultE[tuple[Path, ...], _BuilderConfig]:
    def _inner(_: _BuilderConfig):
        return flow(
            obj_files,
            compile_all_test_files,
            RequiresContextIOResultE.from_context,  # Needed because "compile_all_test_files()" returns a "RequiresContext"
            bind(_build_command_run_all_concurrent_with_context),
        )

    return RequiresContextIOResultE[Path, _BuilderConfig].ask().bind(_inner)


def build_test_files(context) -> IOResultE[tuple[Path, ...]]:
    return flow(
        tuple(filter(lambda file: file.name != "main.c", context.src.rglob("*.c"))),
        _build_obj_files,
        bind(_build_test_files),
    )(context)
