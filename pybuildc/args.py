import argparse
from pathlib import Path
from pybuildc.__version__ import __version__


def parse_args(args: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="A build system for the c language",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument(
        "-d",
        "--directory",
        help="directory to build",
        type=Path,
        default=Path.cwd(),
    )
    subparser = parser.add_subparsers(
        dest="action",
        required=True,
        description="Build action",
    )

    new_parser = subparser.add_parser("new", help="Creates a new project")
    # makes directory a required argument
    new_parser.add_argument(
        "directory",
        help="Name of the new project directory",
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
        "--release",
        help="Enables optimizations and removes debug flags",
        action="store_true",
    )

    run_parser = subparser.add_parser(
        "run", help="Builds the project and runs the binary"
    )
    run_parser.add_argument(
        "--release",
        help="Enables optimizations and removes debug flags",
        action="store_true",
    )

    test_parser = subparser.add_parser(
        "test",
        help="Builds and runs tests in 'tests' folder. '*-test.c' is treated as the 'main' file.",
    )
    test_parser.add_argument("--file", help="Runs only one specific '*-test.c' file.")

    return parser.parse_known_args(args)
