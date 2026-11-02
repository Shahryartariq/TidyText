"""
Text transformations.

Pure functions with no Django dependency. `static/js/transforms.js` is a line-for-line
port used for instant formatting in the browser; both are checked against the same
cases in `tools/tests/cases.json`, so the server fallback and the browser always agree.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

LINE_BREAK_MODES = ("keep", "paragraphs", "remove")
CASE_MODES = ("keep", "upper", "lower", "title", "sentence")
FLAGS = ("remove_extra_spaces", "remove_empty_lines", "remove_punctuation", "remove_invisible")

# Zero-width space/joiners, word joiner, byte-order mark, soft hyphen.
INVISIBLE_CHARS = "\u200b\u200c\u200d\u2060\ufeff\u00ad"
_INVISIBLE = re.compile(f"[{INVISIBLE_CHARS}]")
_NEWLINES = re.compile(r"\r\n|\r")
_BLANK_LINE = re.compile(r"\n[ \t\u00a0]*\n")
_HORIZONTAL_SPACE = re.compile(r"[ \t\u00a0]+")
_LETTER = r"[^\W\d_]"
_TITLE_START = re.compile(rf"""(^|[\s\-/(\[{{"“‘])({_LETTER})""")
_SENTENCE_START = re.compile(rf"""(^[\s"'“‘(]*|[.!?]["'”’)]*\s+["'“‘(]*|\n[\s"'“‘(]*)({_LETTER})""")
_PRONOUN_I = re.compile(rf"(?<!{_LETTER})i(?!{_LETTER}|\.e\.)")


@dataclass(frozen=True)
class Options:
    line_breaks: str = "keep"
    case: str = "keep"
    flags: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def build(cls, line_breaks: str = "keep", case: str = "keep", flags=()) -> Options:
        """Create options, silently ignoring unknown values (input comes from forms)."""
        return cls(
            line_breaks=line_breaks if line_breaks in LINE_BREAK_MODES else "keep",
            case=case if case in CASE_MODES else "keep",
            flags=frozenset(f for f in flags if f in FLAGS),
        )

    @property
    def is_noop(self) -> bool:
        return self.line_breaks == "keep" and self.case == "keep" and not self.flags


def normalize_newlines(text: str) -> str:
    return _NEWLINES.sub("\n", text)


def remove_invisible(text: str) -> str:
    return _INVISIBLE.sub("", text)


def remove_punctuation(text: str) -> str:
    return "".join(ch for ch in text if not unicodedata.category(ch).startswith("P"))


def _join_lines(text: str) -> str:
    return " ".join(line.strip() for line in text.split("\n") if line.strip())


def remove_line_breaks(text: str) -> str:
    """Put everything on one line, separated by single spaces."""
    return _join_lines(text)


def join_paragraph_lines(text: str) -> str:
    """Join the lines inside each paragraph; keep blank lines between paragraphs."""
    paragraphs = (_join_lines(p) for p in _BLANK_LINE.split(text))
    return "\n\n".join(p for p in paragraphs if p)


def remove_empty_lines(text: str) -> str:
    return "\n".join(line for line in text.split("\n") if line.strip())


def remove_extra_spaces(text: str) -> str:
    """Collapse runs of spaces/tabs to one space and trim each line. Keeps line breaks."""
    return "\n".join(_HORIZONTAL_SPACE.sub(" ", line).strip() for line in text.split("\n"))


def title_case(text: str) -> str:
    return _TITLE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text.lower())


def sentence_case(text: str) -> str:
    text = _SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), text.lower())
    return _PRONOUN_I.sub("I", text)


_CASES = {
    "upper": str.upper,
    "lower": str.lower,
    "title": title_case,
    "sentence": sentence_case,
}


def apply(text: str, options: Options) -> str:
    """Run the selected transformations in a fixed, predictable order."""
    text = normalize_newlines(text)
    if "remove_invisible" in options.flags:
        text = remove_invisible(text)
    if "remove_punctuation" in options.flags:
        text = remove_punctuation(text)
    if options.line_breaks == "remove":
        text = remove_line_breaks(text)
    elif options.line_breaks == "paragraphs":
        text = join_paragraph_lines(text)
    if "remove_empty_lines" in options.flags:
        text = remove_empty_lines(text)
    if "remove_extra_spaces" in options.flags:
        text = remove_extra_spaces(text)
    if options.case in _CASES:
        text = _CASES[options.case](text)
    return text


@dataclass(frozen=True)
class Stats:
    characters: int
    words: int
    lines: int


def stats(text: str) -> Stats:
    text = normalize_newlines(text)
    return Stats(
        characters=len(text),
        words=len(text.split()),
        lines=0 if text == "" else text.count("\n") + 1,
    )
