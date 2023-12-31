from pathlib import Path
from typing import Literal, Protocol
import argparse


class ArgsConfig(Protocol):
    action: str
    dir: Path
    mode: Literal["debug"] | Literal["release"]
    build_dir: str
    bin: Path | None
    exe: str | None


def args_parse(argv: list[str]) -> tuple[ArgsConfig, list[str]]:
    parser = argparse.ArgumentParser(
        prog="pybuildc",
        description="Builds C projects",
        epilog="",
    )
    parser.add_argument("-d", "--dir", type=Path, default=Path.cwd())
    parser.add_argument("-bd", "--build-dir")
    parser.add_argument("-m", "--mode", choices=("debug", "release"), default="debug")

    subparser = parser.add_subparsers(dest="action", required=True)

    new = subparser.add_parser("new")
    new.add_argument("dir", type=Path)
    new.add_argument("--bin", choices=("static", "exe"), default="exe")

    subparser.add_parser("build")
    run = subparser.add_parser("run")
    run.add_argument("-e", "--exe", default=None)

    subparser.add_parser("test")

    return parser.parse_known_args(argv)  # type: ignore
