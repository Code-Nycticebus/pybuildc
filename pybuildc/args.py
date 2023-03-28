import argparse
from pathlib import Path


def parse_args(args: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="A build system for the c language",
    )
    subparser = parser.add_subparsers(
        dest="action",
        required=True,
        description="Build action",
    )
    new_parser = subparser.add_parser("new", help="Creates a new project")
    new_parser.add_argument(
        "directory",
        help="Name of the project directory",
        type=Path,
    )
    new_parser.add_argument(
        "--lib",
        action="store_true",
        help="creates a library template instead of a executable template.",
        default=False,
    )

    build_parser = subparser.add_parser("build", help="Builds the project")
    build_parser.add_argument(
        "-d",
        "--directory",
        help="directory to build",
        type=Path,
        default=Path.cwd(),
    )
    build_parser.add_argument(
        "-r",
        "--release",
        help="Enables optimizations and removes debug flags",
        action="store_true",
    )

    run_parser = subparser.add_parser(
        "run", help="Builds the project and runs the binary"
    )
    run_parser.add_argument(
        "-d",
        "--directory",
        help="directory to build",
        type=Path,
        default=Path.cwd(),
    )
    run_parser.add_argument(
        "-r",
        "--release",
        help="Enables optimizations and removes debug flags",
        action="store_true",
    )

    return parser.parse_known_args(args)
