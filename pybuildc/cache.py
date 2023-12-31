from collections import defaultdict
import pickle
from pathlib import Path
from itertools import chain


def _load_pickle(path: Path) -> dict[Path, float]:
    if not path.exists():
        return {}
    return pickle.loads(path.read_bytes())


def _save_pickle(path: Path, files: tuple[Path, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps({path: path.stat().st_mtime for path in files}))


def _build_dependency_dict(
    files: tuple[Path, ...], include_dirs: tuple[Path, ...]
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
    file: Path, deps: dict[Path, tuple[Path, ...]], cache: set[Path]
) -> bool:
    if file in cache:
        return True
    if cache.intersection(deps[file]):
        return True
    return any(map(lambda f: _has_changed_dep(f, deps, cache), deps[file]))


def load_cache(directory: Path, include_dir: tuple[Path, ...]) -> set[Path]:
    config_file = directory / "pybuildc.toml"
    file_m_times = _load_pickle(directory / ".build/cache.pckl")
    files = tuple(
        chain(directory.rglob("./src/*.[h|c]"), directory.rglob("./test/*.[h|c]"))
    )
    _save_pickle(directory / ".build/cache.pckl", (*files, config_file))

    if file_m_times.get(config_file, 0) < config_file.stat().st_mtime:
        return set(files)

    cache = {file for file in files if file_m_times.get(file, 0) < file.stat().st_mtime}

    included_files = _build_dependency_dict(files, include_dir)
    cache.update(filter(lambda f: _has_changed_dep(f, included_files, cache), files))

    return cache
