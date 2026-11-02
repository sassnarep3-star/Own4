/* Progressive enhancement: filter & sort tables. Content is fully server-rendered. */
(function () {
  var input = document.getElementById('globalFilter');
  var tables = Array.prototype.slice.call(document.querySelectorAll('table.data-table'));
  if (input) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      tables.forEach(function (t) {
        Array.prototype.slice.call(t.tBodies[0].rows).forEach(function (tr) {
          tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
        });
      });
    });
  }
  tables.forEach(function (t) {
    Array.prototype.slice.call(t.tHead.rows[0].cells).forEach(function (th, idx) {
      th.style.cursor = 'pointer';
      th.title = 'Click to sort';
      th.addEventListener('click', function () {
        var body = t.tBodies[0], rows = Array.prototype.slice.call(body.rows);
        var asc = th.dataset.asc !== '1';
        th.dataset.asc = asc ? '1' : '0';
        rows.sort(function (a, b) {
          var x = (a.cells[idx] || {}).textContent || '', y = (b.cells[idx] || {}).textContent || '';
          var nx = parseFloat(x.replace(/[^0-9.\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\-]/g, ''));
          if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
          return asc ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
