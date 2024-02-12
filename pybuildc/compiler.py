from collections.abc import Iterable
from pathlib import Path
import platform

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
            "-Wconversion",
            "-Wbad-function-cast",
            "-Wcast-qual",
            "-Wfloat-equal",
            "-Wformat=2",
            "-Wmissing-declarations",
            "-Wmissing-include-dirs",
            "-Wmissing-prototypes",
            "-Wnested-externs",
            "-Wpointer-arith",
            "-Wredundant-decls",
            "-Wsequence-point",
            "-Wshadow",
            "-Wstrict-prototypes",
            "-Wswitch",
            "-Wundef",
            "-Wunreachable-code",
            "-Wunused-but-set-parameter",
            "-Wwrite-strings",
            "-pedantic",
        ]
        self.cflags.extend(("-g",) if context.args.mode == "debug" else ("-O2",))
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
        if platform.system() == "Windows":
            return ("lib", f"/OUT:{library}", *map(str, obj_files))
        else:
            return ("ar", "rcs", str(library), *map(str, obj_files))
