from argparse import ArgumentParser
from pathlib import Path
from typing import Callable, Iterable

import pygit2 as git


def main():
    args = parse_args()
    kb_dir = args.kb_dir or Path.cwd()
    print(f"args: {args}")

    path_filter = make_kb_filter(args.suffix)

    # for f in scan_kb(kb_dir, kb_filter):

    # If `kb_dir` is not a Git repo, fails with
    # _pygit2.GitError: Repository not found at <path>
    repo = git.Repository(kb_dir)
    # obj = repo.revparse_single("HEAD")
    obj = repo.get(repo.head.target)
    assert isinstance(obj, git.Commit)
    # for f in walk_tree(repo, obj.tree, kb_filter):
    #     print(f"{f}")
    # scan_commits_x(repo, obj.id, kb_filter)
    rank_objects(
        repo,
        obj.id,
        depth_limit=args.depth,
        top=args.top,
        path_filter=path_filter,
        b=args.b,
    )


def parse_args():
    p = ArgumentParser()
    p.add_argument("-d", "--kb-dir", type=Path)
    p.add_argument(
        "-s",
        "--suffix",
        action="append",
        help="Filter files by name suffix (e.g. '.md', '.g.dart'). Can be used multiple times.",
    )
    p.add_argument("--depth", type=int, default=100)
    p.add_argument("--top", type=int, default=10)
    p.add_argument(
        "-b",
        type=float,
        default=0.0,
        help="Values greater than zero make the weight of older changes decline slower (the weight of a change is computed as 1/(depth + b)).",
    )
    args = p.parse_args()

    assert args.depth >= args.b, "Depth is expected to be multiple times larger than b."

    return args


def make_kb_filter(suffixes: list[str] | None) -> bool:
    def kb_filter(f: Path) -> bool:
        return not f.name.startswith(".") and (
            f.is_dir() or suffixes is None or any(map(f.name.endswith, suffixes))
        )

    return kb_filter


def scan_kb(
    kb_dir: Path, path_filter: Callable[[Path], bool] | None = None
) -> Iterable:
    dirs = [kb_dir]
    while dirs:
        d = dirs.pop(0)
        for f in d.iterdir():
            if path_filter is None or path_filter(f):
                if f.is_file():
                    yield f
                elif f.is_dir():
                    dirs.append(f)


def rank_objects(
    repo: git.Repository,
    oid: git.Oid,
    depth_limit: int,
    top: int,
    path_filter: Callable[[Path], bool] | None = None,
    b: float = 0.0,
):
    bonus_delta_status = [
        git.GIT_DELTA_ADDED,
        git.GIT_DELTA_COPIED,
        git.GIT_DELTA_MODIFIED,
        git.GIT_DELTA_RENAMED,
    ]
    assert git.GIT_DELTA_DELETED not in bonus_delta_status

    scores = dict[str, float]()
    deleted = set[str]()
    renamed = dict[str, str]()  # old -> new

    def apply_future_renames(name: str) -> str:
        while name in renamed:
            name = renamed[name]
        return name

    depth = 1
    for commit in repo.walk(oid, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_TIME):
        if depth > depth_limit:
            break

        bonus = 1 / (depth + b)

        # Ignore merge commits.
        # The root commit is also ignored, though it may be worth taking into account.
        if len(commit.parents) == 1:
            diff = commit.parents[0].tree.diff_to_tree(commit.tree)
            diff.find_similar()  # Find renames and more
            for patch in diff:
                if patch.delta.status == git.GIT_DELTA_RENAMED:
                    renamed[patch.delta.old_file.path] = patch.delta.new_file.path
                name = apply_future_renames(patch.delta.new_file.path)
                if name not in deleted:
                    if patch.delta.status in bonus_delta_status:
                        scores[name] = scores.get(name, 0.0) + bonus
                    elif patch.delta.status == git.GIT_DELTA_DELETED:
                        deleted.add(patch.delta.old_file.path)

            # Count only the analyzed commits.
            depth += 1

    chart = sorted(scores.items(), key=lambda entry: entry[1], reverse=True)
    if path_filter is not None:
        chart = [(name, score) for name, score in chart if path_filter(Path(name))]

    for name, score in chart[:top]:
        print(f"{name} ({score:.3f})")


if __name__ == "__main__":
    main()
