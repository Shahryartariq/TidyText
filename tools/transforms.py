"""
Text transformations.

Pure functions with no Django dependency. `static/js/transforms.js` is a line-for-line
port used for instant formatting in the browser; both are checked against the same
cases in `tools/tests/cases.json`, so the server fallback and the browser always agree.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

LINE_BREAK_MODES = ("keep", "paragraphs", "remove")
CASE_MODES = ("keep", "upper", "lower", "title", "sentence")
SORT_MODES = ("keep", "az", "za")
FLAGS = (
    "remove_extra_spaces",
    "remove_empty_lines",
    "remove_duplicate_lines",
    "remove_invisible",
    "fix_hyphenation",
    "straighten_quotes",
    "strip_html",
    "remove_punctuation",
)
MAX_FIND_CHARS = 1000

# Zero-width space/joiners, word joiner, byte-order mark, soft hyphen.
INVISIBLE_CHARS = "".join(map(chr, (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD)))
# One explicit whitespace set, identical in the JavaScript port, so counts always match.
WHITESPACE = " \t\n\f\v\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000"

_INVISIBLE = re.compile(f"[{INVISIBLE_CHARS}]")
_NEWLINES = re.compile(r"\r\n|\r")
_BLANK_LINE = re.compile(r"\n[ \t\u00a0]*\n")
_HORIZONTAL_SPACE = re.compile(r"[ \t\u00a0]+")
_WORD = re.compile(f"[^{WHITESPACE}]+")
_NON_SPACE = re.compile(f"[^{WHITESPACE}]")
_LETTER = r"[^\W\d_]"
_TITLE_START = re.compile(rf"""(^|[\s\-/(\[{{"“‘])({_LETTER})""")
_SENTENCE_START = re.compile(rf"""(^[\s"'“‘(]*|[.!?]["'”’)]*\s+["'“‘(]*|\n[\s"'“‘(]*)({_LETTER})""")
_PRONOUN_I = re.compile(rf"(?<!{_LETTER})i(?!{_LETTER}|\.e\.)")
_SENTENCE_END = re.compile(r"""[.!?]+(?=[\s"'”’)]|$)""")
_HYPHEN_BREAK = re.compile(rf"({_LETTER})-[ \t]*\n[ \t]*({_LETTER})")
_ESCAPES = re.compile(r"\\(n|t|\\)")
_QUOTES = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "′": "'",
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "″": '"',
        "–": "-",
        "—": "-",
        "…": "...",
    }
)
_HTML_COMMENT = re.compile(r"<!--[\s\S]*?-->")
_HTML_SCRIPT = re.compile(r"<(script|style)\b[^>]*>[\s\S]*?</\1\s*>", re.IGNORECASE)
_HTML_BREAK = re.compile(r"<br\s*/?>|</(?:p|div|li|h[1-6]|tr|blockquote|pre)\s*>", re.IGNORECASE)
_HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
_HTML_ENTITY = re.compile(r"&(#\d{1,7}|#x[0-9a-f]{1,6}|nbsp|amp|lt|gt|quot|apos);", re.IGNORECASE)
_NAMED_ENTITIES = {"nbsp": "\u00a0", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'"}


@dataclass(frozen=True)
class Options:
    line_breaks: str = "keep"
    case: str = "keep"
    flags: frozenset[str] = field(default_factory=frozenset)
    sort: str = "keep"
    find: str = ""
    replace: str = ""

    @classmethod
    def build(
        cls,
        line_breaks: str = "keep",
        case: str = "keep",
        flags=(),
        sort: str = "keep",
        find: str = "",
        replace: str = "",
    ) -> Options:
        """Create options, silently ignoring unknown values (input comes from forms)."""
        return cls(
            line_breaks=line_breaks if line_breaks in LINE_BREAK_MODES else "keep",
            case=case if case in CASE_MODES else "keep",
            flags=frozenset(f for f in flags if f in FLAGS),
            sort=sort if sort in SORT_MODES else "keep",
            find=(find or "")[:MAX_FIND_CHARS],
            replace=(replace or "")[:MAX_FIND_CHARS],
        )

    @property
    def is_noop(self) -> bool:
        return (
            self.line_breaks == "keep"
            and self.case == "keep"
            and self.sort == "keep"
            and not self.flags
            and not self.find
        )


def normalize_newlines(text: str) -> str:
    return _NEWLINES.sub("\n", text)


def unescape(value: str) -> str:
    """Let people type \\n for a new line and \\t for a tab in find and replace."""
    return _ESCAPES.sub(lambda m: {"n": "\n", "t": "\t", "\\": "\\"}[m.group(1)], value)


def find_replace(text: str, find: str, replace: str) -> str:
    """Plain-text, case-sensitive find and replace (no regular expressions)."""
    find = unescape(find)
    return text.replace(find, unescape(replace)) if find else text


def _decode_entity(match: re.Match) -> str:
    name = match.group(1).lower()
    if name in _NAMED_ENTITIES:
        return _NAMED_ENTITIES[name]
    code = int(name[2:], 16) if name.startswith("#x") else int(name[1:])
    return chr(code) if 0 < code <= 0x10FFFF and not 0xD800 <= code <= 0xDFFF else match.group(0)


def strip_html(text: str) -> str:
    """Remove HTML tags and comments, keep the text, and decode common entities."""
    text = _HTML_COMMENT.sub("", text)
    text = _HTML_SCRIPT.sub("", text)
    text = _HTML_BREAK.sub("\n", text)
    text = _HTML_TAG.sub("", text)
    return _HTML_ENTITY.sub(_decode_entity, text)


def remove_invisible(text: str) -> str:
    return _INVISIBLE.sub("", text)


def straighten_quotes(text: str) -> str:
    """Curly quotes to straight quotes, dashes to hyphens, … to three dots."""
    return text.translate(_QUOTES)


def fix_hyphenation(text: str) -> str:
    """Rejoin words split across lines with a hyphen, as PDFs do: "infor-\\nmation"."""
    return _HYPHEN_BREAK.sub(lambda m: m.group(1) + m.group(2) if m.group(2).islower() else m.group(0), text)


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


def remove_duplicate_lines(text: str) -> str:
    """Keep the first copy of each line. Blank lines are left alone."""
    seen: set[str] = set()
    kept = []
    for line in text.split("\n"):
        if line.strip():
            if line in seen:
                continue
            seen.add(line)
        kept.append(line)
    return "\n".join(kept)


def _sort_key(line: str) -> tuple[str, str, str]:
    """Alphabetical order that ignores case and accents: "apple", "Äpfel", "banana"."""
    lower = line.lower()
    plain = "".join(
        ch for ch in unicodedata.normalize("NFKD", lower) if not unicodedata.category(ch).startswith("M")
    )
    return (plain, lower, line)


def sort_lines(text: str, mode: str) -> str:
    """Sort lines alphabetically, ignoring case and accents. Blank lines move to the end."""
    lines = text.split("\n")
    filled = sorted((line for line in lines if line.strip()), key=_sort_key, reverse=mode == "za")
    blank = [line for line in lines if not line.strip()]
    return "\n".join(filled + blank)


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
    flags = options.flags
    text = normalize_newlines(text)
    text = find_replace(text, options.find, options.replace)
    if "strip_html" in flags:
        text = strip_html(text)
    if "remove_invisible" in flags:
        text = remove_invisible(text)
    if "straighten_quotes" in flags:
        text = straighten_quotes(text)
    if "fix_hyphenation" in flags:
        text = fix_hyphenation(text)
    if "remove_punctuation" in flags:
        text = remove_punctuation(text)
    if options.line_breaks == "remove":
        text = remove_line_breaks(text)
    elif options.line_breaks == "paragraphs":
        text = join_paragraph_lines(text)
    if "remove_empty_lines" in flags:
        text = remove_empty_lines(text)
    if "remove_extra_spaces" in flags:
        text = remove_extra_spaces(text)
    if "remove_duplicate_lines" in flags:
        text = remove_duplicate_lines(text)
    if options.sort != "keep":
        text = sort_lines(text, options.sort)
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
        words=len(_WORD.findall(text)),
        lines=0 if text == "" else text.count("\n") + 1,
    )


@dataclass(frozen=True)
class Details:
    characters_no_spaces: int
    sentences: int
    paragraphs: int
    reading_seconds: int
    speaking_seconds: int


WORDS_PER_MINUTE_READING = 238
WORDS_PER_MINUTE_SPEAKING = 150


def details(text: str) -> Details:
    """Extra counts for the word counter."""
    text = normalize_newlines(text)
    words = len(_WORD.findall(text))
    sentences = sum(1 for part in _SENTENCE_END.split(text) if any(ch.isalnum() for ch in part))
    paragraphs = sum(1 for part in _BLANK_LINE.split(text) if part.strip())
    return Details(
        characters_no_spaces=len(_NON_SPACE.findall(text)),
        sentences=sentences,
        paragraphs=paragraphs,
        reading_seconds=math.ceil(words * 60 / WORDS_PER_MINUTE_READING),
        speaking_seconds=math.ceil(words * 60 / WORDS_PER_MINUTE_SPEAKING),
    )
