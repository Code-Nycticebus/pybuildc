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
    project: Path
    src: Path
    tests: Path
    build: Path
    bin: str
    cc: str

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
        config_file = context.project / "pybuildc.toml"
        cache_dict[config_file] = config_file.stat().st_mtime
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
                "directory": str(context.project.absolute()),
                "arguments": command.command,
            }
        )

    with open(
        _create_path(context.project, ".build", "compile_commands.json"), "w"
    ) as f:
        json.dump(compile_commands, f)

    return context


def build_script(context):
    script_path: Path = context.project / "build.sh"

    with open(script_path, "w") as f:
        f.write(f"#!bin/bash\n")
        f.write(f"# Generated by pybuildc\n")
        f.write("\n#----------Variables-----------#\n")

        f.write(f'PROJECT="{context.project.absolute().name}"\n')
        f.write(f'CC="{context.cc}"\n')
        f.write(f'BUILD_DIR="{context.build.relative_to(context.project)}"\n')
        f.write("CFLAGS=()\n")

        f.write("\n#-------------Setup------------#\n")
        f.write(f'SCRIPT_DIR=$(dirname "$0")\n')
        f.write(f"set -xe\n")
        f.write(f"cd $SCRIPT_DIR\n")

        f.write("\n")
        f.write(f"BIN=$BUILD_DIR/bin/$PROJECT\n")
        f.write(f"mkdir -p $BUILD_DIR/bin\n")
        f.write(f"mkdir -p $BUILD_DIR/obj\n")

        if len(context.build_scripts):
            f.write("\n#---------Dependencies---------#\n")
        for script in context.build_scripts:
            f.write(f"bash {script.relative_to(context.project)}\n")

        f.write("\n#---------Compilation---------#\n")

        # set context to be
        cc = context.cc
        context.cc = "$CC"
        build = context.build
        context.build = "$BUILD_DIR"
        cflags = context.cflags
        context.cflags = (*context.cflags, "${CFLAGS[@]}")
        include_flags = context.include_flags
        context.include_flags = tuple(
            map(lambda f: f.relative_to(context.project), context.include_flags)
        )
        library_flags = context.library_flags
        context.library_flags = tuple(
            map(
                lambda f: (f[0].relative_to(context.project), f[1])
                if f[0]
                else (f[0], f[1]),
                context.library_flags,
            )
        )
        if context.bin == "exe":
            command = compile(
                map(
                    lambda file: file.relative_to(context.project),
                    context.src.rglob("*.c"),
                ),
                Path("$BIN"),
            )(context)
            f.write(" ".join(command.command))
            f.write("\n")
        elif context.bin == "static":
            command = compile_all_obj_files(
                map(
                    lambda file: file.relative_to(context.project),
                    context.src.rglob("*.c"),
                )
            )(context)
            for cmd in command:
                f.write(f"mkdir -p {cmd.output_path.parent}\n")
                f.write(" ".join(cmd.command))
                f.write("\n")
            command = link_static(tuple(map(lambda cmd: cmd.output_path, command)))(
                context
            )
            f.write(" ".join(command.command))
            f.write("\n")

        # Reset context
        context.cc = cc
        context.build = build
        context.cflags = cflags
        context.include_flags = include_flags
        context.library_flags = library_flags

    return IOResultE.from_value(context)
