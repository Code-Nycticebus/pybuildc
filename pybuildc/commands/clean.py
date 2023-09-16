from pathlib import Path
import shutil
from returns.io import IOResultE
import toml


def remove_dir(d: Path):
    if d.exists():
        shutil.rmtree(d)


def clean(args) -> IOResultE[int]:
    remove_dir(Path(args.directory, ".build"))
    with Path(args.directory, "pybuildc.toml").open("r") as f:
        config = toml.load(f)
        for dep in config.get("dependencies", dict()).values():
            if dep.get("dep_type") == "pybuildc":
                remove_dir(Path(dep.get("dir"), ".build"))
    return IOResultE.from_value(0)
