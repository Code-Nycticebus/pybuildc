from pathlib import Path
from typing import Literal, Protocol
import argparse


class ArgsConfig(Protocol):
    action: str
    dir: Path
    mode: Literal["debug"] | Literal["release"]
    build_dir: str


def args_parse(argv: list[str]) -> tuple[ArgsConfig, list[str]]:
    parser = argparse.ArgumentParser(
        prog="pybuildc",
        description="Builds C projects",
        epilog="",
    )
    parser.add_argument("-d", "--dir", type=Path, default=Path.cwd())
    parser.add_argument("-bd", "--build-dir")
    parser.add_argument("--cflags", type=list, nargs="?")
    parser.add_argument("-m", "--mode", choices=("debug", "release"), default="debug")

    subparser = parser.add_subparsers(dest="action", required=True)

    new = subparser.add_parser("new")
    new.add_argument("dir", type=Path)

    subparser.add_parser("build")
    subparser.add_parser("run")

    subparser.add_parser("test")
    subparser.add_parser("script")

    return parser.parse_known_args(argv)  # type: ignore
