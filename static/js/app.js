// Instant, in-browser cleaning. The server only formats text when JavaScript is off.
import { apply, details, stats } from "./transforms.js";

const MAX_CHARS = 200_000;
const MAX_FILE_BYTES = 5 * 1024 * 1024;
const form = document.querySelector("[data-tool]");

if (form) {
  const input = form.querySelector("[data-input]");
  const output = form.querySelector("[data-output]");
  const before = form.querySelector('[data-stats="before"]');
  const after = form.querySelector('[data-stats="after"]');
  const detailBox = form.querySelector("[data-details]");
  const fileInput = form.querySelector("[data-file]");
  const inputPane = input.closest(".pane");
  const toast = form.querySelector("[data-toast]");
  const errorBox = form.querySelector(".form-error");
  const fmt = new Intl.NumberFormat("en-US");
  const LABELS = ["characters", "words", "lines"];

  const readOptions = () => ({
    lineBreaks: form.querySelector('input[name="line_breaks"]:checked')?.value ?? "keep",
    textCase: form.elements.case.value,
    sort: form.elements.sort.value,
    find: form.elements.find.value,
    replace: form.elements.replace.value,
    flags: [...form.querySelectorAll('input[name="flags"]:checked')].map((el) => el.value),
  });

  const delta = (a, b) => (b > a ? `+${fmt.format(b - a)}` : `−${fmt.format(a - b)}`);
  const label = (key, n) => ` ${key.slice(0, -1)}${n === 1 ? "" : "s"}`;
  const duration = (seconds) => {
    if (seconds < 60) return `${seconds} sec`;
    const minutes = Math.floor(seconds / 60);
    const rest = seconds % 60;
    return rest === 0 || minutes >= 10 ? `${minutes} min` : `${minutes} min ${rest} sec`;
  };

  // Renders "1,240 characters −312" for each stat; the mark shows the change.
  const renderStats = (target, a, b) => {
    target.replaceChildren(
      ...LABELS.map((key) => {
        const span = document.createElement("span");
        const value = document.createElement("b");
        value.textContent = fmt.format(b[key]);
        span.append(value, label(key, b[key]));
        if (a[key] !== b[key]) {
          const mark = document.createElement("mark");
          mark.className = "delta";
          mark.textContent = delta(a[key], b[key]);
          span.append(" ", mark);
        }
        return span;
      }),
    );
  };

  const renderDetails = (text, s) => {
    if (!detailBox) return;
    const d = details(text);
    const values = {
      words: fmt.format(s.words),
      characters: fmt.format(s.characters),
      lines: fmt.format(s.lines),
      characters_no_spaces: fmt.format(d.characters_no_spaces),
      sentences: fmt.format(d.sentences),
      paragraphs: fmt.format(d.paragraphs),
      reading_seconds: duration(d.reading_seconds),
      speaking_seconds: duration(d.speaking_seconds),
    };
    for (const [key, value] of Object.entries(values)) {
      const cell = detailBox.querySelector(`[data-detail="${key}"]`);
      if (cell) cell.textContent = value;
    }
  };

  const update = () => {
    errorBox?.remove();
    const cleaned = apply(input.value, readOptions());
    output.value = cleaned;
    const a = stats(input.value);
    const b = stats(cleaned);
    renderStats(before, a, a);
    if (input.value === "") after.replaceChildren();
    else renderStats(after, a, b);
    renderDetails(cleaned, b);
  };

  // Very long text: wait until typing pauses so the page stays responsive.
  let timer = 0;
  const schedule = () => {
    clearTimeout(timer);
    if (input.value.length > 50_000) timer = setTimeout(update, 150);
    else update();
  };

  let toastTimer = 0;
  const say = (message) => {
    toast.textContent = message;
    toast.classList.add("is-visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
  };

  const setInput = (text, message) => {
    const trimmed = text.length > MAX_CHARS;
    input.value = trimmed ? text.slice(0, MAX_CHARS) : text;
    update();
    say(trimmed ? `Only the first ${fmt.format(MAX_CHARS)} characters were kept.` : message);
  };

  const copy = async () => {
    if (!output.value) return say("Nothing to copy yet. Paste some text first.");
    try {
      await navigator.clipboard.writeText(output.value);
    } catch {
      output.select();
      document.execCommand("copy");
    }
    say("Copied to clipboard");
  };

  const paste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (!text) return say("Your clipboard is empty.");
      setInput(text, "Pasted from clipboard");
    } catch {
      input.focus();
      say("Press Ctrl+V (or ⌘V) to paste.");
    }
  };

  const download = () => {
    if (!output.value) return say("Nothing to download yet. Paste some text first.");
    const url = URL.createObjectURL(new Blob([output.value], { type: "text/plain;charset=utf-8" }));
    const link = Object.assign(document.createElement("a"), { href: url, download: "tidytext.txt" });
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    say("Downloaded tidytext.txt");
  };

  const clear = () => {
    input.value = "";
    update();
    input.focus();
  };

  // Files are read on this device only; nothing is uploaded.
  const looksLikeText = (file) =>
    file.type.startsWith("text/") ||
    /\.(txt|md|csv|tsv|html?|json|log|srt|xml)$/i.test(file.name) ||
    file.type === "application/json" ||
    file.type === "";

  const openFile = async (file) => {
    if (!file) return;
    if (!looksLikeText(file)) return say("That file isn't plain text. Try a .txt, .csv or .md file.");
    if (file.size > MAX_FILE_BYTES) return say("That file is over 5 MB. Try a smaller one.");
    try {
      setInput(await file.text(), `Opened ${file.name}`);
    } catch {
      say("That file couldn't be read.");
    }
  };

  input.addEventListener("input", schedule);
  form.addEventListener("input", (event) => {
    if (event.target.matches('input[type="text"]')) update();
  });
  form.addEventListener("change", (event) => {
    if (event.target === fileInput) {
      openFile(fileInput.files[0]);
      fileInput.value = "";
    } else if (event.target !== input && event.target.type !== "text") {
      update();
    }
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    update();
  });
  form.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action === "copy") copy();
    else if (action === "paste") paste();
    else if (action === "open") fileInput.click();
    else if (action === "download") download();
    else if (action === "clear") clear();
  });

  // Drag and drop a text file onto the input box.
  let dragDepth = 0;
  inputPane.addEventListener("dragenter", (event) => {
    if (![...event.dataTransfer.types].includes("Files")) return;
    event.preventDefault();
    dragDepth += 1;
    inputPane.classList.add("is-dropping");
  });
  inputPane.addEventListener("dragover", (event) => {
    if ([...event.dataTransfer.types].includes("Files")) event.preventDefault();
  });
  inputPane.addEventListener("dragleave", () => {
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) inputPane.classList.remove("is-dropping");
  });
  inputPane.addEventListener("drop", (event) => {
    if (!event.dataTransfer.files.length) return;
    event.preventDefault();
    dragDepth = 0;
    inputPane.classList.remove("is-dropping");
    openFile(event.dataTransfer.files[0]);
  });

  update();
}
