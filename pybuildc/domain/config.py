from pathlib import Path
from typing import Any, TypedDict
import toml
import platform

from returns.io import IOResultE, impure_safe
from returns.maybe import maybe

from pybuildc.domain.builder import build_script


class DependencyConfig(TypedDict):
    include_flags: tuple[str, ...]
    library_flags: tuple[str, ...]
    build_scripts: tuple[Path, ...]


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


def handle_dependencies_config(project_dir: Path, config: dict[str, Any], action: str):
    include_flags = []
    library_flags = []
    build_scripts = []

    def recursive_adding(project_path: Path, c: Config, target: str):
        include_flags.append(f"-I{(project_path/'include').relative_to(project_path)}")
        include_flags.append(f"-I{(project_path/'src')}")
        library_flags.append(f"-L{(project_path / '.build' / target / 'bin')}")
        library_flags.append(f"-l{c['project']['name']}")

        include_flags.extend(c["deps"]["include_flags"])
        library_flags.extend(c["deps"]["library_flags"])
        return c

    for val in config.values():
        if "include" in val:
            include_flags.extend(
                map(
                    lambda i: f"-I{Path(project_dir, i)}",
                    val["include"],
                )
            )

        match val.get("dep_type", "static"):
            case "static":
                library_flags.extend(
                    (
                        f"-L{Path(project_dir, val['dir'])}",
                        f"-l{val['lib']}",
                    )
                    if "dir" in val
                    else (f"-l{val['lib']}",)
                )
                if "build_script" in val:
                    build_scripts.append(val["build_script"])

            case "pybuildc":
                sub_project_path = Path(project_dir, val["dir"])
                target = val.get("target", "release")
                build_scripts.append(sub_project_path / "build.sh")

                if (
                    val.get("build", False)
                    or not (sub_project_path / ".build" / target).exists()
                ):
                    # To prevent circular import
                    from pybuildc.domain.builder import build_bin
                    from pybuildc.domain.context import BuildContext
                    from pybuildc.domain.builder import build_compile_commands

                    def add_cflags(config: BuildContext):
                        cflags: tuple[str, ...] = val.get("cflags")
                        if cflags:
                            config.cflags = (*config.cflags, *cflags)
                        return config

                    if action != "script":
                        BuildContext.create_from_config(
                            sub_project_path,
                            target == "release",
                            False,
                            action,
                        ).map(add_cflags).map(build_compile_commands).bind(
                            build_bin
                        ).unwrap()

                    BuildContext.create_from_config(
                        sub_project_path,
                        target == "release",
                        False,
                        action,
                    ).map(add_cflags).map(build_compile_commands).bind(
                        build_script
                    ).unwrap()

                load_config(sub_project_path / "pybuildc.toml", action).map(
                    lambda c: recursive_adding(sub_project_path, c, target)
                ).unwrap()

            case n:
                raise ValueError(n)

    return tuple(include_flags), tuple(library_flags), tuple(build_scripts)


def create_dependecy_config(
    project_dir: Path, config: dict[str, Any], action: str
) -> DependencyConfig:
    config.update(config.pop(platform.system().lower(), dict()))
    config.pop("windows", None)
    config.pop("linux", None)
    include_flags, library_flags, build_scripts = handle_dependencies_config(
        project_dir, config, action
    )
    return DependencyConfig(
        # iterate over 'config' library names as keys, chain all the Iterables together and create a tuple.
        include_flags=include_flags,
        library_flags=library_flags,
        build_scripts=build_scripts,
    )


def parse_config(config: dict[str, Any], action: str) -> Config:
    return {
        "project": create_project_config(config["project"]),
        "deps": create_dependecy_config(
            config["project_dir"], config.get("dependencies", dict()), action
        ),
    }


def load_config(config_path: Path, action: str) -> IOResultE[Config]:
    return load_config_file(config_path).map(
        lambda config: parse_config(config, action)
    )
