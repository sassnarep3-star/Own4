// Client-side row filter for any table.filter; no network calls.
(function(){
  var box=document.querySelector('input.search');
  if(!box)return;
  box.addEventListener('input',function(){
    var q=box.value.toLowerCase();
    document.querySelectorAll('table.filter tbody tr').forEach(function(tr){
      tr.style.display=tr.textContent.toLowerCase().indexOf(q)>-1?'':'none';
    });
  });
})();
