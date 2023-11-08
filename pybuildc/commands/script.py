import os
from pathlib import Path
from returns.io import IOResultE
from pybuildc.domain.builder import build_script
from pybuildc.domain.context import BuildContext


def script(args) -> IOResultE[int]:
    os.chdir(args.directory)
    return (
        BuildContext.create_from_config(Path("."), args.release, args.verbose, "script")
        .map(build_script)
        .map(lambda _: 0)
    )
