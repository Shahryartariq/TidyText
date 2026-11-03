# Roadmap

Planned features. Each one must keep TidyText's rules: free, private (text stays in the
browser), and the same result from the Python and JavaScript versions.

## Done (unreleased, on the `feat/humanizer` branch)

- [x] **Grammar check** (`/grammar-fixer/`, the "Fix grammar" option): fixes the slips people
  make when typing fast, especially in South Asian English: "your good" → "you're good",
  "its a" → "it's a", "better then" → "better than", "dont" → "don't", "could of",
  "informations", "discuss about", "since 2 years". "your", "its" and "their" change only when
  the next words make the meaning clear, so "your good name" and "your right to vote" stay.
- [x] **Humanizer** (`/ai-text-humanizer/`): drops filler, swaps stiff words for plain ones,
  uses contractions, turns em dashes into commas, then adds everyday slips ("you're good" →
  "your good"). Extra AI-sounding phrases come from the MIT-licensed list at
  [harshaneel/humanize](https://github.com/harshaneel/humanize).
- [x] **Paraphraser** (`/paraphrasing-tool/`, the "Paraphrase" option): about 100 hand-checked
  phrase rewrites ("is able to" → "can").
- [x] **Paraphrase with AI** (beta): humarin's T5 paraphrase model
  ([8-bit ONNX version](https://huggingface.co/Felladrin/onnx-chatgpt_paraphraser_on_T5_base)),
  run with Transformers.js 4.3.1 in a worker on the visitor's device. About 250 MB on first use.
- [x] Pipeline: grammar check → paraphrase (rule-based or AI) → humanize.

## To do

- [ ] Get a legal review of the AI model's OpenRAIL license before launch. It requires showing
  users its use restrictions and a copy of the license, and one restriction is that
  machine-generated text must be disclosed as such, which sits uneasily with a humanizer.
- [ ] Grow the paraphrase list, ideally from a hand-checked subset of the
  [Paraphrase Database](http://paraphrase.org/) (CC BY, needs attribution).
- [ ] Let the AI paraphraser offer more than one version of each sentence (beam search).
- [ ] Use WebGPU for the AI model when the browser supports it, for faster rewrites.

## Ruled out

- [ksanyok/TextHumanize](https://github.com/ksanyok/TextHumanize): its license forbids
  revenue-generating use without a paid license.
- [ZAYUVALYA/AI-Text-Humanizer](https://github.com/ZAYUVALYA/AI-Text-Humanizer): no license
  file, and the code sends text to an outside AI service.
- [coedit-large ONNX](https://huggingface.co/imrahamed/coedit-large-webgpu-onnx): 3.3 GB and
  licensed for non-commercial use only.
