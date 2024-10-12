from pathlib import Path
from typing import Callable

import pygit2 as git

from parse_args import parse_args
from scan_git import rank_objects
from assist import Assist


def main():
    args = parse_args()
    kb_dir = args.kb_dir or Path.cwd()
    print(f"args: {args}")

    path_filter = make_kb_filter(args.include, args.exclude)

    # If `kb_dir` is not a Git repo, fails with
    # _pygit2.GitError: Repository not found at <path>
    repo = git.Repository(kb_dir)
    # obj = repo.revparse_single("HEAD")
    obj = repo.get(repo.head.target)
    assert isinstance(obj, git.Commit)

    chart = rank_objects(
        repo,
        obj.id,
        depth_limit=args.depth,
        top=args.top,
        path_filter=path_filter,
        b=args.b,
    )

    print("Recently changed files:")
    for name, score in chart:
        print(f"{name} ({score:.3f})")

    assist = Assist()
    for name, _ in chart:
        print(f"\n- {name}")
        assist.ponder(Path(repo.workdir).joinpath(name))


def make_kb_filter(
    include: list[str] | None, exclude: list[str] | None
) -> Callable[[Path], bool]:
    def kb_filter(f: Path) -> bool:
        return not f.name.startswith(".") and (
            f.is_dir()
            or (include is None or any(map(f.name.endswith, include)))
            and (exclude is None or not any(map(f.name.endswith, exclude)))
        )

    return kb_filter


if __name__ == "__main__":
    main()
