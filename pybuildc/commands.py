from pathlib import Path

from returns.io import IOResultE

from pybuildc.builder import build

def _create_file(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    return file

def new_command(args) -> IOResultE:
    args.name.mkdir(parents=True)
    _create_file(
        Path(args.name, "src", args.name.with_suffix(".h").name), 
        f"""\
#pragma once
#define LIBNAME "{args.name.name}" 
"""
    )
    if not args.lib:
        _create_file(
            Path(args.name, "src", "main.c"),
            f"""\
#include "{args.name.name}.h"
#include <stdio.h>
int main(void) {{ printf("Project: " LIBNAME "\\n"); }}
"""    
    )


    _create_file(
        Path(args.name, "pybuildc.toml"), 
        f"""\
[project]
name="{args.name.name}"
version="0.1.0"
"""
    )

    _create_file(
        Path(args.name, "test", "main-test.c"), 
        f"""\
#include "{args.name.name}.h"
#include <stdio.h>
int main(void) {{ printf("Test: " LIBNAME "\\n"); }}
"""
    )


    return IOResultE.from_value(
            args.name
    )

def build_command(args) -> IOResultE:
    # TODO i should create a config here?
    return build(args.directory, not args.release)


def run_command(args) -> IOResultE:
    raise NotImplementedError(args)
