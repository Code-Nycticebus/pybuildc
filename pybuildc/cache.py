from collections import defaultdict
import pickle
from pathlib import Path

from pybuildc.types import Action
from pybuildc.files import Files

DepTree = dict[Path, list[Path]]


class Cache:
    def __init__(self, files: Files, filename: Path, include_dirs: tuple[Path, ...]):
        self.filename = filename
        self.cache: set[Path] = set()
        self.deps = self.dependency_tree(files, include_dirs)
        self.file_m_times = (
            pickle.loads(filename.read_bytes()) if filename.exists() else dict()
        )

        self.cache.update(
            {
                f
                for f in files.all_files
                if self.file_m_times.get(f, 0) < f.stat().st_mtime
                or any(
                    (
                        self.file_m_times.get(include, 0) < include.stat().st_mtime
                        for include in self.deps[f]
                    )
                )
            }
        )

    def __contains__(self, key) -> bool:
        return key in self.cache

    def save(self):
        file_m_times = {}
        for file, files in self.deps.items():
            file_m_times[file] = file.stat().st_mtime
            file_m_times.update({f: f.stat().st_mtime for f in files})
        self.filename.write_bytes(pickle.dumps(file_m_times))

    def _get_dep_of_file(
        self, file: Path, include_dirs: tuple[Path, ...]
    ) -> list[Path]:
        l = list()
        with file.open(encoding="utf-8") as f:
            for line in f.readlines():
                if line.startswith("#include") and line.count('"') == 2:
                    idx = line.index('"') + 1
                    include = line[idx : line.index('"', idx)]
                    for includes in (*include_dirs, file.parent):
                        include_file = includes / include
                        if include_file.exists():
                            l.append(include_file)
                            l.extend(self._get_dep_of_file(include_file, include_dirs))
                            break
                    else:
                        self.cache.add(file)
        return l

    def dependency_tree(self, files: Files, include_dirs: tuple[Path, ...]) -> DepTree:
        deps: DepTree = defaultdict(list)
        for file in files.all_files:
            deps[file] = self._get_dep_of_file(file, include_dirs)
        return deps


def cache_load(files: Files, include_dirs: tuple[Path, ...], action: Action) -> Cache:
    return Cache(files, files.build / f"{action}.pck", include_dirs)
