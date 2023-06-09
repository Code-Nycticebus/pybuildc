from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from returns.context import RequiresContext
from returns.pipeline import flow
from returns.pointfree import bind
from returns.curry import partial


@dataclass()
class CompileCommand:
    """The Return value type of the compile function"""

    output_path: Path
    command: tuple[str, ...]


RELEASE_WARNINGS = ("-Wall", "-Wpedantic")

DEBUG_WARNINGS = (
    "-Wall",
    "-Wextra",
    "-Werror",
    "-Wpedantic",
    "-Wshadow",
    "-Wnull-dereference",
    "-Wformat=2",
)

# TODO some way to disable sanitizer
DEBUG_FLAGS = (
    "-ggdb",
    "-fsanitize=address,undefined,leak",
    "-fno-omit-frame-pointer",
    "-fPIC",
)

RELEASE_FLAGS = ("-O2",)


class _CompilerConfig(Protocol):
    name: str

    cc: str
    cflags: Iterable[str]
    include_flags: Iterable[str]
    library_flags: Iterable[str]
    warnings: bool

    build: Path
    src: Path
    tests: Path


def _create_path(*args):
    """Create path and mkdir's the parents to make sure the directory is valid."""
    p = Path(*args)
    p.parent.mkdir(exist_ok=True, parents=True)
    return p


def _create_obj_file_path(file: Path) -> RequiresContext[Path, _CompilerConfig]:
    return RequiresContext(
        lambda config: _create_path(
            config.build, "obj", file.relative_to(config.src).with_suffix(".o")
        )
    )


def compile(
    obj_files, output_path, obj=False
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    return RequiresContext(
        lambda context: CompileCommand(
            output_path=output_path,
            command=(
                context.cc,
                *context.include_flags,
                *(DEBUG_WARNINGS if context.warnings else ()),
                *context.cflags,
                *map(str, obj_files),
                "-o",
                str(output_path),
                *(("-c",) if obj else context.library_flags),
            ),
        )
    )


def link_exe(
    obj_files: Iterable[Path],
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    """Links all obj files to a exe usin the cc"""

    def _inner_link_exe(context):
        return compile(obj_files, _create_path(context.build, "bin", context.name))

    return RequiresContext[CompileCommand, _CompilerConfig].ask().bind(_inner_link_exe)


def link_lib(
    obj_files: Iterable[Path],
) -> RequiresContext[CompileCommand, _CompilerConfig]:
    """Links all obj files to a static library using ar"""

    def _inner_link_lib(context: _CompilerConfig):
        output_path = _create_path(context.build, "bin", context.name).with_suffix(".a")
        return CompileCommand(
            output_path=output_path,
            command=(
                "ar",
                "rcs",
                str(output_path),
                *map(str, obj_files),
            ),
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
    obj_files: Iterable[Path],
) -> RequiresContext[tuple[CompileCommand, ...], _CompilerConfig]:
    """Compiles test files. It takes the obj_files that need to be included and returns the commands to compile all tests."""

    def _inner_compile_all_test_files(context: _CompilerConfig):
        return tuple(
            map(
                lambda test_file: compile(
                    (test_file, *obj_files),
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
