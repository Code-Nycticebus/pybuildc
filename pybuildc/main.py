import subprocess
import sys
import os

from pybuildc.new import new
from pybuildc.args import ArgsConfig, args_parse
from pybuildc.config import ConfigFile
from pybuildc.build import build, build_commands


def pybuildc(args: ArgsConfig, argv: list[str]):
    match args.action:
        case "new":
            new(args)
        case "build":
            build(ConfigFile.load(args.dir, args.build_dir, args.mode), argv)
        case "run":
            subprocess.run(
                [build(ConfigFile.load(args.dir, args.build_dir, args.mode), []), *argv]
            )

        case action:
            raise Exception(f"{action} is not implemented yet")

    os.chdir(args.dir)
    build_commands(
        ConfigFile.load(args.dir.relative_to(args.dir), args.build_dir, args.mode)
    )
    print(f"[pybuildc] build successful: '{args.dir.name}'")


def main():
    args, argv = args_parse(sys.argv[1:])
    try:
        pybuildc(args, argv)
    except subprocess.CalledProcessError as e:
        failed_cmd = e.args[1]
        print(f"[pybuildc] Error: {' '.join(failed_cmd)}")
