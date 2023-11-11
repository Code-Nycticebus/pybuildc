from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol, Sequence
import platform

from returns.context import RequiresContext
from returns.pipeline import flow
from returns.pointfree import bind
from returns.curry import partial


@dataclass()
class CompileCommand:
    """The Return value type of the compile function"""

    input_files: tuple[Path, ...]
    output_path: Path
    command: tuple[str, ...]


RELEASE_FLAGS = (
    "-Wall",
    "-Wpedantic",
    "-O2",
    "-DNDEBUG",
)

DEBUG_FLAGS = (
    "-g",
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wpedantic",
    "-Wshadow",
    "-Wnull-dereference",
    "-Wformat=2",
)


class _CompilerConfig(Protocol):
    name: str

    release: bool

    cc: str
    cflags: Iterable[str]
    include_flags: Iterable[Path]
    library_flags: Iterable[tuple[Path, str]]

    project: Path
    build: Path
    src: Path
    tests: Path


def _create_path(*args):
    """Create path and mkdir's the parents to make sure the directory is valid."""
    p = Path(*args)
    if not any("$" in str(path) for path in args):
        p.parent.mkdir(exist_ok=True, parents=True)
    return p


def _create_obj_file_path(file: Path) -> RequiresContext[Path, _CompilerConfig]:
    return RequiresContext(
        lambda config: _create_path(
            config.build,
            "obj",
            file.relative_to(config.src).with_suffix(".o").name,
        )
    )


def compile(
    obj_files, output_path, obj=False, shared=False
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    return RequiresContext(
        lambda context: CompileCommand(
            input_files=obj_files,
            output_path=output_path,
            command=(
                context.cc,
                *map(
                    lambda f: f"-I{f}",
                    context.include_flags,
                ),
                *(RELEASE_FLAGS if context.release else DEBUG_FLAGS),
                *context.cflags,
                *map(lambda f: str(f.relative_to(context.project)), obj_files),
                "-o",
                str(output_path),
                *(
                    ("-c",)
                    if obj
                    else (
                        element
                        for f in tuple(
                            map(
                                lambda f: (
                                    f"-L{f[0]}",
                                    f"-l{f[1]}",
                                )
                                if f[0]
                                else (f"-l{f[1]}",),
                                context.library_flags,
                            )
                        )
                        for element in f
                    )
                ),
                *(("--shared",) if shared else ()),
            ),
        )
    )


def link_exe(
    obj_files: Iterable[Path],
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    """Links all obj files to a exe usin the cc"""

    def _inner_link_exe(context):
        bin_path = _create_path(context.build, "bin", context.name).with_suffix(
            ".exe" if platform.system() == "Windows" else ""
        )
        return compile(obj_files, bin_path)

    return RequiresContext[CompileCommand, _CompilerConfig].ask().bind(_inner_link_exe)


def link_shared(
    obj_files: Iterable[Path],
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    """Links all obj files to a exe usin the cc"""

    def _inner_link_exe(context):
        bin_path = _create_path(
            context.build,
            "bin",
            f"lib{context.name}.so"
            if platform.system() == "Linux"
            else f"{context.name}.dll",
        )
        return compile(
            obj_files,
            bin_path,
            shared=True,
        )

    return RequiresContext[CompileCommand, _CompilerConfig].ask().bind(_inner_link_exe)


def link_static(
    obj_files: tuple[Path, ...],
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    """Links all obj files to a static library using ar"""

    def _inner_link_lib(context: _CompilerConfig):
        output_path = _create_path(
            context.build,
            "bin",
            f"lib{context.name}.a"
            if platform.system() == "Linux"
            else f"{context.name}.lib",
        )
        return CompileCommand(
            input_files=obj_files,
            output_path=output_path,
            command=(
                "ar",
                "rcs",
                str(output_path),
                *map(str, obj_files),
            )
            if platform.system().lower() == "linux"
            else ("lib", f"/OUT:{output_path}", *map(str, obj_files)),
        )

    return RequiresContext(_inner_link_lib)


def _compile_obj_file(
    input_file: Path,
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    def _inner_compile_obj_file(_: _CompilerConfig):
        return flow(
            input_file,
            _create_obj_file_path,
            bind(partial(compile, (input_file,), obj=True)),
        )

    return (
        RequiresContext[CompileCommand, _CompilerConfig]
        .ask()
        .bind(_inner_compile_obj_file)
    )


def compile_all_obj_files(
    src_files: Iterable[Path],
) -> RequiresContext[tuple[CompileCommand, ...], _CompilerConfig]:
    """Compiles src files into '.o' files."""
    return RequiresContext(
        lambda config: tuple(
            map(lambda file: _compile_obj_file(file)(config), src_files)
        )
    )


def compile_all_test_files(
    obj_files: Path,
) -> RequiresContext[tuple[CompileCommand, ...], _CompilerConfig]:
    """Compiles test files. It takes the obj_files that need to be included and returns the commands to compile all tests."""

    def _inner_compile_all_test_files(context: _CompilerConfig):
        return tuple(
            map(
                lambda test_file: compile(
                    (test_file, obj_files),
                    _create_path(
                        context.build, "tests", test_file.relative_to(context.tests)
                    ).with_suffix(""),
                )(context),
                sorted(
                    context.tests.rglob("*-test.c"),
                    key=lambda file: file.stat().st_mtime,
                ),
            )
        )

    return RequiresContext(_inner_compile_all_test_files)
