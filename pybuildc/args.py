from pathlib import Path
from typing import Protocol
import argparse

from pybuildc.__version__ import __version__
from pybuildc.types import Action, Bin, Mode


class ArgsConfig(Protocol):
    action: Action
    dir: Path
    mode: Mode
    build_dir: Path | None
    bin: Bin
    exe: str | None
    cflags: list[str]


def args_parse(argv: list[str]) -> tuple[ArgsConfig, list[str]]:
    parser = argparse.ArgumentParser(
        prog="pybuildc",
        description="Builds C projects",
        epilog="",
    )
    parser.add_argument("-d", "--dir", type=Path, default=Path.cwd())
    parser.add_argument("-bd", "--build-dir")
    parser.add_argument("-m", "--mode", choices=("debug", "release"), default="debug")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--cflags", default=tuple())

    subparser = parser.add_subparsers(dest="action", required=True)

    new = subparser.add_parser("new")
    new.add_argument("dir", type=Path)
    new.add_argument("--bin", choices=("static", "exe"), default="exe")

    subparser.add_parser("build")
    run = subparser.add_parser("run")
    run.add_argument("-e", "--exe", default=None)

    test = subparser.add_parser("test")
    test.add_argument("-e", "--exe", default=None)

    return parser.parse_known_args(argv)  # type: ignore
