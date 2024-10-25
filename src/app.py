from pathlib import Path
import re
from typing import Callable

import pygit2 as git

from md_utils import get_tag_line_tags
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
        # path_map=dart_pkg_path,
        b=args.b,
    )

    print("Recently changed files:")
    for name, score in chart:
        print(f"{name} ({score:.3f})")

    assist = Assist()
    repo_path = Path(repo.workdir)
    for name, _ in chart:
        path = repo_path.joinpath(name)
        text = path.read_text()
        tag_line_tags = list(get_tag_line_tags(text))
        if _TAG_IGNORE in tag_line_tags:
            continue
        print(f"\n- {name}")
        if _TAG_ARTICLE in tag_line_tags:
            # assist.assess_subject_consistency(text)
            assist.assess_article_quality(text)


_TAG_PREFIX = "assist-"
_TAG_IGNORE = _TAG_PREFIX + "ignore"
_TAG_ARTICLE = _TAG_PREFIX + "article"


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


def dart_pkg_path(p: Path) -> str | None:
    """
    >>> dart_pkg_path(Path('pkgs/utils/lib/src/misc.dart'))
    'pkgs/utils'
    >>> dart_pkg_path(Path('pkgs/utils/lib/utils.dart'))
    'pkgs/utils'
    >>> dart_pkg_path(Path('pkgs/utils/pubspec.yaml'))
    'pkgs/utils'
    """

    m = _DART_PKG_RE.match(str(p))
    if m:
        return m.group(1)
    return None


_DART_PKG_RE = re.compile(r"^(.*?)/(bin|lib|test|[^/]*$)")

if __name__ == "__main__":
    main()
