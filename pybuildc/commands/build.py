from returns.io import IOResultE
from pybuildc.domain.builder import build_bin, build_compile_commands
from pybuildc.domain.context import BuildContext


def build(args) -> IOResultE[int]:
    return (
        BuildContext.create_from_config(
            args.directory, "release" if args.release else "debug", args.verbose
        )
        .map(build_compile_commands)
        .bind(build_bin)
        .map(lambda _: 0)
    )
