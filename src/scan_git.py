from typing import Callable
from pathlib import Path

import pygit2 as git


def rank_objects(
    repo: git.Repository,
    oid: git.Oid,
    depth_limit: int,
    top: int,
    path_filter: Callable[[Path], bool] | None = None,
    path_map: Callable[[Path], str | None] | None = None,
    b: float = 0.0,
) -> list[tuple[str, float]]:
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
                # Apply the filter to the most recent object name.
                if path_filter is None or path_filter(Path(name)):
                    if name not in deleted:
                        if patch.delta.status in bonus_delta_status:
                            key = path_map(Path(name)) if path_map else name
                            if key:
                                scores[key] = scores.get(key, 0.0) + bonus
                        elif patch.delta.status == git.GIT_DELTA_DELETED:
                            deleted.add(patch.delta.old_file.path)

            # Count only the analyzed commits.
            depth += 1

    chart = sorted(scores.items(), key=lambda entry: entry[1], reverse=True)[:top]

    return chart
