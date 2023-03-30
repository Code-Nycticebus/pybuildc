from dataclasses import dataclass
from pathlib import Path



@dataclass(frozen=True)
class CompileCommand:
    outfile: Path
    infiles: tuple[Path, ...]
    
@dataclass(frozen=True)
class BuildFiles:
    directory: Path
    build_directory: Path
    src_files: tuple[Path, ...]
    include_files: tuple[Path, ...]

@dataclass(frozen=True)
class Dependencies:
    name: str
    version: str
    lib_flags: tuple[str]
    inc_flags: tuple[str]



@dataclass(frozen=True)
class BuildConfig:
    target: str
    project_name: str
    dependecies: Dependencies
    

