from pathlib import Path
import subprocess
from returns.io import IOFailure, IOResultE, IOSuccess
from pybuildc.domain.builder import build_bin
from pybuildc.domain.context import BuildContext


def run(args, argv) -> IOResultE[int]:
    return (
        BuildContext.create_from_config(
            args.directory, "release" if args.release else "debug"
        )
        .bind(
            lambda context: IOSuccess(context)
            if Path(context.src, "main.c").exists()
            else IOFailure(Exception("Not a runable project!"))
        )
        .bind(build_bin)
        .map(lambda exe: subprocess.run((exe, *argv)).returncode)
    )
