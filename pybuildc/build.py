import json
from pathlib import Path
import subprocess
from pybuildc.context import Context
from pybuildc.compiler import Compiler


def build(context: Context) -> Path:
    for dep in context.dependencies:
        dep.build()

    name = context.config["pybuildc"]["name"]

    # create obj files
    obj_files = tuple(
        context.files.build / "obj" / f.with_suffix(".o").name
        for f in context.files.src_files
    )

    compile = tuple(
        (obj, src)
        for obj, src in zip(obj_files, context.files.src_files)
        if src in context.cache
    )
    cc = Compiler(context)
    if len(compile):
        print(f"[pybuildc] building '{name}'")
    for n, (obj, src) in enumerate(compile):
        print(f"  [{(n+1)/len(compile):5.0%} ]: compiling '{src}'")
        subprocess.run(cc.compile_obj(src, obj), check=True)

    library = context.files.bin / f"lib{name}.a"
    subprocess.run(cc.compile_lib(obj_files, library))
    bin_files = tuple((context.files.project / "src" / "bin").rglob("**/*.c"))
    if len(bin_files):
        for bin in bin_files:
            if len(compile):
                print(f"  [pybuildc] bin: '{bin}'")
                subprocess.run(
                    cc.compile_exe(
                        bin, library, context.files.bin / bin.with_suffix("").name
                    ),
                    check=True,
                )

    return library


def run(context: Context, argv: list[str]):
    build(context)
    bin_files = tuple(map(lambda f: f.with_suffix("").name, context.files.bin_files))
    if context.args.exe == None:
        context.args.exe = context.config["pybuildc"]["name"]

    if context.args.exe in bin_files:
        subprocess.run(
            [context.files.bin / context.args.exe, *argv],
        )
    else:
        print(f"[pybuildc]: binary '{context.args.exe}' not found -> {bin_files}")


def test(context: Context):
    lib = build(context)
    cc = Compiler(context)
    for file in context.files.test_files:
        bin = (
            context.files.build
            / "test"
            / file.relative_to(context.files.test).with_suffix("")
        )
        subprocess.run(
            cc.compile_exe(file, lib, bin),
            check=True,
        )
        ret = subprocess.run([bin])
        if ret.returncode != 0:
            print(f"[pybuildc] test failed: {file.with_suffix('').name}")


def build_commands(context: Context):
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
