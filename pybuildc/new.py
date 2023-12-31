from pathlib import Path

from pybuildc.args import ArgsConfig


def _create_path(p: Path) -> Path:
    """Creates path and all its parents"""
    p.parent.mkdir(parents=True)
    return p


def new(config: ArgsConfig):
    directory: Path = config.directory
    if directory.exists():
        raise Exception("Directory exists!")

    config_file = _create_path(directory / "pybuildc.toml")
    config_file.write_text(
        f"""\
[pybuildc]
name = "{directory.name}"
cc = "clang"
bin = "exe"

[build]
    
[deps]

"""
    )

    src_file = _create_path(directory / "src" / "main.c")
    src_file.write_text(
        """\
#include<stdio.h>

int main(void) {
    printf("Hello, World\\n");
}

"""
    )
