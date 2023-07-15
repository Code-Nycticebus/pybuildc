from pathlib import Path
from typing import Any, TypedDict
from itertools import chain
import toml

from returns.io import IOResultE, impure_safe
from returns.maybe import maybe


class DependencyConfig(TypedDict):
    include_flags: tuple[str, ...]
    library_flags: tuple[str, ...]


class ProjectConfig(TypedDict):
    name: str
    version: str

    cc: str
    warnings: bool
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
    return toml.loads(config_path.read_text())


def create_project_config(config: dict[str, Any]) -> ProjectConfig:
    # ignore type because i need the dynamicness to provide default values to the dict. somewhat hacky. it throws an error if 'ProjectConfig' is not initialized correctly.
    return ProjectConfig(  # type: ignore
        warnings=config.pop("warnings", True),
        cflags=config.pop("cflags", tuple()),
        **config,
    )


def create_dependecy_config(config: dict[str, Any]) -> DependencyConfig:
    return DependencyConfig(
        # iterate over 'config' library names as keys, chain all the Iterables toghether and create a tuple.
        include_flags=tuple(chain(*(v.get("include", ()) for v in config.values()))),
        # iterate over 'config' library names as keys, chain the directory and the library flag and create a tuple
        library_flags=tuple(
            chain(
                *(
                    (v["dir"], v["lib"]) if "dir" in v else (v["lib"],)
                    for v in config.values()
                )
            )
        ),
    )


def parse_config(config: dict[str, Any]) -> Config:
    return {
        "project": create_project_config(config["project"]),
        "deps": create_dependecy_config(config.get("dependencies", dict())),
    }


def load_config(config_path: Path) -> IOResultE[Config]:
    return load_config_file(config_path).map(parse_config)
