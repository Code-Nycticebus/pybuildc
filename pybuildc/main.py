from subprocess import CalledProcessError
import sys

from returns.io import IOResultE, IOFailure, IOSuccess
from returns.result import Failure, Success

from pybuildc.args import parse_args
from pybuildc.commands import build_command, new_command, run_command


# TODO error handling
def error(e: Exception) -> int:
    match e:
        case FileNotFoundError():
            print(f"File not found: {e.filename}")
            return 1
        case CalledProcessError():
            print(" ".join(e.cmd))
            return e.returncode
        case _:
            raise e


def pybuildc(commands, argv) -> IOResultE[int]:
    match commands.action:
        case "new":
            return new_command(commands)
        case "build":
            return build_command(commands)
        case "run":
            return run_command(commands, argv)
        case action:
            return IOFailure(
                NotImplementedError(f"action '{action}' is not implemented")
            )


def main() -> int:
    args, argv = parse_args(sys.argv[1:])

    match pybuildc(args, argv):
        case IOSuccess(Success(returncode)):
            return returncode
        case IOFailure(Failure(e)):
            return error(e)
        case unknown:
            raise TypeError(
                f"pybuildc should return a 'IOResultE' instead got {type(unknown)}"
            )
