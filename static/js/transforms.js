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
  "humanize",
  "fix_grammar",
  "paraphrase",
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

// Humanize: phrases that make text sound stiff or machine-written. Keys are lowercase with
// straight apostrophes; they match any capitalisation and either apostrophe.
export const FILLER_PHRASES = [
  "it is important to note that",
  "it's important to note that",
  "it is worth noting that",
  "it's worth noting that",
  "it should be noted that",
  "needless to say,",
  "in today's fast-paced world,",
  "in today's digital age,",
  // More from the MIT-licensed list at github.com/harshaneel/humanize (c) 2026 Harshaneel Gokhale.
  "it is worth mentioning that",
  "it's worth mentioning that",
  "generally speaking,",
  "it goes without saying that",
  "it can be argued that",
  "as previously mentioned,",
];
export const PLAIN_WORDS = {
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
  utilize: "use",
  utilizes: "uses",
  utilized: "used",
  utilizing: "using",
  utilise: "use",
  utilises: "uses",
  utilised: "used",
  utilising: "using",
  leveraging: "using",
  facilitate: "help",
  facilitates: "helps",
  commence: "start",
  commences: "starts",
  commenced: "started",
  ensure: "make sure",
  ensures: "makes sure",
  ensuring: "making sure",
  ensured: "made sure",
  numerous: "many",
  individuals: "people",
  subsequently: "later",
  seamless: "smooth",
  seamlessly: "smoothly",
  robust: "strong",
  comprehensive: "thorough",
  // More from the MIT-licensed list at github.com/harshaneel/humanize (c) 2026 Harshaneel Gokhale.
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
  delve: "dig",
  delves: "digs",
  delving: "digging",
  delved: "dug",
  streamline: "simplify",
  streamlines: "simplifies",
  streamlined: "simplified",
  garner: "get",
  garnered: "got",
  multifaceted: "complex",
  intricate: "complex",
  showcases: "shows",
  showcasing: "showing",
  underscores: "shows",
  pivotal: "key",
  vibrant: "lively",
  breathtaking: "amazing",
  groundbreaking: "new",
};
// Only contracted before another word, so "I know what it is." stays correct.
export const CONTRACTIONS = {
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
  cannot: "can't",
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
};
// Humanize ends with the slips people make when typing fast, very common in South Asian
// English. They run after the contractions, so "you are good" ends up as "your good".
export const SLIPS = {
  "you're": "your",
  "it's": "its",
  "they're": "their",
  than: "then",
  lose: "loose",
  loses: "looses",
  losing: "loosing",
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
};
// Only before another word (that isn't already "about"): "discuss it" → "discuss about it".
export const SLIPS_BEFORE_WORD = {
  discuss: "discuss about",
  discussed: "discussed about",
  discussing: "discussing about",
};

// Paraphrase: hand-checked rewrites that keep the meaning in any sentence. Whole phrases
// where possible; single words only when they have one clear sense.
export const PARAPHRASES = {
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
  purchase: "buy",
  purchased: "bought",
  purchasing: "buying",
  assist: "help",
  assists: "helps",
  assisted: "helped",
  assistance: "help",
  obtain: "get",
  obtains: "gets",
  obtained: "got",
  sufficient: "enough",
  approximately: "about",
  demonstrate: "show",
  demonstrates: "shows",
  demonstrated: "showed",
  additional: "extra",
  frequently: "often",
  occasionally: "sometimes",
  immediately: "right away",
  inquire: "ask",
  inquired: "asked",
  regarding: "about",
  possess: "have",
  possesses: "has",
  terminate: "end",
  terminated: "ended",
  modify: "change",
  modifies: "changes",
  modified: "changed",
  visualize: "picture",
  residence: "home",
};

