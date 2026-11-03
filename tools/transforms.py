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
    "humanize",
    "fix_grammar",
    "paraphrase",
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

# Humanize: phrases that make text sound stiff or machine-written. Keys are lowercase with
# straight apostrophes; they match any capitalisation and either apostrophe.
FILLER_PHRASES = (
    "it is important to note that",
    "it's important to note that",
    "it is worth noting that",
    "it's worth noting that",
    "it should be noted that",
    "needless to say,",
    "in today's fast-paced world,",
    "in today's digital age,",
    # More from the MIT-licensed list at github.com/harshaneel/humanize (c) 2026 Harshaneel Gokhale.
    "it is worth mentioning that",
    "it's worth mentioning that",
    "generally speaking,",
    "it goes without saying that",
    "it can be argued that",
    "as previously mentioned,",
)
PLAIN_WORDS = {
    "furthermore,": "also,",
    "moreover,": "also,",
    "additionally,": "also,",
    "in conclusion,": "overall,",
    "in summary,": "overall,",
    "to summarize,": "overall,",
    "therefore,": "so,",
    "thus,": "so,",
    "hence,": "so,",
    "delve into": "look into",
    "delves into": "looks into",
    "delving into": "looking into",
    "delved into": "looked into",
    "in order to": "to",
    "due to the fact that": "because",
    "at this point in time": "now",
    "in the event that": "if",
    "with regard to": "about",
    "with regards to": "about",
    "prior to": "before",
    "in the realm of": "in",
    "a myriad of": "lots of",
    "a plethora of": "plenty of",
    "a wide range of": "lots of",
    "a rich tapestry of": "a mix of",
    "is a testament to": "shows",
    "plays a crucial role in": "is key to",
    "play a crucial role in": "are key to",
    "plays a pivotal role in": "is key to",
    "play a pivotal role in": "are key to",
    "navigate the complexities of": "deal with",
    "navigating the complexities of": "dealing with",
    "utilize": "use",
    "utilizes": "uses",
    "utilized": "used",
    "utilizing": "using",
    "utilise": "use",
    "utilises": "uses",
    "utilised": "used",
    "utilising": "using",
    "leveraging": "using",
    "facilitate": "help",
    "facilitates": "helps",
    "commence": "start",
    "commences": "starts",
    "commenced": "started",
    "ensure": "make sure",
    "ensures": "makes sure",
    "ensuring": "making sure",
    "ensured": "made sure",
    "numerous": "many",
    "individuals": "people",
    "subsequently": "later",
    "seamless": "smooth",
    "seamlessly": "smoothly",
    "robust": "strong",
    "comprehensive": "thorough",
    # More from the MIT-licensed list at github.com/harshaneel/humanize (c) 2026 Harshaneel Gokhale.
    "make an assumption": "assume",
    "has the capacity to": "can",
    "have the capacity to": "can",
    "with respect to": "about",
    "subsequent to": "after",
    "in light of the fact that": "since",
    "stands as a testament to": "shows",
    "serves as a testament to": "shows",
    "plays a vital role in": "is key to",
    "play a vital role in": "are key to",
    "nestled in the heart of": "in",
    "in the heart of": "in",
    "renowned for": "known for",
    "deeply rooted in": "rooted in",
    "let's dive into": "let's look at",
    "delve": "dig",
    "delves": "digs",
    "delving": "digging",
    "delved": "dug",
    "streamline": "simplify",
    "streamlines": "simplifies",
    "streamlined": "simplified",
    "garner": "get",
    "garnered": "got",
    "multifaceted": "complex",
    "intricate": "complex",
    "showcases": "shows",
    "showcasing": "showing",
    "underscores": "shows",
    "pivotal": "key",
    "vibrant": "lively",
    "breathtaking": "amazing",
    "groundbreaking": "new",
}
# Only contracted before another word, so "I know what it is." stays correct.
CONTRACTIONS = {
    "do not": "don't",
    "does not": "doesn't",
    "did not": "didn't",
    "is not": "isn't",
    "are not": "aren't",
    "was not": "wasn't",
    "were not": "weren't",
    "has not": "hasn't",
    "have not": "haven't",
    "will not": "won't",
    "would not": "wouldn't",
    "should not": "shouldn't",
    "could not": "couldn't",
    "cannot": "can't",
    "it is": "it's",
    "that is": "that's",
    "there is": "there's",
    "what is": "what's",
    "i am": "I'm",
    "you are": "you're",
    "we are": "we're",
    "they are": "they're",
    "i will": "I'll",
    "you will": "you'll",
    "we will": "we'll",
    "they will": "they'll",
}
# Humanize ends with the slips people make when typing fast, very common in South Asian
# English. They run after the contractions, so "you are good" ends up as "your good".
SLIPS = {
    "you're": "your",
    "it's": "its",
    "they're": "their",
    "than": "then",
    "lose": "loose",
    "loses": "looses",
    "losing": "loosing",
    "a lot": "alot",
    "in front": "infront",
    "at least": "atleast",
    "in case": "incase",
    "as well": "aswell",
    "each other": "eachother",
    "every time": "everytime",
    "cope with": "cope up with",
    "don't": "dont",
    "doesn't": "doesnt",
    "didn't": "didnt",
    "can't": "cant",
    "won't": "wont",
    "isn't": "isnt",
    "aren't": "arent",
    "wasn't": "wasnt",
    "weren't": "werent",
    "haven't": "havent",
    "hasn't": "hasnt",
    "wouldn't": "wouldnt",
    "shouldn't": "shouldnt",
    "couldn't": "couldnt",
}
# Only before another word (that isn't already "about"): "discuss it" → "discuss about it".
SLIPS_BEFORE_WORD = {
    "discuss": "discuss about",
    "discussed": "discussed about",
    "discussing": "discussing about",
}

