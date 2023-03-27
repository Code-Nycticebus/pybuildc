from returns.io import IOResultE

from pybuildc.builder import build


def build_command(args) -> IOResultE:
    # TODO i should create a config here?
    return build(args.directory, not args.release)


def run_command(args) -> IOResultE:
    raise NotImplementedError(args)
