import sys
from pybuildc.build import build
from pybuildc.new import new

from pybuildc.args import ArgsConfig, args_parse


def pybuildc(args: ArgsConfig, argv: list[str]):
    match args.action:
        case "new":
            new(args)
        case "build":
            build(args, argv)
        case action:
            raise Exception(f"{action} is not implemented yet")


def main():
    args, argv = args_parse(sys.argv[1:])
    pybuildc(args, argv)
