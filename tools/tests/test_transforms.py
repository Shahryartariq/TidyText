import json
from pathlib import Path

from django.test import SimpleTestCase

from tools import transforms
from tools.transforms import Options

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


class SharedCasesTests(SimpleTestCase):
    """The same cases are run against static/js/transforms.js by `make test-js`."""

    def test_cases(self):
        for case in CASES:
            with self.subTest(case["name"]):
                opts = case["options"]
                options = Options.build(
                    opts.get("line_breaks", "keep"), opts.get("case", "keep"), opts.get("flags", [])
                )
                output = transforms.apply(case["input"], options)
                self.assertEqual(output, case["expected"])
                s = transforms.stats(output)
                self.assertEqual(
                    {"characters": s.characters, "words": s.words, "lines": s.lines}, case["stats"]
                )


class OptionsTests(SimpleTestCase):
    def test_unknown_values_fall_back_to_safe_defaults(self):
        options = Options.build("explode", "shout", ["remove_extra_spaces", "rm -rf"])
        self.assertEqual(options.line_breaks, "keep")
        self.assertEqual(options.case, "keep")
        self.assertEqual(options.flags, frozenset({"remove_extra_spaces"}))

    def test_noop(self):
        self.assertTrue(Options.build().is_noop)
        self.assertFalse(Options.build(case="upper").is_noop)


class TransformTests(SimpleTestCase):
    def test_paragraph_mode_never_glues_words_together(self):
        self.assertEqual(transforms.join_paragraph_lines("end of\nline"), "end of line")

    def test_title_case_handles_apostrophes(self):
        self.assertEqual(transforms.title_case("it's DON'T"), "It's Don't")

    def test_sentence_case_capitalises_the_pronoun_i(self):
        self.assertEqual(transforms.sentence_case("yes i can. i'll try"), "Yes I can. I'll try")

    def test_large_input_is_fast(self):
        text = ("Some   text copied\nfrom a PDF.\n\n" * 20_000)[:200_000]
        options = Options.build(
            "paragraphs", "sentence", ["remove_extra_spaces", "remove_invisible", "remove_punctuation"]
        )
        output = transforms.apply(text, options)
        self.assertTrue(output.startswith("Some text copied from a pdf\n\nSome text"))

    def test_stats_counts_windows_newlines_once(self):
        self.assertEqual(transforms.stats("a\r\nb").lines, 2)
