
import sys
from args import parse_args

from commands import build_command

def main() -> int:
    args = parse_args(sys.argv[1:])
    match args.action:
        case 'build':
            build_command(args)
        case _: pass
    return 69

# Is run in development only
if __name__ == "__main__":
     exit(main())
