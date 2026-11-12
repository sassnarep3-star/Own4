/* Minimal, dependency-free enhancements: table filtering and a nav toggle. */
(function () {
  "use strict";
  var q = document.getElementById("q");
  var status = document.getElementById("status");
  var table = document.getElementById("qtable");
  if (q && table) {
    var rows = Array.prototype.slice.call(table.querySelectorAll("tbody tr"));
    function apply() {
      var text = (q.value || "").toLowerCase();
      var st = status ? status.value.toLowerCase() : "";
      rows.forEach(function (r) {
        var hay = r.textContent.toLowerCase();
        var okText = !text || hay.indexOf(text) !== -1;
        var okStatus = !st || hay.indexOf(st) !== -1;
        r.style.display = okText && okStatus ? "" : "none";
      });
    }
    q.addEventListener("input", apply);
    if (status) status.addEventListener("change", apply);
  }

  // Make every table sortable by clicking a header (numeric-aware, no dependencies).
  document.querySelectorAll("table").forEach(function (t) {
    var headers = t.querySelectorAll("thead th");
    headers.forEach(function (h, idx) {
      h.style.cursor = "pointer";
      h.title = "Sort by this column";
      var dir = 1;
      h.addEventListener("click", function () {
        var body = t.tBodies[0];
        var rs = Array.prototype.slice.call(body.rows);
        dir = -dir;
        rs.sort(function (a, b) {
          var x = (a.cells[idx] ? a.cells[idx].textContent : "").trim();
          var y = (b.cells[idx] ? b.cells[idx].textContent : "").trim();
          var nx = parseFloat(x.replace(/[+,%]/g, ""));
          var ny = parseFloat(y.replace(/[+,%]/g, ""));
          if (!isNaN(nx) && !isNaN(ny)) return (nx - ny) * dir;
          return x.localeCompare(y) * dir;
        });
        rs.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
