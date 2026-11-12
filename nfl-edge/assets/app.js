/* client-side table filter: progressive enhancement only, site works without JS */
(function () {
  function init() {
    document.querySelectorAll('.tw table').forEach(function (t) {
      var cap = t.querySelector('caption');
      var box = document.createElement('div');
      box.className = 'filterbox';
      box.style.display = 'block';
      var inp = document.createElement('input');
      inp.type = 'search';
      inp.placeholder = 'Filter rows…';
      inp.setAttribute('aria-label', 'Filter table rows');
      box.appendChild(inp);
      (cap ? cap.parentNode.insertBefore(box, cap.nextSibling) : t.parentNode.insertBefore(box, t));
      inp.addEventListener('input', function () {
        var q = inp.value.toLowerCase();
        t.querySelectorAll('tbody tr').forEach(function (tr) {
          tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
        });
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
