"""Visual feedback helpers so headed runs show which element automation interacts with."""

CLICK_HIGHLIGHT_INIT_SCRIPT = """
(() => {
  if (window.__pwClickHighlightInstalled) {
    return;
  }
  window.__pwClickHighlightInstalled = true;

  const style = document.createElement("style");
  style.textContent = `
    .pw-auto-highlight {
      outline: 3px solid #ff6b00 !important;
      outline-offset: 2px !important;
      box-shadow:
        0 0 0 8px rgba(255, 107, 0, 0.35),
        0 0 22px rgba(255, 107, 0, 0.55) !important;
      filter: brightness(1.05);
      transition: outline 80ms ease, box-shadow 80ms ease !important;
      position: relative;
      z-index: 2147483646 !important;
    }
  `;
  (document.head || document.documentElement).appendChild(style);

  const highlight = (target) => {
    const el = target && target.nodeType === 1 ? target : target && target.parentElement;
    if (!el || !el.classList) {
      return;
    }
    el.classList.add("pw-auto-highlight");
    window.setTimeout(() => el.classList.remove("pw-auto-highlight"), 450);
  };

  window.addEventListener("mousedown", (event) => highlight(event.target), true);
  window.addEventListener("click", (event) => highlight(event.target), true);
  window.addEventListener("focusin", (event) => highlight(event.target), true);
})();
"""
