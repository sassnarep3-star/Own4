/* Own4 canonical dashboard — progressive enhancement only.
   Adds a text filter above every large data table. With JavaScript disabled the
   whole site is still readable; nothing on any page depends on this file. */
(function () {
  "use strict";
  function ready(fn) {
    if (document.readyState !== "loading") { fn(); }
    else { document.addEventListener("DOMContentLoaded", fn); }
  }
  ready(function () {
    var tables = document.querySelectorAll(".tw table");
    Array.prototype.forEach.call(tables, function (table, i) {
      var rows = table.tBodies[0] ? table.tBodies[0].rows : null;
      if (!rows || rows.length < 8) { return; }
      var wrap = document.createElement("div");
      wrap.className = "filter";
      var label = document.createElement("label");
      label.setAttribute("for", "filter-" + i);
      label.className = "small muted";
      label.textContent = "Filter rows";
      var input = document.createElement("input");
      input.type = "search";
      input.id = "filter-" + i;
      input.placeholder = "Type to filter this table\u2026";
      var count = document.createElement("span");
      count.className = "count";
      count.setAttribute("aria-live", "polite");
      table.id = "table-" + i;
      function apply() {
        var q = input.value.toLowerCase().trim();
        var shown = 0;
        Array.prototype.forEach.call(rows, function (row) {
          var hit = q === "" || row.textContent.toLowerCase().indexOf(q) !== -1;
          row.style.display = hit ? "" : "none";
          if (hit) { shown++; }
        });
        count.textContent = shown + " of " + rows.length + " rows";
      }
      input.addEventListener("input", apply);
      input.addEventListener("search", apply);
      wrap.appendChild(label);
      wrap.appendChild(input);
      wrap.appendChild(count);
      table.parentNode.parentNode.insertBefore(wrap, table.parentNode);
      apply();
    });
  });
})();
