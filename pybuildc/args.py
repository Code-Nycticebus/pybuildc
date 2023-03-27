import argparse
from pathlib import Path


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A build system for the c language")
    subparser = parser.add_subparsers(dest="action") # subparserS!

    build_parser = subparser.add_parser("build")
    build_parser.add_argument("-d" ,"--directory", help="directory to build", type=Path, default=Path.cwd())

    return parser.parse_args(args)
