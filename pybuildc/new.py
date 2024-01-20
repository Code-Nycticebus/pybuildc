from pathlib import Path
import subprocess

from pybuildc.args import ArgsConfig


def _create_path(p: Path) -> Path:
    """Creates path and all its parents"""
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def new(config: ArgsConfig):
    directory: Path = config.dir
    if directory.exists():
        raise Exception(f"Directory exists! {directory}")

    config_file = _create_path(directory / "pybuildc.toml")
    config_file.write_text(
        f"""\
[pybuildc]
name = "{directory.name}"
cc = "clang"
bin = "{"exe" if config.bin else "static"}"
"""
    )

    if config.bin:
        src_file = _create_path(directory / "src" / "bin" / f"{directory.name}.c")
        src_file.write_text(
            f"""\
#include<stdio.h>

int main(void) {{
    printf("Hello, {directory.name}\\n");
}}

"""
        )
    else:
        src_file = _create_path(directory / "src" / f"{directory.name}.c")
        src_file.write_text(
            f"""\
#include"{directory.name}.h"
#include<stdio.h>

int foo(void) {{
    printf("Hello, World\\n");
}}

"""
        )
        inc_file = _create_path(directory / "src" / f"{directory.name}.h")
        inc_file.write_text(
            """\
#pragma once

int foo(void);

"""
        )

    clangd_file = _create_path(directory / ".clangd")
    clangd_file.write_text(
        """\
CompileFlags:
    Add: [-xc, -Wall, -Wextra, -pedantic, -Werror]
    CompilationDatabase: .build/
"""
    )

    subprocess.run(["git", "init"])
