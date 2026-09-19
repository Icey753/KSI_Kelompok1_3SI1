// dcc.Upload and dcc.RadioItems accept no aria-* props, so name them after Dash renders them.
(function () {
  var NAMED = [
    ["#upload-data input[type=file]", "Pilih file JSON atau gambar untuk diunggah", null],
    ["#demo-algorithm", "Algoritma untuk demo", "radiogroup"],
  ];

  // Dash 4 dropdowns are buttons named only by their value; prepend the visible label.
  var LABELLED = [
    ["#file-type-dropdown", "file-type-label"],
    ["#demo-tamper-target", "demo-tamper-target-label"],
  ];

  function apply() {
    LABELLED.forEach(function (entry) {
      var el = document.querySelector(entry[0]);
      if (!el || el.tagName !== "BUTTON") return;
      var current = el.getAttribute("aria-labelledby") || "";
      if (current.indexOf(entry[1]) === -1) el.setAttribute("aria-labelledby", entry[1] + " " + current);
    });
    NAMED.forEach(function (entry) {
      var el = document.querySelector(entry[0]);
      if (!el) return;
      if (!el.getAttribute("aria-label")) el.setAttribute("aria-label", entry[1]);
      if (entry[2] && !el.getAttribute("role")) el.setAttribute("role", entry[2]);
    });
  }

  new MutationObserver(apply).observe(document.documentElement, { childList: true, subtree: true });
  apply();
})();
