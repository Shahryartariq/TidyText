// Text transformations, ported line for line from tools/transforms.py.
// Both implementations are tested against tools/tests/cases.json.

export const LINE_BREAK_MODES = ["keep", "paragraphs", "remove"];
export const CASE_MODES = ["keep", "upper", "lower", "title", "sentence"];
export const FLAGS = ["remove_extra_spaces", "remove_empty_lines", "remove_punctuation", "remove_invisible"];

const INVISIBLE = /[\u200b\u200c\u200d\u2060\ufeff\u00ad]/g;
const NEWLINES = /\r\n|\r/g;
const BLANK_LINE = /\n[ \t\u00a0]*\n/;
const HORIZONTAL_SPACE = /[ \t\u00a0]+/g;
const PUNCTUATION = /\p{P}/gu;
const TITLE_START = /(^|[\s\-/(\[{"“‘])(\p{L})/gu;
const SENTENCE_START = /(^[\s"'“‘(]*|[.!?]["'”’)]*\s+["'“‘(]*|\n[\s"'“‘(]*)(\p{L})/gu;
const PRONOUN_I = /(?<!\p{L})i(?!\p{L}|\.e\.)/gu;

export function normalizeOptions({ lineBreaks = "keep", textCase = "keep", flags = [] } = {}) {
  return {
    lineBreaks: LINE_BREAK_MODES.includes(lineBreaks) ? lineBreaks : "keep",
    textCase: CASE_MODES.includes(textCase) ? textCase : "keep",
    flags: new Set([...flags].filter((f) => FLAGS.includes(f))),
  };
}

const normalizeNewlines = (text) => text.replace(NEWLINES, "\n");
const nonBlank = (line) => line.trim() !== "";
const joinLines = (text) =>
  text
    .split("\n")
    .filter(nonBlank)
    .map((line) => line.trim())
    .join(" ");

export const removeInvisible = (text) => text.replace(INVISIBLE, "");
export const removePunctuation = (text) => text.replace(PUNCTUATION, "");
export const removeLineBreaks = (text) => joinLines(text);
export const joinParagraphLines = (text) => text.split(BLANK_LINE).map(joinLines).filter(Boolean).join("\n\n");
export const removeEmptyLines = (text) => text.split("\n").filter(nonBlank).join("\n");
export const removeExtraSpaces = (text) =>
  text
    .split("\n")
    .map((line) => line.replace(HORIZONTAL_SPACE, " ").trim())
    .join("\n");

const upperFirst = (_, before, letter) => before + letter.toUpperCase();
export const titleCase = (text) => text.toLowerCase().replace(TITLE_START, upperFirst);
export const sentenceCase = (text) => text.toLowerCase().replace(SENTENCE_START, upperFirst).replace(PRONOUN_I, "I");

const CASES = {
  upper: (text) => text.toUpperCase(),
  lower: (text) => text.toLowerCase(),
  title: titleCase,
  sentence: sentenceCase,
};

export function apply(input, options) {
  const { lineBreaks, textCase, flags } = normalizeOptions(options);
  let text = normalizeNewlines(input);
  if (flags.has("remove_invisible")) text = removeInvisible(text);
  if (flags.has("remove_punctuation")) text = removePunctuation(text);
  if (lineBreaks === "remove") text = removeLineBreaks(text);
  else if (lineBreaks === "paragraphs") text = joinParagraphLines(text);
  if (flags.has("remove_empty_lines")) text = removeEmptyLines(text);
  if (flags.has("remove_extra_spaces")) text = removeExtraSpaces(text);
  if (CASES[textCase]) text = CASES[textCase](text);
  return text;
}

export function stats(input) {
  const text = normalizeNewlines(input);
  const words = text.split(/\s+/).filter(Boolean).length;
  return {
    characters: [...text].length,
    words,
    lines: text === "" ? 0 : text.split("\n").length,
  };
}
