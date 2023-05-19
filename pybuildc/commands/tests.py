from pathlib import Path
import subprocess
from typing import Iterable

from returns.curry import partial
from returns.io import IOResultE

from pybuildc.domain.builder import build_test_files
from pybuildc.domain.context import BuildContext


# Maybe a test result type would be usefull
def run_all_tests(
    tests: Iterable[Path], argv: Iterable[str]
) -> IOResultE[tuple[Path, ...]]:
    failed: tuple[Path, ...] = ()
    succ: tuple[Path, ...] = ()

    for test in tests:
        ret = subprocess.run((str(test), *argv))
        if ret.returncode == 0:
            succ += (test,)
        else:
            failed += (test,)

    if failed:
        return IOResultE.from_failure(Exception(failed))
    else:
        return IOResultE.from_value(succ)


def test(args, argv) -> IOResultE[int]:
    return (
        BuildContext.create_from_config(args.directory, "debug")
        .bind(build_test_files)
        .bind(partial(run_all_tests, argv=argv))
        .map(lambda _: 0)
    )
