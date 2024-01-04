import json
from pathlib import Path
import subprocess
from pybuildc.context import Context
from pybuildc.compiler import Compiler


def _build_library(context: Context, cc: Compiler) -> tuple[Path, bool]:
    rebuild = False
    for dep in context.dependencies:
        if dep.build() == True:
            rebuild = True

    name = context.config["pybuildc"]["name"]

    obj_files = tuple(
        context.files.build / "obj" / f.with_suffix(".o").name
        for f in context.files.src_files
    )

    compile = tuple(
        (obj, src)
        for obj, src in zip(obj_files, context.files.src_files)
        if src in context.cache
    )
    if compile:
        print(f"[pybuildc] building '{name}'")
    for n, (obj, src) in enumerate(compile):
        print(f"  [{(n)/len(compile):5.0%} ]: compiling '{src}'")
        subprocess.run(cc.compile_obj(src, obj), check=True)


    library = context.files.bin / f"lib{name}.a"
    if compile:
        print(f"  [ 100% ]: compiling '{library}'")
        subprocess.run(cc.compile_lib(obj_files, library))

    return library, rebuild or bool(compile)


def build(context: Context) -> bool:
    cc = Compiler(context)
    library, compile = _build_library(context, cc)

    rebuild = False
    bin_files = (context.files.project / "src" / "bin").rglob("*.c")
    for bin in bin_files:
        if compile or bin in context.cache:
            rebuild = True
            print(f"  [pybuildc] bin: '{bin}'")
            subprocess.run(
                cc.compile_exe(
                    bin, library, context.files.bin / bin.with_suffix("").name
                ),
                check=True,
            )

    return compile or rebuild


def run(context: Context, argv: list[str]) -> None:
    build(context)
    bin_files = tuple(map(lambda f: f.with_suffix("").name, context.files.bin_files))
    if context.args.exe == None:
        context.args.exe = context.config["pybuildc"]["name"]

    if context.args.exe in bin_files:
        subprocess.run(
            [context.files.bin / context.args.exe, *argv],
        )
    else:
        print(f"[building]: binary '{context.args.exe}' not found -> {bin_files}")


def test(context: Context) -> None:
    cc = Compiler(context)
    library, compile = _build_library(context, cc)
    bin_files = tuple(context.files.test.rglob("*-test.c"))
    out_files = tuple(
        (
            context.files.build
            / context.files.test.name
            / bin.relative_to(context.files.test).with_suffix("").name
        )
        for bin in bin_files
    )

    for bin, out in zip(bin_files, out_files):
        if compile or bin in context.cache:
            print(f"  [building] test: '{bin}'")
            subprocess.run(
                cc.compile_exe(bin, library, out),
                check=True,
            )

    for bin, out in zip(bin_files, out_files):
        ret = subprocess.run([out])
        if ret.returncode != 0:
            print(f"[test] failed: {bin}")


def build_commands(context: Context) -> None:
    cc = Compiler(context)

    (context.files.project / ".build" / "compile_commands.json").write_text(
        json.dumps(
            [
                {
                    "file": str(src),
                    "arguments": cc.compile_obj(src, src.with_suffix(".o")),
                    "directory": str(context.files.project.absolute()),
                }
                for src in context.files.src_files
                + context.files.bin_files
                + context.files.test_files
            ]
        )
    )
