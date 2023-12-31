from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from pybuildc.config import ConfigFile


@dataclass
class Command:
    out: Path
    args: tuple[str, ...]


class Compiler:
    def __init__(self, config: ConfigFile) -> None:
        self._config = config

    def compile_obj(self, src: Path, out: Path) -> Command:
        return Command(
            out=out,
            args=(
                self._config.cc,
                *map(lambda f: f"-I{f}", self._config.include_dirs),
                "-c",
                str(src),
                "-o",
                str(out),
            ),
        )

    def compile_exe(self, src_files: Iterable[Path], out: Path) -> Command:
        return Command(
            out=out,
            args=(
                self._config.cc,
                *map(lambda f: f"-I{f}", self._config.include_dirs),
                *map(str, src_files),
                *sum(
                    map(
                        lambda d: (f"-L{d.lib_dir}", f"-l{d.lib_name}")
                        if d.lib_dir
                        else (f"-l{d.lib_name}",),
                        self._config.dependencies,
                    ),
                    (),
                ),
                "-o",
                str(out),
            ),
        )

    def compile_lib(self, src_files: Iterable[Path], out: Path):
        return Command(
            out=out,
            args=("ar", "rcs", str(out), *map(str, src_files)),
        )


def _validate_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _create_obj_filename(config: ConfigFile, file: Path) -> Path:
    return (
        config.build_dir
        / "obj"
        / file.relative_to(config.dir / "src").with_suffix(".o")
    )


def build(config: ConfigFile, cflags: list[str]):
    for d in config.dependencies:
        if d.config:
            build(d.config, [])

    cc = Compiler(config)

    output = _validate_path(
        config.bin_dir / config.name
        if config.bin == "exe"
        else config.bin_dir / f"lib{config.name}.a"
    )

    src_files = tuple(filter(lambda f: f.name.endswith(".c"), config.files))
    obj_files = tuple(map(lambda f: _create_obj_filename(config, f), src_files))

    compile_files = tuple(src for src in src_files if src in config.cache.cache)
    for n, src in enumerate(compile_files):
        if n == 0:
            print(f"[pybuildc] building '{config.name}'")
        print(f"  [{(n+1)/len(compile_files): 5.0%}]: compiling '{src}'")
        cmd = cc.compile_obj(src, _validate_path(_create_obj_filename(config, src)))
        subprocess.run(cmd.args, check=True)

    cmd = (
        cc.compile_exe(obj_files, output)
        if config.bin == "exe"
        else cc.compile_lib(obj_files, output)
    )
    subprocess.run(cmd.args)
    if 0 < len(compile_files):
        print(f"[pybuildc] finished '{config.name}'")

    config.save_cache()
    return output


def build_commands(config: ConfigFile):
    cc = Compiler(config)

    src_files = tuple(
        map(
            lambda file: file.relative_to(config.dir),
            filter(lambda f: f.name.endswith(".c"), config.files),
        )
    )

    _validate_path(config.dir / ".build" / "compile_commands.json").write_text(
        json.dumps(
            [
                {
                    "file": str(src),
                    "arguments": cc.compile_obj(src, src.with_suffix(".o")).args,
                    "directory": str(config.dir.absolute()),
                }
                for src in src_files
            ]
        )
    )
