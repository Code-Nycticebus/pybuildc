import os
from pathlib import Path
import subprocess
import sys

from pybuildc.new import new
from pybuildc.args import ArgsConfig, args_parse
from pybuildc.context import context_load
from pybuildc.build import build, run, test, build_commands


def pybuildc(args: ArgsConfig, argv: list[str]):
    match args.action:
        case "new":
            new(args)

        case "build":
            with context_load(args) as context:
                build(context)

        case "run":
            with context_load(args) as context:
                run(context, argv)

        case "test":
            with context_load(args) as context:
                test(context)

        case action:
            raise Exception(f"{action} is not implemented yet")

    os.chdir(args.dir)
    args.dir = Path(".")
    args.action = "command"
    with context_load(args) as context:
        build_commands(context)


def main():
    args, argv = args_parse(sys.argv[1:])
    try:
        pybuildc(args, argv)
    except subprocess.CalledProcessError as e:
        failed_cmd = e.args[1]
        print(f"[pybuildc] Error: '{' '.join(map(str, failed_cmd))}'")
