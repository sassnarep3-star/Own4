(function () {
  "use strict";

  // Live table search across all tables on the active page
  var searchInput = document.getElementById("table-filter");
  var filterStatus = document.getElementById("filter-count");
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      var q = searchInput.value.trim().toLowerCase();
      var rows = document.querySelectorAll("main tbody tr");
      var shown = 0;
      rows.forEach(function (tr) {
        var txt = tr.textContent.toLowerCase();
        var match = !q || txt.indexOf(q) !== -1;
        tr.style.display = match ? "" : "none";
        if (match) shown += 1;
      });
      if (filterStatus) {
        filterStatus.textContent = q
          ? shown + " of " + rows.length + " rows"
          : rows.length + " verified rows";
      }
    });
  }

  // Exact integer-cent SF Rent Board base-rent calculator (never rounds up)
  var baseInput = document.getElementById("calc-base-rent");
  var pctInput = document.getElementById("calc-rate-pct");
  var serviceSelect = document.getElementById("calc-service-method");
  var calcResult = document.getElementById("calc-result");

  function updateCalculator() {
    if (!baseInput || !pctInput || !calcResult) return;
    var baseDollars = parseFloat(baseInput.value);
    var ratePct = parseFloat(pctInput.value);
    var mailDays = serviceSelect && serviceSelect.value === "mail" ? 5 : 0;

    if (isNaN(baseDollars) || baseDollars <= 0 || isNaN(ratePct) || ratePct < 0) {
      calcResult.textContent = "Enter a positive base monthly rent and allowable percentage.";
      return;
    }

    // Exact floor to integer cents so the calculation NEVER rounds up above the cap
    var baseCents = Math.round(baseDollars * 100);
    var rawIncreaseCents = (baseCents * ratePct) / 100.0;
    var increaseCents = Math.floor(rawIncreaseCents + 1e-9);
    var newRentCents = baseCents + increaseCents;
    var baseStatutoryDays = ratePct > 10.0 ? 90 : 30;
    var totalLeadDays = baseStatutoryDays + mailDays;

    function fmt(cents) {
      return "$" + (cents / 100).toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    }

    calcResult.innerHTML =
      "<strong>Exact Allowable Increase (No Rounding Up):</strong> " +
      fmt(increaseCents) +
      "/mo (" +
      ratePct.toFixed(1) +
      "%) &rarr; <strong>New Monthly Base Rent:</strong> " +
      fmt(newRentCents) +
      "/mo · <strong>Minimum Statutory Lead Time:</strong> " +
      totalLeadDays +
      " calendar days (" +
      baseStatutoryDays +
      " days per Civ. Code § 827" +
      (mailDays ? " + 5 days CA mail per CCP § 1013" : " personal service") +
      ").";
  }

  if (baseInput && pctInput) {
    baseInput.addEventListener("input", updateCalculator);
    pctInput.addEventListener("input", updateCalculator);
    if (serviceSelect) serviceSelect.addEventListener("change", updateCalculator);
    document.querySelectorAll("[data-preset-rent]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        baseInput.value = btn.getAttribute("data-preset-rent");
        pctInput.value = btn.getAttribute("data-preset-rate") || "1.6";
        updateCalculator();
      });
    });
    updateCalculator();
  }
})();
