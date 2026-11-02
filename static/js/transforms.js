// Text transformations, ported line for line from tools/transforms.py.
// Both implementations are tested against tools/tests/cases.json.

export const LINE_BREAK_MODES = ["keep", "paragraphs", "remove"];
export const CASE_MODES = ["keep", "upper", "lower", "title", "sentence"];
export const SORT_MODES = ["keep", "az", "za"];
export const FLAGS = [
  "remove_extra_spaces",
  "remove_empty_lines",
  "remove_duplicate_lines",
  "remove_invisible",
  "fix_hyphenation",
  "straighten_quotes",
  "strip_html",
  "remove_punctuation",
];
export const MAX_FIND_CHARS = 1000;

const WHITESPACE = " \\t\\n\\f\\v\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const INVISIBLE = new RegExp(`[${[0x200b, 0x200c, 0x200d, 0x2060, 0xfeff, 0x00ad].map((c) => String.fromCharCode(c)).join("")}]`, "g");
const NEWLINES = /\r\n|\r/g;
const BLANK_LINE = /\n[ \t\u00a0]*\n/;
const HORIZONTAL_SPACE = /[ \t\u00a0]+/g;
const WORD = new RegExp(`[^${WHITESPACE}]+`, "gu");
const NON_SPACE = new RegExp(`[^${WHITESPACE}]`, "gu");
const PUNCTUATION = /\p{P}/gu;
const TITLE_START = /(^|[\s\-/(\[{"“‘])(\p{L})/gu;
const SENTENCE_START = /(^[\s"'“‘(]*|[.!?]["'”’)]*\s+["'“‘(]*|\n[\s"'“‘(]*)(\p{L})/gu;
const PRONOUN_I = /(?<!\p{L})i(?!\p{L}|\.e\.)/gu;
const SENTENCE_END = /[.!?]+(?=[\s"'”’)]|$)/;
const ALNUM = /[\p{L}\p{N}]/u;
const HYPHEN_BREAK = /(\p{L})-[ \t]*\n[ \t]*(\p{L})/gu;
const ESCAPES = /\\(n|t|\\)/g;
const QUOTES = {
  "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
  "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
  "–": "-", "—": "-", "…": "...",
};
const QUOTE_CHARS = new RegExp(`[${Object.keys(QUOTES).join("")}]`, "g");
const HTML_COMMENT = /<!--[\s\S]*?-->/g;
const HTML_SCRIPT = /<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi;
const HTML_BREAK = /<br\s*\/?>|<\/(?:p|div|li|h[1-6]|tr|blockquote|pre)\s*>/gi;
const HTML_TAG = /<\/?[a-zA-Z][^>]*>/g;
const HTML_ENTITY = /&(#\d{1,7}|#x[0-9a-f]{1,6}|nbsp|amp|lt|gt|quot|apos);/gi;
const NAMED_ENTITIES = { nbsp: "\u00a0", amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" };

export function normalizeOptions({ lineBreaks = "keep", textCase = "keep", flags = [], sort = "keep", find = "", replace = "" } = {}) {
  return {
    lineBreaks: LINE_BREAK_MODES.includes(lineBreaks) ? lineBreaks : "keep",
    textCase: CASE_MODES.includes(textCase) ? textCase : "keep",
    flags: new Set([...flags].filter((f) => FLAGS.includes(f))),
    sort: SORT_MODES.includes(sort) ? sort : "keep",
    find: (find || "").slice(0, MAX_FIND_CHARS),
    replace: (replace || "").slice(0, MAX_FIND_CHARS),
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

export const unescape = (value) => value.replace(ESCAPES, (_, c) => ({ n: "\n", t: "\t", "\\": "\\" })[c]);

export function findReplace(text, find, replace) {
  const needle = unescape(find);
  return needle ? text.split(needle).join(unescape(replace)) : text;
}

function decodeEntity(match, raw) {
  const name = raw.toLowerCase();
  if (name in NAMED_ENTITIES) return NAMED_ENTITIES[name];
  const code = name.startsWith("#x") ? parseInt(name.slice(2), 16) : parseInt(name.slice(1), 10);
  return code > 0 && code <= 0x10ffff && !(code >= 0xd800 && code <= 0xdfff) ? String.fromCodePoint(code) : match;
}

export const stripHtml = (text) =>
  text
    .replace(HTML_COMMENT, "")
    .replace(HTML_SCRIPT, "")
    .replace(HTML_BREAK, "\n")
    .replace(HTML_TAG, "")
    .replace(HTML_ENTITY, decodeEntity);

export const removeInvisible = (text) => text.replace(INVISIBLE, "");
export const straightenQuotes = (text) => text.replace(QUOTE_CHARS, (ch) => QUOTES[ch]);
export const fixHyphenation = (text) =>
  text.replace(HYPHEN_BREAK, (match, a, b) => (b !== b.toUpperCase() && b === b.toLowerCase() ? a + b : match));
export const removePunctuation = (text) => text.replace(PUNCTUATION, "");
export const removeLineBreaks = (text) => joinLines(text);
export const joinParagraphLines = (text) => text.split(BLANK_LINE).map(joinLines).filter(Boolean).join("\n\n");
export const removeEmptyLines = (text) => text.split("\n").filter(nonBlank).join("\n");
export const removeExtraSpaces = (text) =>
  text
    .split("\n")
    .map((line) => line.replace(HORIZONTAL_SPACE, " ").trim())
    .join("\n");

export function removeDuplicateLines(text) {
  const seen = new Set();
  return text
    .split("\n")
    .filter((line) => {
      if (!nonBlank(line)) return true;
      if (seen.has(line)) return false;
      seen.add(line);
      return true;
    })
    .join("\n");
}

const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const MARKS = /\p{M}/gu;
// Alphabetical order that ignores case and accents: "apple", "Äpfel", "banana".
const sortKey = (line) => {
  const lower = line.toLowerCase();
  return [lower.normalize("NFKD").replace(MARKS, ""), lower, line];
};
const compareKeys = (a, b) => compare(a[0], b[0]) || compare(a[1], b[1]) || compare(a[2], b[2]);

export function sortLines(text, mode) {
  const lines = text.split("\n");
  const filled = lines
    .filter(nonBlank)
    .map((line) => [sortKey(line), line])
    .sort((a, b) => compareKeys(a[0], b[0]))
    .map(([, line]) => line);
  if (mode === "za") filled.reverse();
  return [...filled, ...lines.filter((line) => !nonBlank(line))].join("\n");
}

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
  const { lineBreaks, textCase, flags, sort, find, replace } = normalizeOptions(options);
  let text = normalizeNewlines(input);
  text = findReplace(text, find, replace);
  if (flags.has("strip_html")) text = stripHtml(text);
  if (flags.has("remove_invisible")) text = removeInvisible(text);
  if (flags.has("straighten_quotes")) text = straightenQuotes(text);
  if (flags.has("fix_hyphenation")) text = fixHyphenation(text);
  if (flags.has("remove_punctuation")) text = removePunctuation(text);
  if (lineBreaks === "remove") text = removeLineBreaks(text);
  else if (lineBreaks === "paragraphs") text = joinParagraphLines(text);
  if (flags.has("remove_empty_lines")) text = removeEmptyLines(text);
  if (flags.has("remove_extra_spaces")) text = removeExtraSpaces(text);
  if (flags.has("remove_duplicate_lines")) text = removeDuplicateLines(text);
  if (sort !== "keep") text = sortLines(text, sort);
  if (CASES[textCase]) text = CASES[textCase](text);
  return text;
}

const count = (text, re) => (text.match(re) || []).length;

export function stats(input) {
  const text = normalizeNewlines(input);
  return {
    characters: [...text].length,
    words: count(text, WORD),
    lines: text === "" ? 0 : text.split("\n").length,
  };
}

export const WORDS_PER_MINUTE_READING = 238;
export const WORDS_PER_MINUTE_SPEAKING = 150;

export function details(input) {
  const text = normalizeNewlines(input);
  const words = count(text, WORD);
  return {
    characters_no_spaces: count(text, NON_SPACE),
    sentences: text.split(SENTENCE_END).filter((part) => ALNUM.test(part)).length,
    paragraphs: text.split(BLANK_LINE).filter((part) => part.trim() !== "").length,
    reading_seconds: Math.ceil((words * 60) / WORDS_PER_MINUTE_READING),
    speaking_seconds: Math.ceil((words * 60) / WORDS_PER_MINUTE_SPEAKING),
  };
}
