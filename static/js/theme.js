// Loaded in <head> (not deferred) so the saved theme applies before the first paint.
(() => {
  const root = document.documentElement;
  const KEY = "tidytext-theme";
  const ORDER = ["auto", "light", "dark"];
  const LABELS = { auto: "Auto", light: "Light", dark: "Dark" };

  const read = () => {
    try {
      return localStorage.getItem(KEY) || "auto";
    } catch {
      return "auto";
    }
  };
  const write = (value) => {
    try {
      localStorage.setItem(KEY, value);
    } catch {
      /* storage unavailable (private mode): the choice lasts for this page only */
    }
  };
  const applyTheme = (value) => {
    if (value === "auto") delete root.dataset.theme;
    else root.dataset.theme = value;
  };

  root.classList.add("js");
  applyTheme(read());

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-theme-toggle]");
    const label = document.querySelector("[data-theme-label]");
    if (!button || !label) return;
    const render = (value) => {
      label.textContent = LABELS[value];
      button.setAttribute("aria-label", `Color theme: ${LABELS[value]}. Change theme`);
    };
    render(read());
    button.addEventListener("click", () => {
      const next = ORDER[(ORDER.indexOf(read()) + 1) % ORDER.length];
      write(next);
      applyTheme(next);
      render(next);
    });
  });
})();
