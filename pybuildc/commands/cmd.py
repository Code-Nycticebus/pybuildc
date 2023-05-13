import subprocess
from returns.io import IOResultE

from pybuildc.commands.new import new_project
from pybuildc.commands.build import project_builder
from pybuildc.commands.tests import test_builder


def new(args):
    return new_project(args)


def build(args) -> IOResultE[int]:
    return project_builder(args).map(lambda _: 0)


def run(args, argv) -> IOResultE[int]:
    return project_builder(args).map(
        lambda exe_path: res.returncode
        if (res := subprocess.run((str(exe_path, *argv))))
        else 0
    )


def test(args, argv) -> IOResultE[int]:
    return test_builder(args, argv)
