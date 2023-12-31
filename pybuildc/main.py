import sys
from pybuildc.new import new

from pybuildc.args import ArgsConfig, args_parse
from pybuildc.config import config_load
from pybuildc.builder import build


def pybuildc(args: ArgsConfig, argv: list[str]):
    match args.action:
        case "new":
            new(args)
        case "build":
            build(config_load(args.directory), argv)

        case action:
            raise Exception(f"{action} is not implemented yet")


def main():
    args, argv = args_parse(sys.argv[1:])
    pybuildc(args, argv)
