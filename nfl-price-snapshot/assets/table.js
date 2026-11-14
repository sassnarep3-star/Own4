// Simple client-side table filtering for the NFL Price Snapshot dashboard.
// Optional enhancement; every page is fully readable without JavaScript.
(function () {
  var inputs = document.querySelectorAll("input.table-filter");
  inputs.forEach(function (input) {
    var table = document.getElementById(input.dataset.table);
    if (!table) return;
    var rows = table.querySelectorAll("tbody tr");
    input.addEventListener("input", function () {
      var term = input.value.toLowerCase();
      rows.forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(term) === -1 ? "none" : "";
      });
    });
  });
})();
