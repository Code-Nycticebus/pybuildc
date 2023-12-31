import subprocess
import sys
import os

from pybuildc.new import new
from pybuildc.args import ArgsConfig, args_parse
from pybuildc.config import ConfigFile
from pybuildc.build import build, build_commands, test


def pybuildc(args: ArgsConfig, argv: list[str]):
    match args.action:
        case "new":
            new(args)
        case "build":
            config = ConfigFile.load(args.dir, args.build_dir, args.mode)
            build(config, argv)
            config.save_cache()
        case "run":
            config = ConfigFile.load(args.dir, args.build_dir, args.mode)
            config.exe = args.exe
            if config.bin == "exe":
                subprocess.run([build(config, []), *argv])
            else:
                raise Exception("project not runnable")
            config.save_cache()
        case "test":
            config = ConfigFile.load(args.dir, args.build_dir, args.mode)
            test(config)
            config.save_cache()
        case action:
            raise Exception(f"{action} is not implemented yet")

    os.chdir(args.dir)
    build_commands(
        ConfigFile.load(
            directory=args.dir.relative_to(args.dir),
            build_dir=args.build_dir,
            mode=args.mode,
        )
    )


def main():
    args, argv = args_parse(sys.argv[1:])
    try:
        pybuildc(args, argv)
    except subprocess.CalledProcessError as e:
        failed_cmd = e.args[1]
        print(f"[pybuildc] Error: '{' '.join(failed_cmd)}'")
