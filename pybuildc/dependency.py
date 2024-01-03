from functools import cached_property
from pathlib import Path
from typing import Protocol

from pybuildc.args import ArgsConfig
from pybuildc.files import Files, files_load
from pybuildc.config import DepConfig, config_load


class Dependency(Protocol):
    dir: Path
    config: DepConfig

    @cached_property
    def cflags(self) -> tuple[str, ...]:
        ...

    @cached_property
    def lib(self) -> tuple[Path, str]:
        ...

    @cached_property
    def include(self) -> tuple[Path, ...]:
        ...

    def build(self):
        ...


class Static(Dependency):
    def __init__(self, dir: Path, config: DepConfig):
        self.dir = dir
        self.config = config

    @cached_property
    def cflags(self) -> tuple[str, ...]:
        raise NotImplementedError()

    @cached_property
    def lib(self) -> tuple[Path, str]:
        raise NotImplementedError()

    @cached_property
    def include(self) -> tuple[Path, ...]:
        raise NotImplementedError()

    def build(self):
        raise NotImplementedError()


class Pybuildc(Dependency):
    def __init__(self, name: str, files: Files, config: DepConfig):
        self.name = name
        self.dir = files.project / config["dir"]
        self.config = config
        self.file = config_load(self.dir / "pybuildc.toml")
        self.build_dir = files.build / "deps" / name
        self.files = files_load(
            self.dir, self.config.get("mode", "release"), build=self.build_dir
        )
        self.deps = dependencies_load(self.files, self.file.get("deps", {}))

    @cached_property
    def cflags(self) -> tuple[str, ...]:
        return sum((f.cflags for f in self.deps), tuple(self.config["cflags"]))

    @cached_property
    def lib(self) -> tuple[Path, str]:
        return self.build_dir / "bin", self.name

    @cached_property
    def include(self) -> tuple[Path, ...]:
        return tuple(
            (
                *(self.config["I"] if "I" in self.config else ()),
                *sum((d.include for d in self.deps), ()),
                self.dir / "src",
            )
        )

    def build(self):
        from pybuildc.build import build
        from pybuildc.context import context_load

        class Args(ArgsConfig):
            action = "build"
            dir = self.dir
            mode = self.config.get("mode", "release")
            build_dir = self.build_dir
            bin = "static"
            exe = None
            cflags = list(self.cflags)

        with context_load(Args) as context:  # type: ignore
            build(context)


def dependencies_load(files: Files, config: dict[str, DepConfig]) -> list[Dependency]:
    deps: list[Dependency] = []
    for dep, conf in config.items():
        match conf.get("type", "static"):
            case "static":
                deps.append(Static(files.project, conf))
            case "pybuildc":
                deps.append(Pybuildc(dep, files, conf))

    return deps
