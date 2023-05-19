from subprocess import CalledProcessError
import sys

from returns.io import IOResultE, IOFailure, IOSuccess
from returns.result import Failure, Success

from pybuildc.args import parse_args

import pybuildc.commands as commands


# TODO error handling
def error(e: Exception) -> int:
    match e:
        case FileNotFoundError():
            print(f"File not found: {e.filename}")
            return 1
        case CalledProcessError():
            print("Command exited with non zero exit code:", " ".join(e.cmd))
            return e.returncode
        case Exception():
            raise e
        case _:
            print("Unkown returntype", e)


def pybuildc(args, argv) -> IOResultE[int]:
    match args.action:
        case "new":
            return commands.new(args)
        case "build":
            return commands.build(args)
        case "run":
            return commands.run(args, argv)
        case "test":
            return commands.test(args, argv)
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
