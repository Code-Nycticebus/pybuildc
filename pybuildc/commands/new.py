from pathlib import Path
from returns.io import IOResultE

from pybuildc.domain.context import BuildContext
from pybuildc.domain.builder import build_compile_commands


def _create_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file


def new(args) -> IOResultE[int]:
    args.directory.mkdir(parents=True)
    _create_file(
        Path(args.directory, "src", args.directory.with_suffix(".h").name),
        f"""\
#pragma once
#define {args.directory.name.capitalize()} "{args.directory.name}"
""",
    )

    if not args.lib:
        _create_file(
            Path(args.directory, "src", "main.c"),
            f"""\
#include "{args.directory.name}.h"
#include <stdio.h>
int main(void) {{ printf("Project: " {args.directory.name.capitalize()} "\\n"); }}
""",
        )

    _create_file(
        Path(args.directory, "pybuildc.toml"),
        f"""\
[project]
name="{args.directory.name}"
version="0.1.0"
cc="gcc"
bin="{"static" if args.lib else "exe"}"
""",
    )

    _create_file(
        Path(args.directory, "tests", "main-test.c"),
        f"""\
#include "{args.directory.name}.h"
#include <stdio.h>
int main(void) {{ printf("Test: " LIBNAME "\\n"); }}
""",
    )

    _create_file(
        Path(args.directory, ".clangd"),
        """\
CompileFlags:
    CompilationDatabase: .build/
""",
    )

    return (
        BuildContext.create_from_config(args.directory, "debug", False)
        .map(build_compile_commands)
        .map(lambda _: 0)
    )
