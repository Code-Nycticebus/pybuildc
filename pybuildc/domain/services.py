from dataclasses import dataclass

Cmd = list[str]

RELEASE_WARNINGS: list[str] = [
    "-Wall",
    "-Wpedantic"
]

DEBUG_WARNINGS: list[str] = [
    "-Wall",
    "-Wextra",
    "-Wpedantic",
    "-Werror",
    "-Wshadow",
    "-Wnull-dereference",
    "-Wformat=2",
    "-Wno-unused-command-line-argument",
]

# TODO some way to disable sanitizer
DEBUG_FLAGS: list[str] = [
    "-ggdb",
    "-fsanitize=address,undefined,leak",
    "-fno-omit-frame-pointer",
    "-fPIC"
]

RELEASE_FLAGS: list[str] = [
    "-O2",
]

@dataclass(frozen=True)
class Compiler:
    cc: str
    warnings: list[str]
    flags: list[str]
    libraries: list[str]

    def compile(self, files: list[str], output: str, flags: list[str], disable_warnings=False) -> Cmd:
        return [
            self.cc,
            *files,
            *(self.warnings if not disable_warnings else ()),
            *self.libraries,
            *(self.flags + flags),
            "-o",
            output,
        ]

    @classmethod
    def create(
            cls,
            cc: str,
            libraries: list[str],
            debug: bool):
        return cls(
            cc=cc,
            warnings=DEBUG_WARNINGS if debug else RELEASE_WARNINGS,
            flags=DEBUG_FLAGS if debug else RELEASE_FLAGS,
            libraries=libraries,
        )


if __name__ == "__main__":
    import subprocess

    def execute(cmd: Cmd):
        print(" ".join(cmd))
        subprocess.run(cmd)

    c = Compiler.create("gcc", ["-lm"], True)
    execute(c.compile(["src/main.c"], "src/main.o", ["-c"]))
    execute(c.compile(["src/main.o"], "main", []))
