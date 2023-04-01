from pathlib import Path
import subprocess

from returns.io import IOResultE, impure_safe

from pybuildc.builder import build


def _create_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file


def new_command(args) -> IOResultE:
    args.directory.mkdir(parents=True)
    _create_file(
        Path(args.directory, "src", args.directory.with_suffix(".h").name),
        f"""\
#pragma once
#define LIBNAME "{args.directory.name}"
""",
    )
    if not args.lib:
        _create_file(
            Path(args.directory, "src", "main.c"),
            f"""\
#include "{args.directory.name}.h"
#include <stdio.h>
int main(void) {{ printf("Project: " LIBNAME "\\n"); }}
""",
        )

    _create_file(
        Path(args.directory, "pybuildc.toml"),
        f"""\
[project]
name="{args.directory.name}"
version="0.1.0"
""",
    )

    _create_file(
        Path(args.directory, "test", "main-test.c"),
        f"""\
#include "{args.directory.name}.h"
#include <stdio.h>
int main(void) {{ printf("Test: " LIBNAME "\\n"); }}
""",
    )

    return IOResultE.from_value(args.directory)


def build_command(args) -> IOResultE[int]:
    return build(args.directory, not args.release).map(lambda _: 0)


def run_command(args, argv) -> IOResultE[int]:
    return (
        build(args.directory, not args.release)
        .map(lambda context: str(context.bin_file))
        .bind(lambda exe: impure_safe(subprocess.run)((exe, *argv), check=True))
        .alt(lambda p: Exception("Not an exe project") if isinstance(p, FileNotFoundError) else p)
        .map(lambda process: process.returncode)
    )
