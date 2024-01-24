import json
from pathlib import Path
import subprocess
from pybuildc.context import Context
from pybuildc.compiler import Compiler
import os


def _build_library(context: Context, cc: Compiler) -> tuple[Path, bool]:
    # Build scripts
    if "build" in context.config and "scripts" in context.config["build"]:
        cwd = Path.cwd()
        os.chdir(context.files.project)
        for script in context.config["build"]["scripts"]:
            subprocess.run([script["cmd"], *script["args"]])
        os.chdir(cwd)

    rebuild = context.files.config in context.cache
    for dep in context.dependencies:
        if dep.build() == True:
            rebuild = True

    name = context.config["pybuildc"]["name"]

    obj_files = tuple(
        context.files.build / "obj" / f.relative_to(context.files.src).with_suffix(".o")
        for f in context.files.src_files
    )

    compile = tuple(
        (obj, src)
        for obj, src in zip(obj_files, context.files.src_files)
        if rebuild or src in context.cache
    )

    library = context.files.bin / f"lib{name}.a"
    if rebuild or compile:
        rebuild = True
        print(f"[pybuildc] building '{name}'")
        for n, (obj, src) in enumerate(compile):
            print(f"  [{(n)/len(compile):5.0%} ]: compiling '{src}'")
            subprocess.run(cc.compile_obj(src, obj), check=True)
        print(f"  [ 100% ]: compiling '{library}'")
    subprocess.run(cc.compile_lib(obj_files, library), check=True)

    return library, rebuild


def build(context: Context) -> bool:
    cc = Compiler(context)
    library, compile = _build_library(context, cc)

    rebuild = False
    for name, file in context.config.get("exe", {}).items():
        bin = context.files.project / file
        if compile or bin in context.cache:
            rebuild = True
            print(f"  [{name}] '{bin}'")
            subprocess.run(
                cc.compile_exe(bin, library, context.files.bin / name),
                check=True,
            )

    return compile or rebuild


def run(context: Context, argv: list[str]) -> None:
    build(context)
    bin_files: set[str] = set()
    for exe in context.config.get("exe", ()):
        bin_files.add(exe)

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
            / bin.relative_to(context.files.test).with_suffix("")
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
        if subprocess.run([out]).returncode != 0:
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
                + tuple(
                    context.files.project / files
                    for _, files in context.config.get("exe", {}).items()
                )
                + context.files.test_files
            ]
        )
    )
