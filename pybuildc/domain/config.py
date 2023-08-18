from pathlib import Path
from typing import Any, TypedDict
import toml
import platform

from returns.io import IOResultE, impure_safe
from returns.maybe import maybe


class DependencyConfig(TypedDict):
    include_flags: tuple[str, ...]
    library_flags: tuple[str, ...]


class ProjectConfig(TypedDict):
    name: str
    version: str

    cc: str
    cflags: tuple[str, ...]
    bin: str


class Config(TypedDict):
    project: ProjectConfig
    deps: DependencyConfig


@maybe
def get(d: dict, key: Any) -> Any:
    return d.get(key)


@impure_safe
def load_config_file(config_path: Path):
    dic = toml.loads(config_path.read_text())
    dic["project_dir"] = config_path.parent
    return dic


def create_project_config(config: dict[str, Any]) -> ProjectConfig:
    # ignore type because i need the dynamicness to provide default values to the dict. somewhat hacky. it throws an error if 'ProjectConfig' is not initialized correctly.
    return ProjectConfig(  # type: ignore
        cflags=config.pop("cflags", tuple()),
        **config,
    )


def handle_dependencies_config(project_dir: Path, config: dict[str, Any]):
    include_flags = []
    library_flags = []

    def recursive_adding(project_path: Path, c: Config, target: str):
        include_flags.append(f"-I{project_path/'include'}")
        include_flags.append(f"-I{project_path/'src'}")

        library_flags.append(f"-L{project_path / '.build' / target / 'bin'}")
        library_flags.append(f"-l{c['project']['name']}")

        include_flags.extend(c["deps"]["include_flags"])
        library_flags.extend(c["deps"]["library_flags"])
        return c

    for val in config.values():
        if "include" in val:
            include_flags.extend(map(lambda i: f"-I{i}", val["include"]))

        match val.get("dep_type", "static"):
            case "static":
                library_flags.extend(
                    (
                        f"-L{Path(project_dir, val['dir']).absolute().resolve()}",
                        f"-l{val['lib']}",
                    )
                    if "dir" in val
                    else (f"-l{val['lib']}",)
                )

            case "pybuildc":
                sub_project_path = Path(val["dir"])
                load_config(sub_project_path / "pybuildc.toml").map(
                    lambda c: recursive_adding(
                        sub_project_path, c, val.get("target", "release")
                    )
                ).unwrap()

            case n:
                raise ValueError(n)

    return tuple(include_flags), tuple(library_flags)


def create_dependecy_config(
    project_dir: Path, config: dict[str, Any]
) -> DependencyConfig:
    config.update(config.pop(platform.system().lower(), dict()))
    config.pop("windows", None)
    config.pop("linux", None)
    include_flags, library_flags = handle_dependencies_config(project_dir, config)
    return DependencyConfig(
        # iterate over 'config' library names as keys, chain all the Iterables together and create a tuple.
        include_flags=include_flags,
        library_flags=library_flags,
    )


def parse_config(config: dict[str, Any]) -> Config:
    return {
        "project": create_project_config(config["project"]),
        "deps": create_dependecy_config(
            config["project_dir"], config.get("dependencies", dict())
        ),
    }


def load_config(config_path: Path) -> IOResultE[Config]:
    return load_config_file(config_path).map(parse_config)
