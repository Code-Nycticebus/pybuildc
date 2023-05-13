from pathlib import Path
import subprocess
from typing import Iterable

from returns.io import IOResultE, IOFailure, IOSuccess
from returns.iterables import Fold

from pybuildc.domain.entities import BuildStructure, CommandEntity, CompilerEntity
from pybuildc.domain.services import (
    compile_exe,
    create_path,
    get_project_structure,
    compile_obj_files,
)


def run_test(test: Path, argv: list[str]):
    ret = subprocess.run((str(test), *argv))
    if ret.returncode:
        return IOFailure(Exception(ret))
    else:
        return IOSuccess(test)


def compile_all_tests(
    cc: CompilerEntity,
    build_dirs: BuildStructure,
    obj_files: Iterable[Path],
) -> IOResultE[Iterable[CommandEntity]]:
    return Fold.collect(
        map(
            lambda test_file: compile_exe(
                cc,
                (*obj_files, test_file),
                create_path(build_dirs.build, "test", test_file.with_suffix("").name),
            ),
            build_dirs.test.rglob("*-test.c"),
        ),
        IOResultE.from_value(()),
    ) or IOFailure(ValueError("Something wrong while compiling all tests"))


def test_builder(args, argv: list[str]) -> IOResultE:
    build_dirs = get_project_structure(args.directory, "debug")

    cc = CompilerEntity(
        cc="gcc", cflags=(), lib_flags=("-lm",), includes=(f"-I{build_dirs.src}",)
    )

    return (
        compile_obj_files(cc, build_dirs)
        .bind(
            lambda obj_file_commands: compile_all_tests(
                cc,
                build_dirs,
                tuple(map(lambda cmd: cmd.output_path, obj_file_commands)),
            )
        )
        .bind(
            lambda test_compile_commands: Fold.collect(
                map(
                    lambda test: run_test(test.output_path, argv),
                    test_compile_commands,
                ),
                IOResultE.from_value(()),
            )
            or IOFailure(ValueError("Something wrong while compiling all tests"))
        )
    )