// Fix grammar undoes those slips, and a few more.
export const COMPARATIVES = [
  "more", "less", "rather", "other", "fewer", "better", "worse", "greater", "larger", "bigger",
  "smaller", "higher", "lower", "faster", "slower", "longer", "shorter", "older", "younger",
  "easier", "harder", "cheaper", "stronger", "earlier", "later",
];
export const GRAMMAR_FIXES = {
  dont: "don't",
  doesnt: "doesn't",
  didnt: "didn't",
  cant: "can't",
  wont: "won't",
  isnt: "isn't",
  arent: "aren't",
  wasnt: "wasn't",
  werent: "weren't",
  havent: "haven't",
  hasnt: "hasn't",
  wouldnt: "wouldn't",
  shouldnt: "shouldn't",
  couldnt: "couldn't",
  im: "I'm",
  ive: "I've",
  youre: "you're",
  theyre: "they're",
  thats: "that's",
  whats: "what's",
  alot: "a lot",
  infront: "in front",
  atleast: "at least",
  incase: "in case",
  aswell: "as well",
  eachother: "each other",
  everytime: "every time",
  loosing: "losing",
  looses: "loses",
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
  informations: "information",
  advices: "advice",
  furnitures: "furniture",
  equipments: "equipment",
  luggages: "luggage",
  baggages: "baggage",
  softwares: "software",
  feedbacks: "feedback",
  stuffs: "stuff",
  "discuss about": "discuss",
  "discussed about": "discussed",
  "discussing about": "discussing",
  "mention about": "mention",
  "cope up with": "cope with",
  "return back": "return",
  "reply back": "reply",
  "revert back": "reply",
  "explain me": "explain to me",
  ...Object.fromEntries(COMPARATIVES.map((word) => [`${word} then`, `${word} than`])),
};
// "your", "its" and "their" are right in "your car" but wrong in "your welcome", so these
// change only before words that can't follow a possessive...
export const SUBJECT_NEXT = [
  "a", "an", "the", "not", "so", "too", "really", "just", "always", "never", "still", "also",
  "being", "going", "gonna", "doing", "getting", "making", "trying", "looking", "coming",
  "here", "there", "my", "such", "absolutely", "probably", "definitely", "actually",
];
// ...or before an adjective that ends the clause: "your good." but not "your good name".
export const PREDICATES = [
  "good", "great", "fine", "okay", "ok", "sure", "right", "wrong", "welcome", "late", "early",
  "beautiful", "amazing", "awesome", "smart", "crazy", "lucky", "done", "ready", "sorry",
  "correct", "free", "busy", "kind", "funny", "cute", "safe", "true", "over", "easy", "hard",
  "important", "possible", "clear",
];
// "your welcome to join" needs fixing, "your right to vote" doesn't, so only these before "to".
export const PREDICATES_BEFORE_TO = ["welcome", "ready", "free", "sure", "able", "happy", "lucky", "kind"];
export const CONTEXT_FIXES = {
  your: ["you're", []],
  its: ["it's", ["been", "raining", "time", "better", "worse"]],
  their: ["they're", []],
};
const CLAUSE_END = "[ \\t]*(?:[.,!?;:)\\n]|(?![\\s\\S]))|[ \\t]+(?:at|with|for|now|too|enough|already|though)(?!\\p{L})";
// "since 2 years" (South Asian) and "for 2 years" (standard).
const DURATION = "[ \\t]+(?:[0-9]+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|many|several)[ \\t]+(?:year|month|week|day|hour)s?(?!\\p{L})";
const PHRASE_SPACE = /[ \t]+/g;
const EM_DASH = /(?<=[^ \t\n])[ \t]*\u2014[ \t]*(?=[^ \t\n])/g;
const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// One case-insensitive pattern for whole phrases, longest first, any apostrophe and spacing.
function phrases(list, tail = "") {
  const longestFirst = [...list].sort((a, b) => b.length - a.length);
  const body = longestFirst
    .map((p) => p.split(" ").map((w) => escapeRegExp(w).replaceAll("'", "['\u2019]")).join("[ \\t]+"))
    .join("|");
  return new RegExp(`(?<!\\p{L})(?:${body})(?!\\p{L})${tail}`, "giu");
}

