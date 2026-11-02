(() => {
  const menu = document.querySelector('.mobile-menu');
  const nav = document.querySelector('.sidebar');
  if (menu) menu.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    menu.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', e => {
    if (nav && nav.classList.contains('open') && !nav.contains(e.target) && !menu.contains(e.target)) {
      nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false');
    }
  });
  document.querySelectorAll('[data-table-search]').forEach(input => {
    const table = document.getElementById(input.dataset.tableSearch);
    if (!table) return;
    const rows = Array.from(table.tBodies[0]?.rows || []);
    const count = document.querySelector(`[data-count-for="${table.id}"]`);
    const empty = table.parentElement.querySelector('.empty');
    input.addEventListener('input', () => {
      const q = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      rows.forEach(row => { const show = row.textContent.toLocaleLowerCase().includes(q); row.hidden = !show; if(show) visible++; });
      if(count) count.textContent = `${visible} of ${rows.length} entries`;
      if(empty) empty.hidden = visible !== 0;
    });
    if(count) count.textContent = `${rows.length} entries`;
  });
})();
