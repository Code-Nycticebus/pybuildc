from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import tomllib
from collections import defaultdict
import pickle
from itertools import chain
from typing import Literal


@dataclass
class Dependency:
    name: str
    path: Path | None
    lib_name: str
    include_dirs: tuple[Path, ...]
    lib_dir: Path | None
    cflags: tuple[str, ...]
    config: ConfigFile | None = None

    @staticmethod
    def static(project: Path, dep: str, config) -> Dependency:
        match config.get("dir"):
            case None:
                return Dependency(
                    name=dep,
                    path=None,
                    lib_name=config.get("l", dep),
                    lib_dir=None,
                    include_dirs=(),
                    cflags=config.get("cflags", ()),
                )

            case path:
                return Dependency(
                    name=dep,
                    path=path,
                    lib_name=config.get("l", dep),
                    lib_dir=project / path / config["L"] if "L" in config else None,
                    include_dirs=(project / path / config["I"],)
                    if isinstance(config["I"], str)
                    else tuple(map(lambda i: project / path / i, config["I"]))
                    if "I" in config
                    else (),
                    cflags=config.get("cflags", ()),
                )

    @staticmethod
    def pybuildc(
        project: Path, build_dir: Path, dep: str, config
    ) -> tuple[Dependency, ...]:
        dir: Path = Path(project, config["dir"])

        return (
            Dependency(
                name=dep,
                lib_name=dep,
                lib_dir=build_dir / dep / config.get("mode", "release") / "bin",
                path=dir,
                include_dirs=(dir / "src",),
                cflags=config.get("cflags", ()),
                config=ConfigFile.load(
                    directory=dir,
                    build_dir=build_dir / dep / config.get("mode", "release"),
                    mode=config.get("mode", "release"),
                ),
            ),
            *_load_dependencies(
                dir,
                build_dir,
                tomllib.loads((dir / "pybuildc.toml").read_text()).get("deps", {}),
            ),
        )


def _load_dependencies(
    project: Path,
    build_dir: Path,
    config: dict[str, dict],
) -> tuple[Dependency, ...]:
    deps: list[Dependency] = []

    for dep, c in config.items():
        match c.get("type", "static"):
            case "static":
                deps.append(Dependency.static(project, dep, c))
            case "pybuildc":
                deps.extend(Dependency.pybuildc(project, build_dir, dep, c))

    return tuple(deps)


class Cache:
    def __init__(self, path: Path, build_dir: Path, deps, include_dir):
        self.build_dir = build_dir
        self._load_cache(path, deps, include_dir)

    @staticmethod
    def _load_pickle(path: Path) -> dict[Path, float]:
        if not path.exists():
            return {}
        return pickle.loads(path.read_bytes())

    @staticmethod
    def _save_pickle(path: Path, files: tuple[Path, ...]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps({path: path.stat().st_mtime for path in files}))

    def _build_dependency_dict(
        self, files: tuple[Path, ...], include_dirs: tuple[Path, ...]
    ) -> dict[Path, tuple[Path, ...]]:
        deps: dict[Path, tuple[Path, ...]] = defaultdict(tuple)
        for file in files:
            for line in file.open().readlines():
                if line.startswith("#include") and '"' in line:
                    idx = line.find('"')
                    include = line[idx + 1 : line.find('"', idx + 1)]
                    include_files = tuple(
                        filter(
                            lambda f: f.exists(),
                            map(lambda d: d / include, include_dirs),
                        )
                    )
                    deps[file] = include_files

        return deps

    def _has_changed_dep(
        self, file: Path, deps: dict[Path, tuple[Path, ...]], cache: set[Path]
    ) -> bool:
        if file in cache:
            return True
        if cache.intersection(deps[file]):
            return True
        return any(map(lambda f: self._has_changed_dep(f, deps, cache), deps[file]))

    def _load_cache(
        self,
        directory: Path,
        dependencies: list[Dependency],
        include_dir: tuple[Path, ...],
    ):
        config_file = directory / "pybuildc.toml"
        self.file_m_times = self._load_pickle(self.build_dir / "cache.pckl")
        self.files = tuple(
            chain(
                (directory / "src").rglob("./**/*.[h|c]"),
                (directory / "test").rglob("./**/*.[h|c]"),
                sum(
                    (
                        tuple((d.config.dir / "src").rglob("./**/*.[h|c]"))
                        for d in dependencies
                        if d.config
                    ),
                    (),
                ),
            )
        )

        if self.file_m_times.get(config_file, 0) < config_file.stat().st_mtime:
            self.cache = set(self.files)
            return

        self.cache = {
            file
            for file in self.files
            if self.file_m_times.get(file, 0) < file.stat().st_mtime
        }

        included_files = self._build_dependency_dict(self.files, include_dir)
        self.cache.update(
            filter(
                lambda f: self._has_changed_dep(f, included_files, self.cache),
                self.files,
            )
        )

    def save_cache(self, dir: Path):
        self._save_pickle(
            self.build_dir / "cache.pckl",
            (
                *self.files,
                dir / "pybuildc.toml",
            ),
        )


@dataclass
class ConfigFile:
    dir: Path
    name: str
    bin: Literal["static"] | Literal["exe"]
    mode: Literal["debug"] | Literal["release"]
    cc: str

    cache: Cache
    dependencies: tuple[Dependency, ...]
    include_dirs: tuple[Path, ...]
    cflags: list[str]

    files: tuple[Path, ...]

    build_dir: Path
    bin_dir: Path
    exe: str | None = None

    @staticmethod
    def load(
        directory: Path,
        build_dir: str | Path | None,
        mode: Literal["debug"] | Literal["release"],
    ) -> ConfigFile:
        bd = Path(build_dir) if build_dir else directory / ".build" / mode
        file = tomllib.loads((directory / "pybuildc.toml").read_text())
        deps = _load_dependencies(directory, bd, file.get("deps", {}))
        include_dirs = (
            directory / "src",
            *sum(map(lambda x: x.include_dirs, deps), ()),
        )
        cache = Cache(directory, bd, deps, include_dirs)

        return ConfigFile(
            dir=directory,
            build_dir=bd,
            bin_dir=bd / "bin",
            mode=mode,
            files=tuple((directory / "src").rglob("*.[h|c]")),
            cache=cache,
            dependencies=deps,
            include_dirs=include_dirs,
            cflags=file["pybuildc"].pop("cflags", ()),
            **file["pybuildc"],
        )

    def save_cache(self):
        self.cache.save_cache(self.dir)
