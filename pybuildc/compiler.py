from collections.abc import Iterable
from pathlib import Path

from pybuildc.context import Context

from pybuildc.types import Cmd


class Compiler:
    def __init__(self, context: Context):
        self.cc = context.config["pybuildc"]["cc"]
        self.includes = sum(
            (tuple(map(lambda f: f"-I{f}", d.include)) for d in context.dependencies),
            (f"-I{context.files.src}",),
        )
        self.lib = sum(
            map(
                lambda x: (f"-L{x[0]}", f"-l{x[1]}") if len(x) == 2 else (f"-l{x[0]}",),
                map(lambda f: f.lib, context.dependencies),
            ),
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
        )

    def compile_lib(self, obj_files: Iterable[Path], library: Path) -> Cmd:
        return ("ar", "rcs", str(library), *map(str, obj_files))
