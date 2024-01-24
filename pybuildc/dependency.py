from functools import cached_property
from pathlib import Path
from typing import Protocol

from pybuildc.args import ArgsConfig
from pybuildc.files import Files, files_load
from pybuildc.config import DepConfig, config_load


class Dependency(Protocol):
    name: str
    dir: Path
    config: DepConfig

    @cached_property
    def cflags(self) -> tuple[str, ...]:
        ...

    @cached_property
    def lib(self) -> tuple[str, ...]:
        ...

    @cached_property
    def include(self) -> tuple[Path, ...]:
        ...

    def build(self) -> bool:
        ...


class Static(Dependency):
    def __init__(self, name: str, dir: Path, config: DepConfig):
        self.name = name
        self.dir = dir
        self.config = config

    @cached_property
    def cflags(self) -> tuple[str, ...]:
        return tuple(self.config.get("cflags", ()))

    @cached_property
    def lib(self) -> tuple[str, ...]:
        if "L" in self.config and "l" in self.config:
            return (
                str(self.dir / self.config["dir"] / self.config["L"]),
                self.config["l"],
            )
        return (self.config.get("l", self.name),)

    @cached_property
    def include(self) -> tuple[Path, ...]:
        if "dir" in self.config:
            return tuple(self.dir / self.config["dir"] / f for f in self.config["I"])
        return ()

    def build(self) -> bool:
        return False


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
        return sum((f.cflags for f in self.deps), tuple(self.config.get("cflags", ())))

    @cached_property
    def lib(self) -> tuple[str, ...]:
        return str(self.build_dir / "bin"), self.name

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
            return build(context)


def dependencies_load(files: Files, config: dict[str, DepConfig]) -> list[Dependency]:
    deps: list[Dependency] = []
    for dep, conf in config.items():
        match conf.get("type", "static"):
            case "static":
                deps.append(Static(dep, files.project, conf))
            case "pybuildc":
                deps.append(Pybuildc(dep, files, conf))

    return deps
