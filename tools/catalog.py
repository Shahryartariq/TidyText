"""
The tools TidyText offers. Each tool gets its own landing page (good for search):
same editor, different preset options, title, description and help text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tools.transforms import Options


@dataclass(frozen=True)
class Tool:
    slug: str
    name: str  # short name for menus and links
    title: str  # <title>, under ~60 characters
    description: str  # meta description, under ~160 characters
    heading: str  # the page's <h1>
    intro: str
    summary: str  # one line for tool lists
    options: Options
    example: str
    faqs: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def _opts(line_breaks="keep", case="keep", *flags: str) -> Options:
    return Options.build(line_breaks, case, flags)


HOME = Tool(
    slug="",
    name="Text cleaner",
    title="TidyText: Clean Up Messy Text Online, Free and Private",
    description=(
        "Fix line breaks, extra spaces and letter case in text copied from PDFs, emails "
        "and websites. Free, instant, and your text never leaves your browser."
    ),
    heading="Clean up messy text in seconds",
    summary="Fix line breaks, spaces and case in one go.",
    intro=(
        "Paste text from a PDF, email or web page, choose what to fix, then copy the clean "
        "version. It all happens instantly in your browser."
    ),
    options=_opts("paragraphs", "keep", "remove_extra_spaces", "remove_invisible"),
    example="This report was\ncopied  from a   PDF,   so\nevery line   is broken.\n\n\nTidyText fixes it.",
)

TOOLS: tuple[Tool, ...] = (
    Tool(
        slug="fix-pdf-line-breaks",
        name="Fix PDF line breaks",
        title="Fix Line Breaks in Text Copied From a PDF",
        description=(
            "Paste text copied from a PDF and join the broken lines back into proper "
            "paragraphs. Keeps paragraph breaks, removes stray spaces. Free and private."
        ),
        heading="Fix line breaks in text copied from a PDF",
        summary="Join broken lines and keep paragraphs.",
        intro=(
            "Text copied from a PDF breaks at the end of every printed line. This joins the "
            "lines back together while keeping the blank line between paragraphs."
        ),
        options=_opts("paragraphs", "keep", "remove_extra_spaces", "remove_invisible"),
        example="The committee met on\nTuesday to review the\nannual budget.\n\nNo changes\nwere approved.",
        faqs=(
            (
                "Why does text copied from a PDF have so many line breaks?",
                "A PDF stores each printed line separately, so copying it gives you a hard "
                "line break wherever the page wrapped, even in the middle of a sentence.",
            ),
            (
                "Will my paragraphs be merged together?",
                "No. Lines are joined only within a paragraph. A blank line between "
                "paragraphs is kept, so the structure of the document stays intact.",
            ),
        ),
    ),
    Tool(
        slug="remove-line-breaks",
        name="Remove line breaks",
        title="Remove Line Breaks Online: Join Lines Into One",
        description=(
            "Remove all line breaks and join your text into a single line, with one space "
            "between the words. Instant, free and private."
        ),
        heading="Remove line breaks",
        summary="Put all your text on a single line.",
        intro=(
            "Turn text with many lines into one continuous line. Every line break becomes a "
            "single space, and empty lines disappear."
        ),
        options=_opts("remove", "keep", "remove_extra_spaces"),
        example="apples\nbananas\n\ncherries\ndates",
        faqs=(
            (
                "What happens to the line breaks?",
                "Each line break is replaced with a single space, so words on separate lines "
                "don't run together.",
            ),
            (
                "Can I keep my paragraphs?",
                "Yes. Choose “Join lines, keep paragraphs” under Line breaks, or use the Fix "
                "PDF line breaks tool.",
            ),
        ),
    ),
    Tool(
        slug="remove-extra-spaces",
        name="Remove extra spaces",
        title="Remove Extra Spaces From Text Online",
        description=(
            "Replace double spaces and tabs with a single space and trim spaces at the start "
            "and end of each line. Line breaks are kept. Free and private."
        ),
        heading="Remove extra spaces",
        summary="Collapse double spaces and tabs, trim lines.",
        intro=(
            "Collapse double spaces, tabs and non-breaking spaces into a single space, and "
            "trim the start and end of every line. Your line breaks stay where they are."
        ),
        options=_opts("keep", "keep", "remove_extra_spaces"),
        example="  Too    many   spaces\there.  \n\tAnd   here.  ",
        faqs=(
            (
                "Does this remove line breaks too?",
                "No. Only spaces and tabs within each line are changed. To remove line "
                "breaks as well, change the Line breaks option.",
            ),
            (
                "What is a non-breaking space?",
                "A special space that often comes along when you copy from web pages or Word. "
                "It looks like a normal space but can break formatting. It's replaced too.",
            ),
        ),
    ),
    Tool(
        slug="remove-empty-lines",
        name="Remove empty lines",
        title="Remove Empty Lines From Text Online",
        description=(
            "Delete blank and whitespace-only lines from your text in one click. Useful for "
            "lists, code and copied content. Free and private."
        ),
        heading="Remove empty lines",
        summary="Delete blank and whitespace-only lines.",
        intro=(
            "Delete every blank line, including lines that only contain spaces or tabs. "
            "Lines with content stay in their original order."
        ),
        options=_opts("keep", "keep", "remove_empty_lines"),
        example="first item\n\n\nsecond item\n   \nthird item",
        faqs=(
            (
                "Are lines with only spaces removed?",
                "Yes. A line that contains nothing but spaces or tabs counts as empty.",
            ),
        ),
    ),
    Tool(
        slug="remove-punctuation",
        name="Remove punctuation",
        title="Remove Punctuation From Text Online",
        description=(
            "Strip commas, periods, quotes, dashes and other punctuation from text, in any "
            "language. Free, instant and private."
        ),
        heading="Remove punctuation",
        summary="Strip commas, periods, quotes and dashes.",
        intro=(
            "Remove punctuation marks such as commas, periods, quotes, brackets and dashes. "
            "Works with punctuation from any language, including “curly quotes” and ¿¡."
        ),
        options=_opts("keep", "keep", "remove_punctuation", "remove_extra_spaces"),
        example="Wait... what?! “Really” — (yes), really.",
        faqs=(
            (
                "Are symbols like $, % and + removed?",
                "Currency signs, math symbols and emoji are kept, because they aren't "
                "punctuation. The percent sign counts as punctuation and is removed.",
            ),
            (
                "Why are apostrophes removed?",
                "An apostrophe is a punctuation mark, so “it's” becomes “its”. Turn the "
                "option off if you need to keep them.",
            ),
        ),
    ),
    Tool(
        slug="remove-invisible-characters",
        name="Remove invisible characters",
        title="Remove Invisible Characters: Zero-Width Spaces and More",
        description=(
            "Find and remove hidden characters such as zero-width spaces, byte order marks "
            "and soft hyphens that break code, search and formatting."
        ),
        heading="Remove invisible characters",
        summary="Remove zero-width spaces and other hidden characters.",
        intro=(
            "Remove characters you can't see but that still cause trouble: zero-width spaces "
            "and joiners, word joiners, byte order marks and soft hyphens."
        ),
        options=_opts("keep", "keep", "remove_invisible"),
        example="pass​word﻿ and soft­hyphen",
        faqs=(
            (
                "How do I know if my text has invisible characters?",
                "Paste it in. If the character count drops after cleaning, invisible "
                "characters were removed.",
            ),
            (
                "Where do these characters come from?",
                "Usually from copying text out of web pages, chat apps, PDFs or word "
                "processors. They can break passwords, code, URLs and spreadsheet formulas.",
            ),
        ),
    ),
    Tool(
        slug="uppercase-converter",
        name="UPPERCASE",
        title="Uppercase Converter: Convert Text to ALL CAPS",
        description=(
            "Convert any text to UPPERCASE letters instantly. Works with accented letters "
            "and any language. Free and private."
        ),
        heading="Convert text to uppercase",
        summary="MAKE EVERY LETTER A CAPITAL.",
        intro="Change every letter to a capital letter. Numbers and symbols stay the same.",
        options=_opts("keep", "upper"),
        example="Meeting moved to Friday, 3 pm.",
    ),
    Tool(
        slug="lowercase-converter",
        name="lowercase",
        title="Lowercase Converter: Convert Text to Lowercase",
        description=(
            "Convert text to lowercase letters instantly, including text written in ALL "
            "CAPS. Free, private and works in any language."
        ),
        heading="Convert text to lowercase",
        summary="make every letter small.",
        intro="Change every capital letter to a small letter, including text typed in caps lock.",
        options=_opts("keep", "lower"),
        example="SORRY FOR SHOUTING, CAPS LOCK WAS ON.",
    ),
    Tool(
        slug="title-case-converter",
        name="Title Case",
        title="Title Case Converter: Capitalize Every Word",
        description=(
            "Capitalize the first letter of every word for headings and titles. Handles "
            "apostrophes and hyphenated words. Free and private."
        ),
        heading="Convert text to title case",
        summary="Capitalize The First Letter Of Every Word.",
        intro=(
            "Capitalize the first letter of every word and make the rest lowercase. "
            "Apostrophes are handled, so “it's” never becomes “It'S”."
        ),
        options=_opts("keep", "title"),
        example="the QUICK guide to well-known tools",
        faqs=(
            (
                "Are small words like “of” and “the” capitalized?",
                "Yes, every word is capitalized. This matches the simple title case used "
                "by most apps, but not the rules of style guides such as APA or Chicago.",
            ),
        ),
    ),
    Tool(
        slug="sentence-case-converter",
        name="Sentence case",
        title="Sentence Case Converter: Fix Capitalization Online",
        description=(
            "Convert text to sentence case: a capital letter at the start of each sentence "
            "and the word “I”, lowercase everywhere else. Free and private."
        ),
        heading="Convert text to sentence case",
        summary="Capitalize the start of each sentence.",
        intro=(
            "Start each sentence with a capital letter and make everything else lowercase. "
            "The word “I” is capitalized too."
        ),
        options=_opts("keep", "sentence"),
        example="THIS WAS TYPED IN CAPS. can i fix it? yes, i can.",
        faqs=(
            (
                "Are names capitalized?",
                "No. TidyText can't tell names apart from other words, so check proper nouns "
                "such as people and places after converting.",
            ),
        ),
    ),
)

TOOLS_BY_SLUG = {tool.slug: tool for tool in TOOLS}

COMMON_FAQS: tuple[tuple[str, str], ...] = (
    (
        "Is my text saved or sent anywhere?",
        "No. With JavaScript turned on, your text is processed entirely in your browser and "
        "never leaves your device. If JavaScript is off, the text is sent to our server only "
        "to format it, and is never saved or logged.",
    ),
    (
        "Is TidyText free?",
        "Yes. There's no sign-up, no limit on how often you use it, and no ads.",
    ),
)
