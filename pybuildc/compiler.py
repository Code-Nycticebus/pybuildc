from collections.abc import Iterable
from pathlib import Path
import platform
import shutil

from pybuildc.context import Context

from pybuildc.types import Cmd


class Compiler:
    def __init__(self, context: Context):
        self.cc = context.config["pybuildc"]["cc"]
        self.includes = sum(
            map(
                lambda f: tuple(map(lambda x: f"-I{x}", f.include)),
                context.dependencies,
            ),
            (f"-I{context.files.src}",),
        )
        self.lib: tuple[str, ...] = sum(
            map(lambda f: tuple(map(lambda x: f"-L{x}", f.lib)), context.dependencies),
            (),
        )
        self.link: tuple[str, ...] = sum(
            map(lambda f: tuple(map(lambda x: f"-l{x}", f.link)), context.dependencies),
            (),
        )
        self.cflags = [
            "-Werror",
            "-Wall",
            "-Wextra",
            "-Wshadow",
            "-Wmissing-include-dirs",
            "-pedantic",
        ]
        self.cflags.extend(
            ("-g",) if context.args.mode == "debug" else ("-O2", "-DNDEBUG")
        )
        self.cflags.extend(context.args.cflags)
        self.cflags.extend(context.config["pybuildc"].get("cflags", ()))

    def compile_obj(self, infile: Path, outfile: Path) -> Cmd:
        return (
            self.cc,
            *self.includes,
            *self.cflags,
            "-o",
            str(outfile),
            "-c",
            str(infile),
        )

    def compile_exe(self, src: Path, library: Path, outfile: Path) -> Cmd:
        return (
            self.cc,
            *self.includes,
            *self.cflags,
            "-o",
            str(outfile),
            str(src),
            str(library),
            *self.lib,
            *self.link,
        )

    def compile_lib(self, obj_files: Iterable[Path], library: Path) -> Cmd:
        if shutil.which("ar"):
            return ("ar", "rcs", str(library), *map(str, obj_files))
        elif shutil.which("lib"):
            return ("lib", f"/OUT:{library}", *map(str, obj_files))
        raise Exception("No library tool found")
