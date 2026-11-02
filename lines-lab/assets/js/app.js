/* Own4 dashboard renderer. Reads OWN4 (data*.js) and renders sidebar, header, cards, tables. */
(function () {
  "use strict";
  var data = window.OWN4 || {};
  var meta = data.meta || {};
  var pages = data.pages || {};
  var nav = data.nav || [];
  var LINK_PREFIX = ""; // set in render(): "" for root index, "../" for pages/*

  function fixHref(u) {
    return (/^(https?:|#|data:|mailto:)/.test(u) ? u : LINK_PREFIX + u);
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function cellHtml(c) {
    if (c === null || c === undefined || c === "") {
      return '<span class="empty">—</span>';
    }
    if (typeof c === "string") return esc(c);
    var out = "";
    if (c.links && c.links.length) {
      out += c.links.map(function (l) {
        return '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener noreferrer">' + esc(l[0]) + "</a>";
      }).join('<span class="linksep"> · </span>');
      if (c.t) out = esc(c.t) + ' <span class="srclabel">[' + out + "]</span>";
    } else if (c.u) {
      out = '<a href="' + esc(fixHref(c.u)) + '" target="_blank" rel="noopener noreferrer">' + esc(c.t || c.u) + "</a>";
    } else {
      out = esc(c.t || "");
    }
    if (c.flag) {
      out += ' <span class="badge badge-flag" title="Could not be confirmed from an official source — left blank / flagged, never inferred">' + esc(c.flag) + "</span>";
    }
    if (c.badge) {
      out += ' <span class="badge badge-ok">' + esc(c.badge) + "</span>";
    }
    return out;
  }

  function tableHtml(t) {
    var h = "";
    if (t.caption) h += '<h3 class="tbl-caption">' + esc(t.caption) + "</h3>";
    h += '<div class="tbl-wrap"><table class="tbl"><thead><tr>';
    (t.head || []).forEach(function (th) { h += "<th>" + esc(th) + "</th>"; });
    h += "</tr></thead><tbody>";
    (t.rows || []).forEach(function (r) {
      h += "<tr>";
      r.forEach(function (c) { h += "<td>" + cellHtml(c) + "</td>"; });
      h += "</tr>";
    });
    h += "</tbody></table></div>";
    if (t.note) h += '<p class="tbl-note">' + esc(t.note) + "</p>";
    return h;
  }

  function pageHtml(p) {
    var h = "";
    h += '<h1 class="page-title">' + esc(p.title) + "</h1>";
    if (p.intro) h += '<p class="intro">' + esc(p.intro) + "</p>";
    if (p.cards && p.cards.length) {
      h += '<div class="cards">';
      p.cards.forEach(function (c) {
        h += '<div class="card"><div class="card-value">' + esc(c.value) + "</div>" +
             '<div class="card-label">' + esc(c.label) + "</div>" +
             '<div class="card-note">' + cellHtml(c.note) + "</div>" +
             (c.flag ? '<span class="badge badge-flag">' + esc(c.flag) + "</span>" : "") + "</div>";
      });
      h += "</div>";
    }
    (p.tables || []).forEach(function (t) { h += tableHtml(t); });
    return h;
  }

  function render() {
    var pageEl = document.getElementById("page");
    var key = pageEl ? pageEl.getAttribute("data-page") : "home";
    var base = pageEl && pageEl.getAttribute("data-base") === "root" ? "" : "../";
    var prefix = pageEl && pageEl.getAttribute("data-prefix") || base;
    LINK_PREFIX = prefix;

    // sidebar
    var sb = document.getElementById("sidebar");
    if (sb) {
      var h = '<div class="brand"><a href="' + prefix + 'index.html">' + esc(meta.title || "Own4") + "</a></div>";
      h += '<div class="brand-sub">NBA Lines Lab</div>';
      h += '<nav class="nav">';
      nav.forEach(function (n) {
        var active = (n.id === key) ? ' class="active"' : "";
        h += '<a href="' + prefix + n.href + '"' + active + ">" + esc(n.label) + "</a>";
      });
      h += "</nav>";
      h += '<div class="side-foot">Built ' + esc(meta.built || "") + "<br>Branch: <code>" + esc(meta.branch || "") + "</code></div>";
      sb.innerHTML = h;
    }

    // topbar
    var tb = document.getElementById("topbar");
    if (tb) {
      tb.innerHTML = '<div class="top-title">' + esc((pages[key] || {}).title || meta.title || "") + "</div>" +
        '<input id="search" type="search" placeholder="Filter rows in all tables on this page…" aria-label="Filter table rows">';
    }

    // page
    if (pageEl) {
      var p = pages[key];
      pageEl.innerHTML = p ? pageHtml(p) : "<p>Page not found: " + esc(key) + "</p>";
    }

    // footer
    var ft = document.getElementById("footer");
    if (ft) ft.innerHTML = esc(meta.footer || "");

    // search filter
    var si = document.getElementById("search");
    if (si) {
      si.addEventListener("input", function () {
        var q = si.value.trim().toLowerCase();
        document.querySelectorAll("#page table.tbl tbody tr").forEach(function (tr) {
          var txt = tr.textContent.toLowerCase();
          tr.style.display = (!q || txt.indexOf(q) !== -1) ? "" : "none";
        });
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
