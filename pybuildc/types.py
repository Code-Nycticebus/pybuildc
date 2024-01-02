from typing import Literal

Mode = Literal["debug"] | Literal["release"]
Action = Literal["build"] | Literal["test"] | Literal["run"] | Literal["command"]
Bin = Literal["exe"] | Literal["static"]


Cmd = tuple[str, ...]
