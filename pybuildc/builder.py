from pathlib import Path
import subprocess

from returns.io import IOResultE, IOFailure, IOSuccess, impure_safe
from returns.iterables import Fold
from returns.curry import partial

from domain.services import Compiler, Cmd


@impure_safe
def execute(cmd: Cmd):
    subprocess.run(cmd, check=True)


def convert_to_obj_file(project_directory, file: Path) -> Path:
    return Path(
        project_directory,
        ".build",
        "obj",
        file.with_suffix(".o").name)


def compile_to_obj_file(cc: Compiler, project_directory: Path, obj_file: Path):
    return execute(
        cc.compile(
            [obj_file],
            convert_to_obj_file(
                project_directory,
                obj_file),
            ["-c"]))


def build(directory: Path) -> IOResultE:
    config_file = Path(directory, "pybuildc.toml")
    if not config_file.exists():
        e = FileNotFoundError()
        e.filename = config_file
        return IOFailure(e)

    cc = Compiler.create("gcc", [], False)

    src_files = tuple(directory.rglob("src/**/*.c"))

   # TODO filter src files to the ones that need recompiling
    res = Fold.collect(
        map(partial(compile_to_obj_file, cc, directory), src_files), IOSuccess(()))
    match res:
        case IOFailure():
            return res

    obj_files = tuple(map(partial(convert_to_obj_file, directory), src_files))
    # Creates every directory needed
    obj_files[0].parent.mkdir(parents=True, exist_ok=True)

    exe_file = Path(directory, ".build", "bin", "project_name")
    exe_file.parent.mkdir(parents=True, exist_ok=True)

    res = execute(cc.compile(obj_files, exe_file, []))
    match res:
        case IOFailure():
            return res

    return IOResultE.from_value(exe_file)
