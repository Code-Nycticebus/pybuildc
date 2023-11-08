import os
from pathlib import Path
import subprocess
from returns.io import IOFailure, IOResultE, IOSuccess
from pybuildc.domain.builder import build_bin, build_compile_commands
from pybuildc.domain.context import BuildContext


def run(args, argv) -> IOResultE[int]:
    os.chdir(args.directory)
    return (
        BuildContext.create_from_config(Path("."), args.release, args.verbose, "build")
        .bind(
            lambda context: IOSuccess(context)
            if context.bin == "exe"
            else IOFailure(Exception("Not a runable project!"))
        )
        .map(build_compile_commands)
        .bind(build_bin)
        .map(lambda exe: subprocess.run((exe, *argv)).returncode)
    )
