import sys

from pybuildc.args import ArgsConfig, args_parse


def pybuildc(args: ArgsConfig, argv: list[str]):
    print(args)


def main():
    args, argv = args_parse(sys.argv[1:])
    pybuildc(args, argv)
