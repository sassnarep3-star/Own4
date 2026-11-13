/* Optional progressive enhancement: click a table header to sort, type to filter.
   Nothing on this site depends on JavaScript; every table is complete in the HTML. */
(function () {
  "use strict";
  function textOf(row, i) {
    var c = row.cells[i];
    return c ? (c.dataset.sort || c.textContent.trim()) : "";
  }
  function asNumber(s) {
    var m = s.replace(/[^0-9eE+\-.]/g, "");
    return m === "" ? null : parseFloat(m);
  }
  document.querySelectorAll(".tw > table").forEach(function (table) {
    var head = table.tHead && table.tHead.rows[0];
    if (!head) return;
    Array.prototype.forEach.call(head.cells, function (th, i) {
      th.style.cursor = "pointer";
      th.title = "Sort by this column";
      var dir = 1;
      th.addEventListener("click", function () {
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        rows.sort(function (a, b) {
          var x = textOf(a, i), y = textOf(b, i);
          var nx = asNumber(x), ny = asNumber(y);
          if (nx !== null && ny !== null) return (nx - ny) * dir;
          return x.localeCompare(y) * dir;
        });
        dir = -dir;
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
