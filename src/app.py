from argparse import ArgumentParser
from pathlib import Path
from typing import Callable, Iterable, List

import pygit2 as git


def main():
    args = parse_args()
    kb_dir = args.kb_dir or Path.cwd()
    print(f"args: {args}")

    kb_filter = make_kb_filter([".md"])

    # for f in scan_kb(kb_dir, kb_filter):

    # If `kb_dir` is not a Git repo, fails with
    # _pygit2.GitError: Repository not found at <path>
    repo = git.Repository(kb_dir)
    rev = repo.revparse_single("HEAD")
    assert isinstance(rev, git.Commit)
    # for f in walk_tree(repo, rev.tree, kb_filter):
    #     print(f"{f}")
    scan_commits(repo, rev.id)


def parse_args():
    p = ArgumentParser()
    p.add_argument("-i", "--interactive", action="store_true")
    p.add_argument("-d", "--kb-dir", type=Path)
    args = p.parse_args()
    return args


def make_kb_filter(exts: List[str]) -> bool:
    def kb_filter(f: Path) -> bool:
        return not f.name.startswith(".") and (f.is_dir() or f.suffix in exts)

    return kb_filter


def scan_kb(kb_dir: Path, filter: Callable[[Path], bool] | None = None) -> Iterable:
    dirs = [kb_dir]
    while dirs:
        d = dirs.pop(0)
        for f in d.iterdir():
            if filter is None or filter(f):
                if f.is_file():
                    yield f
                elif f.is_dir():
                    dirs.append(f)


def walk_tree(
    repo: git.Repository, tree: git.Tree, filter: Callable[[Path], bool] | None = None
) -> Iterable:
    entries = [(tree, Path())]
    while entries:
        tree, path = entries.pop(0)
        for obj in tree:
            obj_path = path.joinpath(obj.name)
            if filter is None or filter(obj_path):
                if obj.type == git.GIT_OBJECT_TREE:
                    obj_tree = repo.get(obj.id)
                    entries.append((obj_tree, obj_path))
                elif obj.type == git.GIT_OBJECT_BLOB:
                    yield path.joinpath(obj.name)


def scan_commits(repo: git.Repository, oid: git.Oid):
    for commit in repo.walk(oid, git.GIT_SORT_TOPOLOGICAL | git.GIT_SORT_TIME):
        if len(commit.parents) == 1:
            print(f"\n{commit.message}")
            diff = commit.parents[0].tree.diff_to_tree(commit.tree)
            diff.find_similar()  # Find renames and more
            for patch in diff:
                if patch.delta.old_file.path != patch.delta.new_file.path:
                    print(
                        f"{patch.delta.status_char()} "
                        f"{patch.delta.old_file.path} => {patch.delta.new_file.path} ({patch.delta.similarity}%)"
                    )
                else:
                    print(f"{patch.delta.status_char()} {patch.delta.new_file.path}")


if __name__ == "__main__":
    main()
