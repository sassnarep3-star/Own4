document.querySelectorAll('input.filter').forEach(function(inp){
  var wrap=inp.nextElementSibling; if(!wrap) return; var rows=wrap.querySelectorAll('tbody tr');
  inp.addEventListener('input',function(){var q=inp.value.toLowerCase();
    rows.forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>-1?'':'none';});});
});