# Paraphrase: hand-checked rewrites that keep the meaning in any sentence. Whole phrases
# where possible; single words only when they have one clear sense.
PARAPHRASES = {
    "is able to": "can",
    "are able to": "can",
    "was able to": "could",
    "were able to": "could",
    "you're able to": "you can",
    "we're able to": "we can",
    "they're able to": "they can",
    "i'm able to": "I can",
    "has the ability to": "can",
    "have the ability to": "can",
    "a large number of": "many",
    "a great deal of": "much",
    "a small number of": "a few",
    "the majority of": "most",
    "a number of": "several",
    "each and every": "every",
    "first and foremost": "first",
    "despite the fact that": "although",
    "in spite of the fact that": "although",
    "for the purpose of": "for",
    "with the exception of": "except",
    "in close proximity to": "near",
    "in the near future": "soon",
    "at the present time": "now",
    "at the moment": "right now",
    "on a daily basis": "daily",
    "on a regular basis": "regularly",
    "as soon as possible": "right away",
    "at the end of the day": "in the end",
    "in addition to": "besides",
    "as a result of": "because of",
    "as a result,": "because of this,",
    "in light of": "given",
    "in other words,": "put simply,",
    "for example,": "for instance,",
    "in fact,": "actually,",
    "on the other hand,": "then again,",
    "it seems that": "it looks like",
    "it is possible that": "maybe",
    "is in need of": "needs",
    "are in need of": "need",
    "make a decision": "decide",
    "makes a decision": "decides",
    "made a decision": "decided",
    "making a decision": "deciding",
    "come to the conclusion": "conclude",
    "came to the conclusion": "concluded",
    "take into account": "consider",
    "takes into account": "considers",
    "took into account": "considered",
    "give consideration to": "consider",
    "have a tendency to": "tend to",
    "has a tendency to": "tends to",
    "make an effort to": "try to",
    "makes an effort to": "tries to",
    "made an effort to": "tried to",
    "in an effort to": "to",
    "a lot of": "plenty of",
    "very big": "huge",
    "very small": "tiny",
    "very good": "excellent",
    "very bad": "terrible",
    "very happy": "delighted",
    "very tired": "exhausted",
    "very difficult": "tough",
    "very easy": "simple",
    "very important": "essential",
    "very quickly": "rapidly",
    "very hungry": "starving",
    "very cold": "freezing",
    "very angry": "furious",
    "very scared": "terrified",
    "very surprised": "amazed",
    "purchase": "buy",
    "purchased": "bought",
    "purchasing": "buying",
    "assist": "help",
    "assists": "helps",
    "assisted": "helped",
    "assistance": "help",
    "obtain": "get",
    "obtains": "gets",
    "obtained": "got",
    "sufficient": "enough",
    "approximately": "about",
    "demonstrate": "show",
    "demonstrates": "shows",
    "demonstrated": "showed",
    "additional": "extra",
    "frequently": "often",
    "occasionally": "sometimes",
    "immediately": "right away",
    "inquire": "ask",
    "inquired": "asked",
    "regarding": "about",
    "possess": "have",
    "possesses": "has",
    "terminate": "end",
    "terminated": "ended",
    "modify": "change",
    "modifies": "changes",
    "modified": "changed",
    "visualize": "picture",
    "residence": "home",
}

