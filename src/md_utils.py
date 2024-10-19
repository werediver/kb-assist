import re
from typing import Iterable


def get_tag_line_tags(text: str) -> Iterable[str]:
    """Return tags from the first tag-line in the text."""

    tag_line_match = _tag_line_re.search(text)
    if tag_line_match:
        tag_matches = _tag_re.finditer(tag_line_match.group())
        yield from map(lambda m: m.group(1), tag_matches)


def deemphasize_subject(text: str) -> str:
    """
    Remove the title (the first level one heading), any tag-lines,
    and strip heading markup.
    """

    title_re = re.compile(r"^# .+\n?")
    heading_re = re.compile(r"^#+ (.+)\n?", re.MULTILINE)

    s = title_re.sub("", text)
    s = heading_re.sub(r"\1. ", s)
    s = _tag_line_re.sub("", s)
    s = _remove_excessive_empty_lines(s)

    return s.strip()


def remove_tags(text: str) -> str:
    """
    Remove any tag-lines and strip the hash from in-line tags.
    """

    s = _tag_line_re.sub("", text)
    s = _tag_re.sub(r"\1", s)
    s = _remove_excessive_empty_lines(s)

    return s.strip()


def _remove_excessive_empty_lines(text: str) -> str:
    excessive_empty_lines_re = re.compile(r"\n{3,}")
    s = excessive_empty_lines_re.sub("\n\n", text)
    return s.strip()


_tag_line_re = re.compile(r"^(#[\w\-/]+[, ]*)+\n?\n?$", re.MULTILINE)
_tag_re = re.compile(r"#([\w\-/]+)", re.MULTILINE)
