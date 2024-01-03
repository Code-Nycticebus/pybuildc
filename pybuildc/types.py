from typing import Literal

Mode = Literal["debug", "release"]
Action = Literal["build", "test", "run", "command"]
Bin = Literal["exe", "static"]


Cmd = tuple[str, ...]