# Fix grammar undoes those slips, and a few more.
COMPARATIVES = (
    "more", "less", "rather", "other", "fewer", "better", "worse", "greater", "larger", "bigger",
    "smaller", "higher", "lower", "faster", "slower", "longer", "shorter", "older", "younger",
    "easier", "harder", "cheaper", "stronger", "earlier", "later",
)  # fmt: skip
GRAMMAR_FIXES = {
    "dont": "don't",
    "doesnt": "doesn't",
    "didnt": "didn't",
    "cant": "can't",
    "wont": "won't",
    "isnt": "isn't",
    "arent": "aren't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "havent": "haven't",
    "hasnt": "hasn't",
    "wouldnt": "wouldn't",
    "shouldnt": "shouldn't",
    "couldnt": "couldn't",
    "im": "I'm",
    "ive": "I've",
    "youre": "you're",
    "theyre": "they're",
    "thats": "that's",
    "whats": "what's",
    "alot": "a lot",
    "infront": "in front",
    "atleast": "at least",
    "incase": "in case",
    "aswell": "as well",
    "eachother": "each other",
    "everytime": "every time",
    "loosing": "losing",
    "looses": "loses",
    "dont loose": "don't lose",
    "don't loose": "don't lose",
    "loose weight": "lose weight",
    "to loose": "to lose",
    "will loose": "will lose",
    "not loose": "not lose",
    "never loose": "never lose",
    "can loose": "can lose",
    "could loose": "could lose",
    "might loose": "might lose",
    "could of": "could have",
    "would of": "would have",
    "should of": "should have",
    "must of": "must have",
    "might of": "might have",
    "your's": "yours",
    "their's": "theirs",
    "it's own": "its own",
    "informations": "information",
    "advices": "advice",
    "furnitures": "furniture",
    "equipments": "equipment",
    "luggages": "luggage",
    "baggages": "baggage",
    "softwares": "software",
    "feedbacks": "feedback",
    "stuffs": "stuff",
    "discuss about": "discuss",
    "discussed about": "discussed",
    "discussing about": "discussing",
    "mention about": "mention",
    "cope up with": "cope with",
    "return back": "return",
    "reply back": "reply",
    "revert back": "reply",
    "explain me": "explain to me",
    **{f"{word} then": f"{word} than" for word in COMPARATIVES},
}
# "your", "its" and "their" are right in "your car" but wrong in "your welcome", so these
# change only before words that can't follow a possessive...
SUBJECT_NEXT = (
    "a", "an", "the", "not", "so", "too", "really", "just", "always", "never", "still", "also",
    "being", "going", "gonna", "doing", "getting", "making", "trying", "looking", "coming",
    "here", "there", "my", "such", "absolutely", "probably", "definitely", "actually",
)  # fmt: skip
# ...or before an adjective that ends the clause: "your good." but not "your good name".
PREDICATES = (
    "good", "great", "fine", "okay", "ok", "sure", "right", "wrong", "welcome", "late", "early",
    "beautiful", "amazing", "awesome", "smart", "crazy", "lucky", "done", "ready", "sorry",
    "correct", "free", "busy", "kind", "funny", "cute", "safe", "true", "over", "easy", "hard",
    "important", "possible", "clear",
)  # fmt: skip
# "your welcome to join" needs fixing, "your right to vote" doesn't, so only these before "to".
PREDICATES_BEFORE_TO = ("welcome", "ready", "free", "sure", "able", "happy", "lucky", "kind")
CONTEXT_FIXES = {
    "your": ("you're", ()),
    "its": ("it's", ("been", "raining", "time", "better", "worse")),
    "their": ("they're", ()),
}
_CLAUSE_END = (
    rf"[ \t]*(?:[.,!?;:)\n]|(?![\s\S]))|[ \t]+(?:at|with|for|now|too|enough|already|though)(?!{_LETTER})"
)
# "since 2 years" (South Asian) and "for 2 years" (standard).
_DURATION = (
    r"[ \t]+(?:[0-9]+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|many|several)"
    rf"[ \t]+(?:year|month|week|day|hour)s?(?!{_LETTER})"
)
_PHRASE_SPACE = re.compile(r"[ \t]+")
_EM_DASH = re.compile(r"(?<=[^ \t\n])[ \t]*\u2014[ \t]*(?=[^ \t\n])")


