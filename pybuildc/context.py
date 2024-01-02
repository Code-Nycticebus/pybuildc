from dataclasses import dataclass
from contextlib import contextmanager


from pybuildc.args import ArgsConfig
from pybuildc.cache import Cache, cache_load
from pybuildc.config import Config, config_load
from pybuildc.files import Files, files_load
from pybuildc.dependency import Dependency, dependencies_load


@dataclass
class Context:
    config: Config
    files: Files
    dependencies: list[Dependency]
    cache: Cache
    args: ArgsConfig


@contextmanager
def context_load(
    args: ArgsConfig,
):
    config = config_load(args.dir / "pybuildc.toml")
    files = files_load(args.dir, args.mode, build=args.build_dir)
    dependencies = dependencies_load(files, config.get("deps", {}))
    cache = cache_load(
        files,
        sum((d.include for d in dependencies), (args.dir / "src",)),
        args.action,
    )

    context = Context(
        config=config,
        files=files,
        dependencies=dependencies,
        cache=cache,
        args=args,
    )
    yield context
    context.cache.save()
