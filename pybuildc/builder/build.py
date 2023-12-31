from pybuildc.config import ConfigFile


def build(config: ConfigFile, cflags: list[str]):
    print(config.name)
    print(config.compiling_files)
    print(config.files)
