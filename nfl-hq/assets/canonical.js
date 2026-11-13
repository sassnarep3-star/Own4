/* Own4 canonical dashboard behaviour: table filtering only. No tracking, no network, no deps. */
(function () {
  "use strict";
  function norm(s) {
    return (s || "").toLowerCase().replace(/\s+/g, " ").trim();
  }
  document.querySelectorAll("[data-filter-for]").forEach(function (input) {
    var id = input.getAttribute("data-filter-for");
    var scope = document.getElementById(id);
    if (!scope) return;
    var rows = Array.prototype.slice.call(scope.querySelectorAll("tbody tr"));
    var count = document.querySelector('[data-filter-count="' + id + '"]');
    var total = rows.length;
    var cache = rows.map(function (r) { return norm(r.textContent); });
    function apply() {
      var q = norm(input.value);
      var shown = 0;
      cache.forEach(function (text, i) {
        var hit = !q || text.indexOf(q) !== -1;
        rows[i].style.display = hit ? "" : "none";
        if (hit) shown++;
      });
      if (count) count.textContent = shown + " of " + total + " rows shown";
    }
    input.addEventListener("input", apply);
    apply();
  });
})();
