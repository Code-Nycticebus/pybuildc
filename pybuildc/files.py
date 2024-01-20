from dataclasses import dataclass
from pathlib import Path
import itertools

from pybuildc.types import Mode


@dataclass
class Files:
    project: Path
    bin: Path
    build: Path
    src: Path
    test: Path

    src_files: tuple[Path, ...]
    bin_files: tuple[Path, ...]
    test_files: tuple[Path, ...]
    all_files: tuple[Path, ...]

    def ensure(self):
        self.build.mkdir(parents=True, exist_ok=True)
        (self.build / ".gitignore").write_text("*")
        self.bin.mkdir(exist_ok=True)
        for file in self.src_files:
            (self.build / "obj" / file.relative_to(self.src)).parent.mkdir(
                parents=True, exist_ok=True
            )
        for file in self.bin_files:
            (self.bin / file.relative_to(self.src / "bin")).parent.mkdir(
                parents=True, exist_ok=True
            )
        for file in self.test_files:
            (self.build / "tests" / file.relative_to(self.test)).parent.mkdir(
                parents=True, exist_ok=True
            )
        return self


def files_load(dir: Path, mode: Mode, build: Path | None = None):
    build = build if build else dir / ".build" / mode
    return Files(
        project=dir,
        bin=build / "bin",
        build=build,
        src=dir / "src",
        test=dir / "tests",
        src_files=tuple(f for f in (dir / "src").rglob("*.c") if "bin" not in f.parts),
        bin_files=tuple((dir / "src" / "bin").rglob("*.c")),
        test_files=tuple((dir / "tests").rglob("*-test.c")),
        all_files=tuple(
            itertools.chain(
                (dir / "tests").rglob("*.[c|h]"), (dir / "src").rglob("*.c")
            )
        ),
    ).ensure()
