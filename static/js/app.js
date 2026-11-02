// Instant, in-browser cleaning. The server only formats text when JavaScript is off.
import { apply, stats } from "./transforms.js";

const form = document.querySelector("[data-tool]");

if (form) {
  const input = form.querySelector("[data-input]");
  const output = form.querySelector("[data-output]");
  const before = form.querySelector('[data-stats="before"]');
  const after = form.querySelector('[data-stats="after"]');
  const toast = form.querySelector("[data-toast]");
  const errorBox = form.querySelector(".form-error");
  const fmt = new Intl.NumberFormat("en-US");
  const LABELS = ["characters", "words", "lines"];

  const readOptions = () => ({
    lineBreaks: form.querySelector('input[name="line_breaks"]:checked')?.value ?? "keep",
    textCase: form.elements.case.value,
    flags: [...form.querySelectorAll('input[name="flags"]:checked')].map((el) => el.value),
  });

  const delta = (a, b) => (b > a ? `+${fmt.format(b - a)}` : `−${fmt.format(a - b)}`);

  const label = (key, n) => ` ${key.slice(0, -1)}${n === 1 ? "" : "s"}`;

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

  const update = () => {
    errorBox?.remove();
    const cleaned = apply(input.value, readOptions());
    output.value = cleaned;
    const a = stats(input.value);
    renderStats(before, a, a);
    if (input.value === "") after.replaceChildren();
    else renderStats(after, a, stats(cleaned));
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
    toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2200);
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

  input.addEventListener("input", schedule);
  form.addEventListener("change", (event) => {
    if (event.target !== input) update();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    update();
  });
  form.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action;
    if (action === "copy") copy();
    else if (action === "download") download();
    else if (action === "clear") clear();
  });

  update();
}
