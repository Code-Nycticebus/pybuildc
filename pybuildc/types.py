from typing import Literal

Mode = Literal["debug"] | Literal["release"]
Action = Literal["build"] | Literal["test"] | Literal["run"]
Bin = Literal["exe"] | Literal["static"]


Cmd = tuple[str, ...]
