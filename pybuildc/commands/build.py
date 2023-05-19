from returns.io import IOResultE
from pybuildc.domain.builder import build_bin
from pybuildc.domain.context import BuildContext


def build(args) -> IOResultE[int]:
    return (
        BuildContext.create_from_config(
            args.directory, "release" if args.release else "debug"
        )
        .bind(build_bin)
        .map(lambda _: 0)
    )
