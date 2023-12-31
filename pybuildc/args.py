from pathlib import Path
from typing import Protocol
import argparse


class ArgsConfig(Protocol):
    action: str
    directory: Path


def args_parse(argv: list[str]) -> tuple[ArgsConfig, list[str]]:
    parser = argparse.ArgumentParser(
        prog="pybuildc",
        description="Builds C projects",
        epilog="",
    )
    parser.add_argument("-d", "--directory", type=Path, default=Path.cwd())

    subparser = parser.add_subparsers(dest="action", required=True)

    new = subparser.add_parser("new")
    new.add_argument("directory", type=Path)

    subparser.add_parser("build")
    subparser.add_parser("run")
    subparser.add_parser("test")
    subparser.add_parser("script")

    return parser.parse_known_args(argv)  # type: ignore
