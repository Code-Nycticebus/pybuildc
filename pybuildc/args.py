from pathlib import Path
from typing import Protocol
import argparse


class ArgsConfig(Protocol):
    directory: Path


def args_parse(argv: list[str]) -> tuple[ArgsConfig, list[str]]:
    parser = argparse.ArgumentParser(
        prog="pybuildc",
        description="Builds C projects",
        epilog="",
    )
    parser.add_argument("-d", "--directory", type=Path, default=Path.cwd())

    subparser = parser.add_subparsers(required=True)

    subparser.add_parser("build")
    subparser.add_parser("run")
    subparser.add_parser("test")
    subparser.add_parser("script")

    return parser.parse_known_args(argv)  # type: ignore
