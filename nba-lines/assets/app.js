/* Own4 · NBA Line Lab — progressive enhancement only.
   Every table is fully readable with JavaScript disabled. */
(function () {
  "use strict";

  function wire() {
    document.querySelectorAll("[data-table-tools]").forEach(function (tools) {
      var tableId = tools.getAttribute("data-table-tools");
      var table = document.getElementById(tableId);
      if (!table) return;
      var input = tools.querySelector('input[type="search"]');
      var select = tools.querySelector("select");
      var count = tools.querySelector(".count");
      var rows = Array.prototype.slice.call(table.tBodies[0].rows);

      function apply() {
        var q = input ? input.value.trim().toLowerCase() : "";
        var key = select ? select.value : "";
        var shown = 0;
        rows.forEach(function (row) {
          var text = row.textContent.toLowerCase();
          var ok = !q || text.indexOf(q) !== -1;
          if (key === "__blank__") {
            ok = ok && !row.querySelector(".blank");
          }
          row.style.display = ok ? "" : "none";
          if (ok) shown++;
        });
        if (count) count.textContent = shown + " of " + rows.length + " rows";
      }
      if (input) input.addEventListener("input", apply);
      if (select) select.addEventListener("change", apply);
      apply();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire);
  } else {
    wire();
  }
})();
