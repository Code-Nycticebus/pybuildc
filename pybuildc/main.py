import sys
from args import parse_args

from returns.io import IOResultE, IOFailure, IOSuccess

from commands import build_command, run_command


# TODO error handling


def pybuildc(args) -> IOResultE:
    match args.action:
        case 'build':
            return build_command(args)
        case 'run':
            return run_command(args)
        case _: pass

    return IOFailure(Exception("argument not implemented"))


def main() -> int:
    args = parse_args(sys.argv[1:])

    match pybuildc(args):
        case IOSuccess(r):
            print(r.unwrap())
            return 0
        case IOFailure(e):
            raise e.failure()

        case _: return 1


# Is run in development only
if __name__ == "__main__":
    exit(main())
