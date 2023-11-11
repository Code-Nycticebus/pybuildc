from pathlib import Path
from typing import Any, TypedDict
import toml
import platform

from returns.io import IOResultE, impure_safe
from returns.maybe import maybe

from pybuildc.domain.builder import build_script


class DependencyConfig(TypedDict):
    include_flags: tuple[Path, ...]
    library_flags: tuple[tuple[Path, str], ...]
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


def handle_dependencies_config(project_dir: Path, config: dict[str, Any]):
    include_flags = []
    library_flags = []
    build_scripts = []

    def recursive_adding(project_path: Path, c: Config, target: str):
        include_flags.append(project_path / "include")
        include_flags.append(project_path / "src")
        library_flags.append(
            (project_path / ".build" / target / "bin", f"{c['project']['name']}")
        )
        include_flags.extend(c["deps"]["include_flags"])
        library_flags.extend(c["deps"]["library_flags"])
        return c

    for val in config.values():
        if "include" in val:
            include_flags.extend(
                map(
                    lambda i: Path(project_dir, i),
                    val["include"],
                )
            )

        match val.get("dep_type", "static"):
            case "static":
                library_flags.append(
                    (
                        Path(project_dir, val["dir"]),
                        val["lib"],
                    )
                    if "dir" in val
                    else ("", val["lib"])
                )
                if "build_script" in val:
                    build_script_path = project_dir / Path(val["build_script"])
                    build_scripts.append(build_script_path)
                    if (
                        "dir" in val
                        and not Path(
                            project_dir, val["dir"], f"lib{val['lib']}.a"
                        ).exists()
                    ):
                        import os

                        cwd = Path.cwd()
                        print(project_dir / build_script_path.parent)
                        os.chdir(build_script_path.parent)
                        os.system(f"sh {build_script_path.name}")
                        os.chdir(cwd)

            case "pybuildc":
                sub_project_path = Path(project_dir, val["dir"])
                target = val.get("target", "release")
                build_scripts.append(sub_project_path / "build.sh")

                def build(_):
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

                        return (
                            BuildContext.create_from_config(
                                sub_project_path,
                                target == "release",
                                False,
                            )
                            .map(add_cflags)
                            .map(build_compile_commands)
                            .bind(build_script)
                            .bind(build_bin)
                        )

                load_config(sub_project_path / "pybuildc.toml").map(
                    lambda c: recursive_adding(sub_project_path, c, target)
                ).map(build).unwrap()

            case n:
                raise ValueError(n)

    return tuple(include_flags), tuple(library_flags), tuple(build_scripts)


def create_dependecy_config(
    project_dir: Path, config: dict[str, Any]
) -> DependencyConfig:
    config.update(config.pop(platform.system().lower(), dict()))
    config.pop("windows", None)
    config.pop("linux", None)
    include_flags, library_flags, build_scripts = handle_dependencies_config(
        project_dir, config
    )
    return DependencyConfig(
        # iterate over 'config' library names as keys, chain all the Iterables together and create a tuple.
        include_flags=include_flags,
        library_flags=library_flags,
        build_scripts=build_scripts,
    )


def parse_config(config: dict[str, Any]) -> Config:
    return {
        "project": create_project_config(config["project"]),
        "deps": create_dependecy_config(
            config["project_dir"], config.get("dependencies", dict())
        ),
    }


def load_config(config_path: Path) -> IOResultE[Config]:
    return load_config_file(config_path).map(lambda config: parse_config(config))
