// Tiny table filter: one input finds a row by text in any cell.
// Progressive enhancement only — every page reads fully without it.
(function () {
  var inputs = document.querySelectorAll('input[data-filter]');
  Array.prototype.forEach.call(inputs, function (box) {
    var target = document.querySelector(box.getAttribute('data-filter'));
    if (!target) return;
    box.addEventListener('input', function () {
      var q = box.value.toLowerCase();
      var rows = target.querySelectorAll('tbody tr');
      Array.prototype.forEach.call(rows, function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
      });
    });
  });
})();
