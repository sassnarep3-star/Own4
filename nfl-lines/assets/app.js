
document.addEventListener('input', function (e) {
  if (!e.target.classList.contains('filter')) return;
  var q = e.target.value.toLowerCase();
  var box = e.target.closest('.tools');
  var tbl = box.parentNode.querySelector('table');
  if (!tbl) return;
  var rows = tbl.tBodies[0].rows, shown = 0, total = 0;
  for (var i = 0; i < rows.length; i++) {
    total++;
    var ok = rows[i].textContent.toLowerCase().indexOf(q) >= 0;
    rows[i].style.display = ok ? '' : 'none';
    if (ok) shown++;
  }
  var out = box.querySelector('.small');
  if (out) out.textContent = shown + ' of ' + total + ' rows';
});