def _phrases(phrases, tail: str = "") -> re.Pattern:
    """One case-insensitive pattern for whole phrases, longest first, any apostrophe and spacing."""

    def pattern(phrase: str) -> str:
        return "[ \t]+".join(re.escape(word).replace("'", "['\u2019]") for word in phrase.split(" "))

    body = "|".join(pattern(p) for p in sorted(phrases, key=len, reverse=True))
    return re.compile(f"(?<!{_LETTER})(?:{body})(?!{_LETTER}){tail}", re.IGNORECASE)


_FILLER = _phrases(FILLER_PHRASES, "[ \t]+(.?)")
_PLAIN = _phrases(PLAIN_WORDS)
_CONTRACTIBLE = _phrases(CONTRACTIONS, f"(?=[ \t]+{_LETTER})")
_SLIPS = _phrases(SLIPS)
_SLIPS_BEFORE_WORD = _phrases(SLIPS_BEFORE_WORD, f"(?=[ \t]+(?!about(?!{_LETTER})){_LETTER})")
_FOR_DURATION = re.compile(f"(?<!{_LETTER})for(?={_DURATION})", re.IGNORECASE)
_PARAPHRASES = _phrases(PARAPHRASES)
_GRAMMAR_FIXES = _phrases(GRAMMAR_FIXES)
_SINCE_DURATION = re.compile(f"(?<!{_LETTER})since(?={_DURATION})", re.IGNORECASE)


def _context(word: str, extra_next: tuple[str, ...]) -> str:
    nexts = "|".join(SUBJECT_NEXT + extra_next)
    predicates = "|".join(PREDICATES)
    before_to = "|".join(PREDICATES_BEFORE_TO)
    return (
        f"{word}(?=[ \t]+(?:(?:{nexts})(?!{_LETTER})|(?:{predicates})(?:{_CLAUSE_END})"
        f"|(?:{before_to})[ \t]+to(?!{_LETTER})))"
    )


_CONTEXT_FIXES = re.compile(
    f"(?<!{_LETTER})(?:{'|'.join(_context(w, extra) for w, (_, extra) in CONTEXT_FIXES.items())})",
    re.IGNORECASE,
)


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


def _phrase_key(match: str) -> str:
    return _PHRASE_SPACE.sub(" ", match.lower()).replace("’", "'")


def _match_case(source: str, replacement: str) -> str:
    """Give the replacement the capitals of the text it replaces: Utilize → Use, DO NOT → DON'T."""
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _drop_filler(match: re.Match) -> str:
    # The next sentence now starts where the filler did, so it takes over its capital.
    return match.group(1).upper() if match.group(0)[:1].isupper() else match.group(1)


def _apostrophe(text: str) -> str:
    """Write new apostrophes the way the text already does."""
    return "’" if "’" in text and "'" not in text else "'"


def _swap(pattern: re.Pattern, table: dict[str, str], text: str, apostrophe: str = "'") -> str:
    def replace(match: re.Match) -> str:
        return _match_case(match.group(0), table[_phrase_key(match.group(0))]).replace("'", apostrophe)

    return pattern.sub(replace, text)


def humanize(text: str) -> str:
    """Make text read like a person typed it: plain words, contractions, everyday slips."""
    apostrophe = _apostrophe(text)
    text = _FILLER.sub(_drop_filler, text)
    text = _swap(_PLAIN, PLAIN_WORDS, text)
    text = _swap(_CONTRACTIBLE, CONTRACTIONS, text, apostrophe)
    text = _EM_DASH.sub(", ", text)
    text = _swap(_SLIPS, SLIPS, text)
    text = _swap(_SLIPS_BEFORE_WORD, SLIPS_BEFORE_WORD, text)
    return _FOR_DURATION.sub(lambda m: _match_case(m.group(0), "since"), text)


def paraphrase(text: str) -> str:
    """Reword with hand-checked phrase rewrites: "is able to" → "can", "very tired" → "exhausted"."""
    return _swap(_PARAPHRASES, PARAPHRASES, text)


def fix_grammar(text: str) -> str:
    """Fix common slips: your good → you're good, dont → don't, better then → better than."""
    apostrophe = _apostrophe(text)
    text = _swap(_GRAMMAR_FIXES, GRAMMAR_FIXES, text, apostrophe)
    fixes = {word: replacement for word, (replacement, _) in CONTEXT_FIXES.items()}
    text = _swap(_CONTEXT_FIXES, fixes, text, apostrophe)
    text = _SINCE_DURATION.sub(lambda m: _match_case(m.group(0), "for"), text)
    return _PRONOUN_I.sub("I", text)


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
    if "fix_grammar" in flags:
        text = fix_grammar(text)
    if "paraphrase" in flags:
        text = paraphrase(text)
    if "humanize" in flags:
        text = humanize(text)
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
