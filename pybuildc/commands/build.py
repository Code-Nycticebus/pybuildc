from pathlib import Path
from typing import Iterable

from returns.io import IOResultE


from pybuildc.domain.entities import BuildStructure, CommandEntity, CompilerEntity
from pybuildc.domain.services import (
    compile_exe,
    compile_lib,
    get_project_structure,
    compile_obj_files,
)


def compile_bin(
    cc: CompilerEntity,
    build_dirs: BuildStructure,
    obj_files: Iterable[Path],
) -> IOResultE[CommandEntity]:
    main = Path(build_dirs.src, "main.c")
    if main.exists():
        return compile_exe(cc, (*obj_files, main), build_dirs.bin)
    else:
        return compile_lib(obj_files, build_dirs.bin)


def project_builder(args) -> IOResultE[Path]:
    build_dirs = get_project_structure(args.directory, "" if args.release else "debug")

    cc = CompilerEntity(
        cc="gcc",
        cflags=(),
        lib_flags=("-lm",),
        includes=(),
    )

    return (
        compile_obj_files(cc, build_dirs)
        .bind(
            lambda obj_file_commands: compile_bin(
                cc, build_dirs, map(lambda cmd: cmd.output_path, obj_file_commands)
            )
        )
        .map(lambda ce: ce.output_path)
    )
