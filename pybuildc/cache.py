from collections import defaultdict
import pickle
from pathlib import Path

from pybuildc.types import Action
from pybuildc.files import Files


DepTree = dict[Path, list[Path]]


def _get_dep_of_file(file: Path, include_dirs: tuple[Path, ...]) -> list[Path]:
    l = list()
    with file.open(encoding="utf-8") as f:
        for line in f.readlines():
            if line.startswith("#include") and line.count('"') == 2:
                idx = line.index('"') + 1
                include = line[idx : line.index('"', idx)]
                for includes in include_dirs:
                    idir = includes / include
                    if idir.exists():
                        l.append(idir)
                        l.extend(_get_dep_of_file(idir, include_dirs))
    return l


def dependency_tree(files: Files, include_dirs: tuple[Path, ...]) -> DepTree:
    deps: DepTree = defaultdict(list)

    for file in files.all_files:
        deps[file] = _get_dep_of_file(file, include_dirs)

    return deps


class Cache:
    def __init__(self, files: Files, filename: Path, deps: DepTree):
        self.filename = filename
        self.deps = deps
        try:
            self.file_m_times = pickle.loads(filename.read_bytes())
        except FileNotFoundError:
            self.file_m_times = {}

        self.cache = {
            f
            for f in files.all_files
            if self.file_m_times.get(f, 0) < f.stat().st_mtime
            or any(
                map(lambda i: self.file_m_times.get(i, 0) < i.stat().st_mtime, deps[f])
            )
        }

    def __contains__(self, key) -> bool:
        return key in self.cache

    def save(self):
        file_m_times = {}
        for file, files in self.deps.items():
            file_m_times[file] = file.stat().st_mtime
            for f in files:
                file_m_times[f] = f.stat().st_mtime
        self.filename.write_bytes(pickle.dumps(file_m_times))


def cache_load(files: Files, include_dirs: tuple[Path, ...], action: Action) -> Cache:
    deps = dependency_tree(files, include_dirs)
    return Cache(files, files.build / f"{action}.pck", deps)
