from dataclasses import dataclass
from pathlib import Path
import toml

import subprocess


@dataclass
class Dependency:
    name: str
    path: Path | None
    library_name: str
    include_dirs: tuple[Path, ...]
    library_dir: Path | None


def handle_static(project: Path, dep: str, config) -> Dependency:
    match config.get("dir"):
        case None:
            return Dependency(
                name=dep,
                path=None,
                library_name=config.get("l", dep),
                library_dir=None,
                include_dirs=(),
            )

        case path:
            return Dependency(
                name=dep,
                path=path,
                library_name=config.get("l", dep),
                library_dir=project / path / config["L"] if "L" in config else None,
                include_dirs=(project / path / config["I"],)
                if isinstance(config["I"], str)
                else tuple(map(lambda i: project / path / i, config["I"]))
                if "I" in config
                else (),
            )


def handle_pybuildc(project: Path, dep: str, config) -> tuple[Dependency, ...]:
    dir: Path = Path(config["dir"])
    if config.get("rebuild", False):
        subprocess.run(["pybuildc", "-d", str(project / dir), "build"])
    return (
        Dependency(
            name=dep,
            library_name=dep,
            path=project / dir,
            library_dir=project
            / dir
            / ".build"
            / config.get("build", "release")
            / "bin",
            include_dirs=(project / dir / "src",),
        ),
        *load_dependencies(
            project / dir, toml.load(project / dir / "pybuildc.toml").get("deps", {})
        ),
    )


def load_dependencies(project: Path, config: dict[str, dict]) -> tuple[Dependency, ...]:
    deps: list[Dependency] = []

    for dep, c in config.items():
        match c.get("type", "static"):
            case "static":
                deps.append(handle_static(project, dep, c))
            case "pybuildc":
                deps.extend(handle_pybuildc(project, dep, c))

    return tuple(deps)
