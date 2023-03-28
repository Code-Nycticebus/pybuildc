from subprocess import CalledProcessError
import sys

from returns.io import IOResultE, IOFailure, IOSuccess


def dev_import_module():
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))


if __name__ == "__main__":
    dev_import_module()

from pybuildc.args import parse_args
from pybuildc.commands import build_command, new_command, run_command


# TODO error handling
def error(e: Exception) -> int:
    match e:
        case FileNotFoundError():
            # TODO args[0] because of custom error
            print(f"File not found: {e.filename}")
            return 1
        case CalledProcessError():
            print(" ".join(e.cmd))
            return e.returncode
        case _:
            raise e


def pybuildc(args) -> IOResultE:
    match args.action:
        case "new":
            return new_command(args)
        case "build":
            return build_command(args)
        case "run":
            return run_command(args)
        case _:
            pass

    return IOFailure(Exception("argument not implemented"))


def main() -> int:
    args = parse_args(sys.argv[1:])

    match pybuildc(args):
        case IOSuccess(r):
            print(r.unwrap())
        case IOFailure(e):
            return error(e.failure())
        case _:
            pass

    return 0


# Is run in development only
if __name__ == "__main__":
    exit(main())