const FILLER = phrases(FILLER_PHRASES, "[ \\t]+(.?)");
const PLAIN = phrases(Object.keys(PLAIN_WORDS));
const CONTRACTIBLE = phrases(Object.keys(CONTRACTIONS), "(?=[ \\t]+\\p{L})");
const SLIPPED = phrases(Object.keys(SLIPS));
const SLIPPED_BEFORE_WORD = phrases(Object.keys(SLIPS_BEFORE_WORD), "(?=[ \\t]+(?!about(?!\\p{L}))\\p{L})");
const FOR_DURATION = new RegExp(`(?<!\\p{L})for(?=${DURATION})`, "giu");
const PARAPHRASABLE = phrases(Object.keys(PARAPHRASES));
const FIXABLE = phrases(Object.keys(GRAMMAR_FIXES));
const SINCE_DURATION = new RegExp(`(?<!\\p{L})since(?=${DURATION})`, "giu");

function context(word, extraNext) {
  const nexts = [...SUBJECT_NEXT, ...extraNext].join("|");
  return (
    `${word}(?=[ \\t]+(?:(?:${nexts})(?!\\p{L})|(?:${PREDICATES.join("|")})(?:${CLAUSE_END})` +
    `|(?:${PREDICATES_BEFORE_TO.join("|")})[ \\t]+to(?!\\p{L})))`
  );
}

const CONTEXTUAL = new RegExp(
  `(?<!\\p{L})(?:${Object.entries(CONTEXT_FIXES)
    .map(([word, [, extra]]) => context(word, extra))
    .join("|")})`,
  "giu",
);
const CONTEXT_REPLACEMENTS = Object.fromEntries(Object.entries(CONTEXT_FIXES).map(([word, [fix]]) => [word, fix]));

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

const phraseKey = (match) => match.toLowerCase().replace(PHRASE_SPACE, " ").replaceAll("’", "'");
const isUpper = (s) => s === s.toUpperCase() && s !== s.toLowerCase();

// Give the replacement the capitals of the text it replaces: Utilize → Use, DO NOT → DON'T.
function matchCase(source, replacement) {
  if (isUpper(source)) return replacement.toUpperCase();
  if (isUpper(source.slice(0, 1))) return replacement.slice(0, 1).toUpperCase() + replacement.slice(1);
  return replacement;
}

// Write new apostrophes the way the text already does.
const apostropheOf = (text) => (text.includes("’") && !text.includes("'") ? "’" : "'");
const swap = (pattern, table, text, apostrophe = "'") =>
  text.replace(pattern, (match) => matchCase(match, table[phraseKey(match)]).replaceAll("'", apostrophe));

// Make text read like a person typed it: plain words, contractions, everyday slips.
export function humanize(input) {
  const apostrophe = apostropheOf(input);
  let text = input.replace(FILLER, (match, next) => (isUpper(match.slice(0, 1)) ? next.toUpperCase() : next));
  text = swap(PLAIN, PLAIN_WORDS, text);
  text = swap(CONTRACTIBLE, CONTRACTIONS, text, apostrophe);
  text = text.replace(EM_DASH, ", ");
  text = swap(SLIPPED, SLIPS, text);
  text = swap(SLIPPED_BEFORE_WORD, SLIPS_BEFORE_WORD, text);
  return text.replace(FOR_DURATION, (match) => matchCase(match, "since"));
}

// Reword with hand-checked phrase rewrites: "is able to" → "can", "very tired" → "exhausted".
export const paraphrase = (text) => swap(PARAPHRASABLE, PARAPHRASES, text);

// Fix common slips: your good → you're good, dont → don't, better then → better than.
export function fixGrammar(input) {
  const apostrophe = apostropheOf(input);
  let text = swap(FIXABLE, GRAMMAR_FIXES, input, apostrophe);
  text = swap(CONTEXTUAL, CONTEXT_REPLACEMENTS, text, apostrophe);
  text = text.replace(SINCE_DURATION, (match) => matchCase(match, "for"));
  return text.replace(PRONOUN_I, "I");
}
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
  if (flags.has("fix_grammar")) text = fixGrammar(text);
  if (flags.has("paraphrase")) text = paraphrase(text);
  if (flags.has("humanize")) text = humanize(text);
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
