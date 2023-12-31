from pybuildc.args import ArgsConfig
from pybuildc.config import config_load, Config


def build(args: ArgsConfig, cflags: list[str]):
    config: Config = config_load(args.directory)
    print(config)
