from returns.io import IOResultE


def build_command(args) -> IOResultE:
    return IOResultE.from_value(args)


def run_command(args) -> IOResultE:
    raise NotImplementedError(args)
