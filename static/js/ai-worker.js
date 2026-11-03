// The optional AI paraphraser, run in a worker so the page stays responsive.
// The model is downloaded from Hugging Face once, cached by the browser, and runs on this
// device: the text never leaves it. Model: humarin/chatgpt_paraphraser_on_T5_base
// (OpenRAIL license), in Felladrin's 8-bit ONNX version (about 250 MB).
import { env, pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.1/dist/transformers.min.js";

const MODEL = "Felladrin/onnx-chatgpt_paraphraser_on_T5_base";
// A sentence ends at . ! or ? (plus closing quotes) followed by a space or the line end,
// so "1.5" stays whole. Pieces ending in a common abbreviation are joined to the next one.
const SENTENCES = /.*?[.!?]+["')\]”’]*(?:\s+|$)|.+$/g;
const ABBREVIATION = /(?:^|\s)(?:Mr|Mrs|Ms|Dr|Prof|St|Sr|Jr|vs|etc|e\.g|i\.e)\.\s*$/i;
const LETTER = /\p{L}/u;

env.allowLocalModels = false;

let model = null;

function load() {
  const files = new Map();
  model ??= pipeline("text2text-generation", MODEL, {
    dtype: "q8",
    device: "wasm",
    progress_callback: (event) => {
      if (event.status !== "progress" || !event.total) return;
      files.set(event.file, [event.loaded, event.total]);
      let loaded = 0;
      let total = 0;
      for (const [l, t] of files.values()) {
        loaded += l;
        total += t;
      }
      postMessage({ type: "download", loaded, total });
    },
  });
  return model;
}

// Splits a line into sentences, or keeps it whole if the split would lose characters.
function sentences(line) {
  const parts = [];
  for (const part of line.match(SENTENCES) ?? []) {
    if (parts.length && ABBREVIATION.test(parts.at(-1))) parts[parts.length - 1] += part;
    else parts.push(part);
  }
  return parts.join("") === line ? parts : [line];
}

async function rewrite(text) {
  postMessage({ type: "status", text: "Getting the AI model ready…" });
  const paraphraser = await load();
  const lines = text.split("\n").map(sentences);
  const total = lines.flat().filter((s) => LETTER.test(s)).length;
  let done = 0;
  const out = [];
  for (const parts of lines) {
    let line = "";
    for (const sentence of parts) {
      const core = sentence.trim();
      if (!LETTER.test(core)) {
        line += sentence;
        continue;
      }
      const before = sentence.slice(0, sentence.length - sentence.trimStart().length);
      const after = sentence.slice(sentence.trimEnd().length);
      const [result] = await paraphraser(`paraphrase: ${core}`, {
        max_new_tokens: Math.min(256, Math.ceil(core.length / 3) + 16),
        repetition_penalty: 1.2,
      });
      line += before + (result?.generated_text?.trim() || core) + after;
      postMessage({ type: "progress", done: ++done, total });
    }
    out.push(line);
  }
  return out.join("\n");
}

self.onmessage = async ({ data }) => {
  try {
    postMessage({ type: "result", id: data.id, text: await rewrite(data.text) });
  } catch (error) {
    model = null; // let the next run try the download again
    postMessage({ type: "error", id: data.id, message: String(error?.message ?? error) });
  }
};
