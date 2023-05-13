from collections.abc import Iterable
from pathlib import Path
import subprocess

from returns.io import IOFailure, IOResultE, IOSuccess
from returns.iterables import Fold

from pybuildc.domain.entities import Args, CommandEntity, CompilerEntity, BuildStructure

RELEASE_WARNINGS: Args = ("-Wall", "-Wpedantic")

DEBUG_WARNINGS: Args = (
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wpedantic",
    "-Wshadow",
    "-Wnull-dereference",
    "-Wformat=2",
)

# TODO some way to disable sanitizer
DEBUG_FLAGS: Args = (
    "-ggdb",
    "-fsanitize=address,undefined,leak",
    "-fno-omit-frame-pointer",
    "-fPIC",
)

RELEASE_FLAGS: Args = ("-O2",)


def compile(
    compiler: CompilerEntity,
    files: Iterable[Path],
    output: Path,
    warnings: bool = True,
    obj: bool = False,
) -> CommandEntity:
    return CommandEntity(
        output_path=output,
        command=(
            compiler.cc,
            *compiler.includes,
            *map(str, files),
            *(DEBUG_WARNINGS if warnings else ()),
            *compiler.cflags,
            *(("-c",) if obj else compiler.lib_flags),
            "-o",
            str(output),
        ),
    )


def get_obj_file_command(
    cc: CompilerEntity, files: Iterable[Path], build_dir: Path
) -> Iterable[CommandEntity]:
    return map(
        lambda file: compile(
            cc,
            (file,),
            create_path(
                build_dir,
                "obj",
                file.with_suffix(".o").name,
            ),
            obj=True,
        ),
        filter(lambda file: file.name != "main.c", files),
    )


def create_path(*args):
    path = Path(*args)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_project_structure(directory: Path, target: str):
    return BuildStructure(
        project=directory,
        build=create_path(directory, ".build", target),
        bin=create_path(directory, ".build", target, "bin", directory.name),
        src=Path(directory, "src"),
        test=Path(directory, "tests"),
    )


def subprocess_run(cmd: CommandEntity) -> IOResultE[CommandEntity]:
    res = subprocess.run(cmd.command)
    if res.returncode:
        return IOFailure(Exception(res))
    return IOSuccess(cmd)


def subprocess_run_all(
    commands: Iterable[CommandEntity],
) -> IOResultE[Iterable[CommandEntity]]:
    return Fold.collect(
        tuple(map(subprocess_run, commands)),
        IOResultE.from_value(()),
    ) or IOFailure(ValueError("Something went wrong while processing all commands"))


def _needs_to_recompile(_):
    return True


def compile_obj_files(
    cc: CompilerEntity, build_dirs: BuildStructure
) -> IOResultE[tuple[CommandEntity, ...]]:
    obj_file_commands = tuple(
        get_obj_file_command(
            cc,
            filter(lambda file: file.name != "main.c", build_dirs.src.rglob("*.c")),
            build_dirs.build,
        )
    )
    return subprocess_run_all(filter(_needs_to_recompile, obj_file_commands)).map(
        lambda _: obj_file_commands
    )


def compile_exe(cc: CompilerEntity, files: Iterable[Path], output_path: Path):
    cmd = compile(
        cc,
        files,
        output_path,
    )
    return subprocess_run(cmd)


def compile_lib(files: Iterable[Path], output_path: Path):
    return subprocess_run(
        CommandEntity(
            output_path=output_path,
            command=(
                "ar",
                "rcs",
                str(output_path),
                *map(str, files),
            ),
        )
    )
