from argparse import ArgumentParser
from pathlib import Path


def parse_args():
    p = ArgumentParser()
    p.add_argument("-d", "--kb-dir", type=Path)
    p.add_argument(
        "-i",
        "--include",
        action="append",
        help="Filter files by name suffix (e.g. '.md'). Can be used multiple times.",
    )
    p.add_argument(
        "-e",
        "--exclude",
        action="append",
        help="Filter files by name suffix (e.g. '.assist.md'). Can be used multiple times.",
    )
    p.add_argument("--depth", type=int, default=50)
    p.add_argument("--top", type=int, default=5)
    p.add_argument(
        "-b",
        type=float,
        default=0.0,
        help="Values greater than zero make the weight of older changes decline slower (the weight of a change is computed as 1/(depth + b)).",
    )
    args = p.parse_args()

    assert args.depth >= args.b, "Depth is expected to be multiple times larger than b."

    return args
