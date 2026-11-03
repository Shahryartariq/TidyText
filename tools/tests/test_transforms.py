import json
from dataclasses import asdict
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
                    opts.get("line_breaks", "keep"),
                    opts.get("case", "keep"),
                    opts.get("flags", []),
                    opts.get("sort", "keep"),
                    opts.get("find", ""),
                    opts.get("replace", ""),
                )
                output = transforms.apply(case["input"], options)
                self.assertEqual(output, case["expected"])
                self.assertEqual(asdict(transforms.stats(output)), case["stats"])
                self.assertEqual(asdict(transforms.details(output)), case["details"])


class OptionsTests(SimpleTestCase):
    def test_unknown_values_fall_back_to_safe_defaults(self):
        options = Options.build("explode", "shout", ["remove_extra_spaces", "rm -rf"], sort="random")
        self.assertEqual(options.line_breaks, "keep")
        self.assertEqual(options.case, "keep")
        self.assertEqual(options.sort, "keep")
        self.assertEqual(options.flags, frozenset({"remove_extra_spaces"}))

    def test_find_and_replace_are_length_limited(self):
        options = Options.build(find="x" * 5000, replace="y" * 5000)
        self.assertEqual(len(options.find), transforms.MAX_FIND_CHARS)
        self.assertEqual(len(options.replace), transforms.MAX_FIND_CHARS)

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

    def test_html_entities_out_of_range_are_left_alone(self):
        self.assertEqual(transforms.strip_html("&#0; &#xD800; &#99999999;"), "&#0; &#xD800; &#99999999;")

    def test_hyphenation_keeps_capitalised_continuations(self):
        self.assertEqual(transforms.fix_hyphenation("New-\nYork re-\nport"), "New-\nYork report")

    def test_sort_ignores_accents_and_case(self):
        self.assertEqual(transforms.sort_lines("éclair\nEagle\ndonut", "az"), "donut\nEagle\néclair")

    def test_reading_time_is_zero_for_empty_text(self):
        self.assertEqual(transforms.details("").reading_seconds, 0)

    def test_stats_counts_windows_newlines_once(self):
        self.assertEqual(transforms.stats("a\r\nb").lines, 2)


class HumanizeTests(SimpleTestCase):
    def test_every_rule_is_in_a_shared_case(self):
        # The shared cases are what keep the JavaScript tables in step with these.
        inputs = {case["name"]: case["input"].split("\n") for case in CASES}
        context = [
            line
            for word, (_, extra) in transforms.CONTEXT_FIXES.items()
            for line in (
                [f"{word} {n}" for n in transforms.SUBJECT_NEXT + extra]
                + [f"{word} {a}." for a in transforms.PREDICATES]
                + [f"{word} {a} to" for a in transforms.PREDICATES_BEFORE_TO]
            )
        ]
        tables = {
            "humanize covers every phrase": [
                *transforms.FILLER_PHRASES,
                *transforms.PLAIN_WORDS,
                *transforms.CONTRACTIONS,
                *transforms.SLIPS,
                *transforms.SLIPS_BEFORE_WORD,
            ],
            "fix grammar covers every rule": [*transforms.GRAMMAR_FIXES, *context],
            "paraphrase covers every phrase": list(transforms.PARAPHRASES),
        }
        for name, phrases in tables.items():
            # Each line is a phrase followed by "word" (or "next words" after a filler phrase).
            covered = {line.removesuffix(" next words").removesuffix(" word") for line in inputs[name]}
            for phrase in phrases:
                with self.subTest(phrase):
                    self.assertIn(phrase, covered, f"add “{phrase}” to the “{name}” case and run make cases")

    def test_contractions_wait_for_another_word(self):
        self.assertEqual(transforms.humanize("Yes, they are. We are done."), "Yes, they are. We're done.")

    def test_capitals_follow_the_original(self):
        self.assertEqual(transforms.humanize("Utilize it. UTILIZE it."), "Use it. USE it.")

    def test_humanize_adds_the_slips(self):
        self.assertEqual(transforms.humanize("You're good. You are right."), "Your good. Your right.")

    def test_fix_grammar_undoes_the_slips(self):
        self.assertEqual(transforms.fix_grammar("Your good. Your right."), "You're good. You're right.")

    def test_fix_grammar_leaves_possessives(self):
        text = "Your good name, your right to vote, its tail and their house."
        self.assertEqual(transforms.fix_grammar(text), text)

    def test_paraphrase_keeps_capitals(self):
        self.assertEqual(transforms.paraphrase("Purchase it. VERY TIRED."), "Buy it. EXHAUSTED.")

    def test_fix_grammar_runs_before_humanize(self):
        options = Options.build(flags=["humanize", "fix_grammar"])
        self.assertEqual(transforms.apply("i dont know", options), "I dont know")
