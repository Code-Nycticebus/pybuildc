import os
from pathlib import Path
from returns.io import IOResultE
from pybuildc.domain.builder import build_bin, build_compile_commands
from pybuildc.domain.context import BuildContext


def build(args) -> IOResultE[int]:
    os.chdir(args.directory)
    return (
        BuildContext.create_from_config(Path("."), args.release, args.verbose, "build")
        .map(build_compile_commands)
        .bind(build_bin)
        .map(lambda _: 0)
    )
