from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import json

from pybuildc.config import ConfigFile, Dependency


@dataclass
class Command:
    out: Path
    args: tuple[str, ...]


class Compiler:
    def __init__(self, config: ConfigFile, cflags: list[str]) -> None:
        self._config = config
        self.cflags = []
        self.cflags.extend(config.cflags)
        self.cflags.extend(cflags)
        self.cflags.extend(
            ("-O2",)
            if config.mode == "release"
            else (
                "-Werror",
                "-Wall",
                "-Wextra",
                "-pedantic",
            )
        )

    def compile_obj(self, src: Path, out: Path) -> Command:
        return Command(
            out=out,
            args=(
                self._config.cc,
                *self.cflags,
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
                *self.cflags,
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
            d.config.save_cache()

    cc = Compiler(config, cflags)

    src_files = tuple(
        filter(lambda f: f.name.endswith(".c") and "bin" not in f.parts, config.files)
    )
    obj_files = tuple(map(lambda f: _create_obj_filename(config, f), src_files))

    compile_files = tuple(src for src in src_files if src in config.cache.cache)
    if len(compile_files):
        print(f"[pybuildc] building '{config.name}'")
    for n, src in enumerate(compile_files):
        print(f"  [{(n+1)/len(compile_files): 5.0%}]: compiling '{src}'")
        cmd = cc.compile_obj(src, _validate_path(_create_obj_filename(config, src)))
        subprocess.run(cmd.args, check=True)

    bin_files = {
        f.with_suffix("").name for f in (config.dir / "src" / "bin").rglob("**/*.c")
    }

    if config.exe in bin_files:
        bin_file = config.dir / "src" / "bin" / f"{config.exe}.c"
    elif config.exe != None:
        raise Exception("pls choose from these binaries:", bin_files)
    else:
        bin_file = config.dir / "src" / "bin" / f"{config.name}.c"

    output = _validate_path(
        config.bin_dir / bin_file.with_suffix("").name
        if config.bin == "exe"
        else config.bin_dir / f"lib{config.name}.a"
    )

    cmd = (
        cc.compile_exe(
            (
                *obj_files,
                bin_file,
            ),
            output,
        )
        if config.bin == "exe"
        else cc.compile_lib(obj_files, output)
    )
    subprocess.run(cmd.args)

    build_tests(config)

    return output


def build_commands(config: ConfigFile):
    cc = Compiler(config, [])

    src_files = tuple(
        map(
            lambda file: file.relative_to(config.dir),
            filter(lambda f: f.name.endswith(".c"), config.cache.files),
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


def build_tests(config: ConfigFile):
    config.dependencies = (
        *config.dependencies,
        Dependency(
            name=config.name,
            lib_name=config.name,
            lib_dir=config.bin_dir,
            path=config.dir,
            include_dirs=(config.dir / "src",),
            cflags=(),
            config=config,
        ),
    )
    cc = Compiler(
        config,
        [],
    )
    tests = (
        (
            _validate_path(
                config.build_dir
                / "test"
                / file.with_suffix("").relative_to(config.dir / "test")
            ),
            file,
        )
        for file in (config.dir / "test").rglob("**/*-test.c")
    )
    test_files = tuple((out, file) for out, file in tests if file in config.cache.cache)
    if len(test_files):
        print(f"[pybuildc]: building tests: '{config.name}'")
        for n, (out, file) in enumerate(test_files):
            cmd = cc.compile_exe(
                (file,),
                out,
            )
            print(f"  [{(n+1)/len(test_files): 5.0%}]: compiling '{file}'")
            subprocess.run(cmd.args, check=True)


def test(config: ConfigFile):
    config.bin = "static"
    build(config, [])

    tests = tuple(
        config.build_dir
        / "test"
        / file.with_suffix("").relative_to(config.dir / "test")
        for file in sorted(
            (config.dir / "test").rglob("**/*-test.c"), key=lambda f: f.stat().st_mtime
        )
    )
    cwd = Path.cwd()
    os.chdir(config.dir)
    for test in tests:
        if subprocess.run([test.relative_to(config.dir)]).returncode != 0:
            raise Exception(f"Test failed: {test.name}")
    os.chdir(cwd)
