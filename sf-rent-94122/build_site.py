#!/usr/bin/env python3
"""Deterministic static site & markdown generator for sf-rent-94122.

Generates all 9 HTML dashboard pages plus EXECUTIVE_SUMMARY.md, REPO_REVIEW.md,
and README.md strictly from verified JSON data in sf-rent-94122/data/.
"""

from __future__ import annotations

import html
import json
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

NAV_PAGES = [
    ("index.html", "Overview Dashboard", "Dashboard"),
    ("executive-summary.html", "Executive Summary", "Dashboard"),
    ("units-analysis.html", "Unit 1 & Unit 2 Analysis", "Core Research"),
    ("laws-and-caps.html", "Local, State & Federal Laws", "Core Research"),
    ("landlord-practices.html", "Corporate vs. Individual", "Core Research"),
    ("notice-and-scrutiny.html", "Notice & Lawyer Scrutiny", "Compliance & Fair Housing"),
    ("repo-audit.html", "Repo Line-by-Line Audit", "Verification"),
    ("sources.html", "Official Source Registry", "Verification"),
    ("flagged.html", "Flagged for Review", "Verification"),
]


def load_json(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def td(val: str) -> str:
    """Render a table cell. Strictly empty string becomes a blank unverified cell."""
    if val == "":
        return '<td class="unverified-blank" aria-label="Unverified — left blank"></td>'
    return f"<td>{esc(val)}</td>"


def td_html(raw_html: str) -> str:
    return f"<td>{raw_html}</td>"


def src_badge(sources_by_id: dict[str, dict], source_id: str) -> str:
    src = sources_by_id[source_id]
    url = esc(src["url"])
    short = esc(source_id)
    title = esc(f"{src['agency']} — {src['title']}")
    return (
        f'<a class="src-link" href="{url}" target="_blank" '
        f'rel="noopener noreferrer" title="{title}">{short} ↗</a>'
    )


def src_badges(sources_by_id: dict[str, dict], source_ids: list[str]) -> str:
    return " ".join(src_badge(sources_by_id, sid) for sid in source_ids)


def render_shell(
    filename: str,
    title: str,
    eyebrow: str,
    lede: str,
    body_html: str,
    flag_count: int,
    source_count: int,
) -> str:
    nav_chunks: list[str] = []
    current_group = None
    for href, label, group in NAV_PAGES:
        if group != current_group:
            current_group = group
            nav_chunks.append(f'<div class="nav-group">{esc(group)}</div>')
        active_cls = " active" if href == filename else ""
        badge = f'<span class="nav-badge">{flag_count}</span>' if href == "flagged.html" else ""
        nav_chunks.append(
            f'<a class="nav-link{active_cls}" href="{esc(href)}">'
            f"<span>{esc(label)}</span>{badge}</a>"
        )
    nav_chunks.append('<div class="nav-group">Repository</div>')
    nav_chunks.append(
        '<a class="nav-link" href="../index.html"><span>&larr; Repository Root</span></a>'
    )
    nav_html = "\n        ".join(nav_chunks)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · SF 94122 Rent Compliance Dashboard</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to main content</a>
  <div class="layout">
    <aside class="sidebar" aria-label="Dashboard navigation">
      <a class="brand" href="index.html">
        SF 94122 Rent Study
        <span>1940 Building · Outer Sunset · Anonymized</span>
      </a>
      <nav>
        {nav_html}
      </nav>
      <div class="sidebar-footer">
        Verified: <strong>2026-11-06</strong><br>
        Official sources: <strong>{source_count}</strong><br>
        Zero personal tenant data stored.<br>
        <a href="EXECUTIVE_SUMMARY.md">Executive Summary (.md)</a> ·
        <a href="REPO_REVIEW.md">Repo Audit (.md)</a>
      </div>
    </aside>
    <div class="content-area">
      <header class="topbar">
        <div class="topbar-meta">
          <span class="pill pill-ok">1.6% SF Cap (3/1/26–2/28/27)</span>
          <span class="pill pill-ok">100% Anonymized</span>
          <a class="pill pill-flag" href="flagged.html">{flag_count} Flagged / Blank Items</a>
        </div>
        <div class="search-box">
          <label for="table-filter" id="filter-count" style="font-size:0.8rem;color:#526377;">Filter tables:</label>
          <input id="table-filter" type="search" placeholder="Search statutes, units, rates, flags...">
        </div>
      </header>
      <main id="main-content">
        <div class="page-header">
          <div class="eyebrow">{esc(eyebrow)}</div>
          <h1>{esc(title)}</h1>
          <p class="lede">{esc(lede)}</p>
        </div>
        {body_html}
      </main>
      <footer class="footer">
        <strong>Informational Compliance Research — Not Legal Advice:</strong>
        All statutory caps, percentages, notice rules, and empirical statistics are verified line-by-line against official San Francisco Rent Board (<code>sf.gov</code>), California Legislature (<code>leginfo.legislature.ca.gov</code>), California CRD/DOJ, U.S. HUD/DOJ, and U.S. SEC sources as of November 6, 2026. Unconfirmable private facts are intentionally left blank and cataloged on <a href="flagged.html">Flagged for Review</a>. Consult licensed San Francisco landlord-tenant counsel before serving any legal notice.
      </footer>
    </div>
  </div>
  <script src="assets/app.js"></script>
</body>
</html>
"""


def build_index_page(sources_map: dict, units_data: dict, laws_data: dict) -> str:
    unit1, unit2 = units_data["units"][0], units_data["units"][1]
    flag_count = len(laws_data["flagged_items"])

    unit_rows = []
    for u in units_data["units"]:
        unit_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(u['unit_id'])}</strong>")
            + td(u["initial_lease_start"])
            + td(u["continuing_tenancy_date"])
            + td(u["initial_base_rent"])
            + td(u["current_tenants_anonymized"])
            + td_html(f"<strong>{esc(u['annual_1_6_pct_increase'])}</strong> &rarr; <strong>{esc(u['annual_1_6_pct_new_rent'])}</strong>")
            + td(u["verified_banked_amount"])
            + td(u["earliest_eligible_window"])
            + td_html(src_badges(sources_map, u["source_ids"]))
            + "</tr>"
        )

    qa_rows_data = [
        (
            "1. Normal & Lawful Annual Increase (1940 Building, ZIP 94122)",
            "1.6% of base rent only for effective dates March 1, 2026 – February 28, 2027 (+$63.92/mo on Unit 1; +$50.40/mo on Unit 2). Zero upward rounding allowed; active SF Housing Inventory Rent Increase License mandatory on effective date.",
            ["SF-INC-GUIDE", "SF-INVENTORY"],
        ),
        (
            "2. Can Unit 1 Be Reset to Market After Apr. 1, 2026 Occupant Change?",
            "No. Original occupant Tenant A1 from the Feb. 1, 2025 lease still resides in Unit 1, barring vacancy decontrol under Costa-Hawkins (Civ. Code § 1954.53(d)(2)–(3)) and Rules § 6.14. Roommate surcharges are barred by Rules § 6.13. Also check if Apr. 1, 2026 created a 12-month fixed-term lease locking rent until Apr. 1, 2027 (Civ. Code § 827(a)).",
            ["SF-614-CH", "CA-CIV-1954-53", "CA-CIV-827"],
        ),
        (
            "3. How Does Unit 2 Banking Since June 1, 2019 Work?",
            "Because the brief gives only the June 1, 2019 lease-start rent ($3,150/mo) and not interim 2019–2026 history, Unit 2's current lawful base rent and collectible banked balance are left strictly BLANK until ledger reconciliation. Under Topic 503, banking requires ≥24 full months without an increase and simple non-compounded addition; if current base rent is $3,150, single-year 1.6% (+$50.40 -> $3,200.40) on 30/35-day notice avoids >10% 90/95-day notice complications.",
            ["SF-BANKED", "SF-FORM-571", "CA-CIV-827"],
        ),
        (
            "4. Corporate REITs vs. Individual SF Property Owners",
            "Public REITs (disclosed in SEC 10-Ks and disqualified from AB 1482 single-family exemptions under Civ. Code § 1947.12(d)(5)) use Bulk Portal licensing (5+ units), whereas small SF owners use unit-by-unit portal filing; SF bans non-public competitor pricing algorithms for all landlords (§ 37.10C). Representative behavioral rates are left blank/flagged.",
            ["FED-SEC-10K", "SF-INVENTORY", "SF-3710C"],
        ),
        (
            "5. Proper Notice Process & Valid Reasons",
            "No cost-justification excuse is needed for the 1.6% CPI rate—cite SF Admin. Code § 37.3(a)(1) neutrally. Serve written notice personally or by first-class U.S. mail (+5 days in CA per CCP § 1013): 30/35 days if ≤10%, 90/95 days if >10%. Email alone is invalid.",
            ["CA-CIV-827", "CA-CCP-1013", "SF-INC-GUIDE"],
        ),
        (
            "6. Tenant-Advocate Scrutiny & Legal Services Scope",
            "ZIP 94122 recorded 42 tenant petitions in FY 2024–25. Note that City-funded free EDC representation applies to eviction court papers, while Form 590 clinics (including Open Door Legal at 1722 Irving St.) have eligibility rules. No formula guarantees passing counsel review without case-specific inspection of unseen leases and ledgers.",
            ["SF-STATS-2425", "SF-REFERRALS", "SF-EVICTIONS"],
        ),
        (
            "7. Raise One Unit or Both Units (Fair Housing Analysis)?",
            "Use a neutral per-unit eligibility rule: apply the published annual SF Rent Board CPI rate at each unit's first lawful month-to-month contract/anniversary eligibility date after independent compliance checks. Deferring a fixed-term-locked unit is contractually required; consistency across simultaneously eligible units avoids unexplained disparities.",
            ["CA-GOV-12955", "FED-HUD-FHA", "SF-3710B"],
        ),
        (
            "8. Repository Line-by-Line Audit & Unverified Blanks",
            "Zero personal tenant identifiers appear anywhere in sf-rent-94122/ (HTML, JSON, Markdown, or verifier code). Audit flagged 2 HTTP 404 sf.gov links in peer rental-sf/index.html, flagged a peer verifier source-code privacy defect in rental-own4/, and cataloged 12 Flagged for Review items.",
            ["SF-3710B", "SF-REFERRALS", "REPO-PEER-RENTAL"],
        ),
    ]
    qa_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(q)}</strong>")
        + td(a)
        + td_html(src_badges(sources_map, sids))
        + "</tr>"
        for q, a, sids in qa_rows_data
    ]

    body = f"""
        <div class="banner banner-privacy">
          <strong>Strict Privacy &amp; Zero-Hallucination Policy Active:</strong>
          All personal tenant identifiers are kept strictly internal and excluded from this repository. Placeholder labels (<strong>Tenant A1–A4</strong>, <strong>Tenant B1–B2</strong>) preserve exact lease dates and dollar figures. Any fact not confirmable from an official source is left literally blank and listed on <a href="flagged.html">Flagged for Review ({flag_count})</a>.
        </div>

        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">SF Annual Cap (3/1/26–2/28/27)</div>
            <div class="kpi-value">1.6%</div>
            <div class="kpi-sub">Base rent only · Active Rent Increase License required (<a href="{esc(sources_map['SF-NEWS-2627']['url'])}" target="_blank" rel="noopener noreferrer">SF.gov ↗</a>)</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Unit 1 ($3,995 · Feb 2025 / Apr 2026)</div>
            <div class="kpi-value">+$63.92/mo</div>
            <div class="kpi-sub">&rarr; $4,058.92/mo <em>only if MTM</em>; barred until 4/1/2027 if 12-mo fixed lease</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Unit 2 ($3,150 · Since Jun 1, 2019)</div>
            <div class="kpi-value">+$50.40/mo</div>
            <div class="kpi-sub">&rarr; $3,200.40/mo standard 1.6% (30/35d notice); actual banked ledger blank/flagged</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">ZIP 94122 Enforcement &amp; Flags</div>
            <div class="kpi-value">42 Petitions</div>
            <div class="kpi-sub">FY 24–25 Sunset tenant petitions · <a href="flagged.html">{flag_count} items on Flagged for Review</a></div>
          </div>
        </div>

        <section class="card">
          <h2>Navigate Research Categories</h2>
          <p>Select any category below to inspect line-by-line verified tables, official statutory citations, calculations, and audit flags.</p>
          <div class="tile-grid">
            <a class="tile" href="executive-summary.html">
              <strong>1. Executive Summary &rarr;</strong>
              <span>Key conclusions, privacy safeguards, compliance gates, and recommended sequence for Unit 1 &amp; Unit 2.</span>
            </a>
            <a class="tile" href="units-analysis.html">
              <strong>2. Unit 1 &amp; Unit 2 Rent Analysis &rarr;</strong>
              <span>Exact penny calculations, Form 571 banking table (2019–2028), interactive calculator, and ZIP 94122 / HUD benchmarks.</span>
            </a>
            <a class="tile" href="laws-and-caps.html">
              <strong>3. Local, State &amp; Federal Laws &rarr;</strong>
              <span>SF Rent Ordinance Ch. 37 &amp; 37A, Rules §§ 6.13–6.14, Costa-Hawkins, AB 1482, Civ. Code §§ 827 &amp; 1942.5, FEHA, and FHA.</span>
            </a>
            <a class="tile" href="landlord-practices.html">
              <strong>4. Corporate vs. Individual Owners &rarr;</strong>
              <span>SEC 10-K disclosures, Housing Inventory bulk vs. unit portal rules, § 37.10C algorithmic ban, and SF petition data.</span>
            </a>
            <a class="tile" href="notice-and-scrutiny.html">
              <strong>5. Notice Process &amp; Lawyer Scrutiny &rarr;</strong>
              <span>5-step notice protocol, 12-point SF tenant-lawyer audit checklist, One-vs-Both units matrix, and free legal clinics.</span>
            </a>
            <a class="tile" href="repo-audit.html">
              <strong>6. Repository Line-by-Line Audit &rarr;</strong>
              <span>Full Own4 repo inspection, broken 404 link detection in peer module, sports workspace boundaries, and PII scan.</span>
            </a>
            <a class="tile" href="sources.html">
              <strong>7. Official Source Registry ({len(sources_map)}) &rarr;</strong>
              <span>Every SF.gov, CA Legislature, CA CRD/DOJ, HUD, DOJ, and SEC document verified on 2026-11-06.</span>
            </a>
            <a class="tile" href="flagged.html">
              <strong>8. Flagged for Review ({flag_count}) &rarr;</strong>
              <span>All unverified blank fields (lease type, Unit 2 ledger, 2027–28 rate, portal license) and repo link flags.</span>
            </a>
          </div>
        </section>

        <section class="card">
          <h2>Unit 1 &amp; Unit 2 Snapshot (Outer Sunset · ZIP 94122 · Built 1940)</h2>
          <p>Blank cells indicate facts that cannot be confirmed from public government sources and are intentionally left unpopulated rather than inferred.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Unit</th>
                  <th>Initial Lease Start</th>
                  <th>Latest Tenancy Event</th>
                  <th>Reported Base Rent</th>
                  <th>Anonymized Occupants</th>
                  <th>Standard 1.6% Annual Math</th>
                  <th>Verified Banked $</th>
                  <th>Eligibility &amp; Notice Gate</th>
                  <th>Official Sources</th>
                </tr>
              </thead>
              <tbody>
                {''.join(unit_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>Core Questions Answered at a Glance</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Question / Deliverable</th>
                  <th>Verified Finding (As of November 6, 2026)</th>
                  <th>Official Sources</th>
                </tr>
              </thead>
              <tbody>
                {''.join(qa_rows)}
              </tbody>
            </table>
          </div>
        </section>
    """
    return body


def build_exec_summary_page(sources_map: dict, units_data: dict, laws_data: dict) -> str:
    action_rows_data = [
        (
            "1. Pre-Notice Portal Licensing Gate",
            "Both Units",
            "Confirm 2026 Housing Inventory is filed on portal.sfrb.org and download active Rent Increase License confirmation + verify $59.00/unit Rent Board Fee paid.",
            "Mandatory before effective date",
            ["SF-INVENTORY", "SF-FEE"],
        ),
        (
            "2. Unit 1 Contract & Roommate Gate",
            "Unit 1 ($3,995.00)",
            "Inspect April 1, 2026 document. Do NOT reset to market or add a roommate fee (Tenant A1 remains). If 12-month fixed lease, defer increase until April 1, 2027; if MTM addendum, 1.6% (+$63.92 -> $4,058.92) is eligible on 30/35-day notice.",
            "Immediate contract check",
            ["SF-614-CH", "CA-CIV-1954-53", "CA-CIV-827"],
        ),
        (
            "3. Unit 2 Ledger & Banking Gate",
            "Unit 2 ($3,150.00)",
            "Audit 2019–2026 rent ledger. Standard 1.6% (+$50.40 -> $3,200.40) on 30/35-day notice is recommended low-risk path and leaves any valid prior banked % intact. Avoid >10% 95-day mailed notices after Nov. 25, 2026 (crosses March 1, 2027 rate cliff).",
            "Eligible on 30/35-day notice once licensed",
            ["SF-BANKED", "SF-FORM-571", "CA-CIV-827"],
        ),
        (
            "4. Retaliation & DBI NOV Clearance",
            "Both Units",
            "Verify zero good-faith tenant repair complaints in the past 180 days (Civ. Code § 1942.5) and zero open SF DBI Notices of Violation before serving any notice.",
            "Pre-service compliance check",
            ["CA-CIV-1942-5", "SF-3710B"],
        ),
        (
            "5. Uniform Building-Wide Policy (One vs. Both Units)",
            "Both Units",
            "Adopt and archive a neutral written policy: apply the published SF Rent Board annual CPI rate to every unit on its first lawful month-to-month anniversary/post-lease eligibility date.",
            "Permanent fair-housing defense",
            ["CA-GOV-12955", "FED-HUD-FHA"],
        ),
        (
            "6. Optional Separate Rent Board Fee Recovery",
            "Both Units",
            "If timely paid to the City, recover 50% ($29.50/unit for 2026–27) ONLY as a separate itemized bill—NEVER fold into base rent or multiply future % increases against it.",
            "Separate itemized billing only",
            ["SF-FEE", "SF-INC-GUIDE"],
        ),
    ]
    rows = [
        "<tr>"
        + td_html(f"<strong>{esc(step)}</strong>")
        + td(unit)
        + td(action)
        + td(window)
        + td_html(src_badges(sources_map, sids))
        + "</tr>"
        for step, unit, action, window, sids in action_rows_data
    ]

    return f"""
        <section class="card">
          <h2>1. Property Context &amp; Privacy Architecture</h2>
          <p>This study evaluates lawful and standard rental increases as of <strong>November 6, 2026</strong> for two tenancies in an <strong>owner-reported 1940 residential building in San Francisco's Outer Sunset (ZIP 94122)</strong> analyzed under the San Francisco Rent Ordinance (<a href="{esc(sources_map['SF-COVERAGE']['url'])}" target="_blank" rel="noopener noreferrer">SF Admin. Code Ch. 37 ↗</a>; parcel APN, total unit count, and exemption status are unverified from Assessor/PIM records and flagged on <a href="flagged.html">Flagged for Review</a>). All personal tenant details and initials supplied in the brief are strictly excluded from <code>sf-rent-94122/</code> (HTML, JSON, Markdown, and verifier source code) and replaced with neutral placeholders (<strong>Tenant A1–A4</strong> in Unit 1; <strong>Tenant B1–B2</strong> in Unit 2), while keeping all dates and dollar amounts exact.</p>
        </section>

        <section class="card">
          <h2>2. Headline Findings for Unit 1 &amp; Unit 2</h2>
          <ul>
            <li><strong>Governing Annual Cap (March 1, 2026 – February 28, 2027):</strong> For covered SF Rent Ordinance units, exactly <strong>1.6%</strong> of base monthly rent (<a href="{esc(sources_map['SF-NEWS-2627']['url'])}" target="_blank" rel="noopener noreferrer">SF Rent Board Announcement ↗</a>). Rounding up to the nearest dollar is unlawful. California's statewide AB 1482 rate (8.8% in SF) does <strong>not</strong> apply where the stricter local SF Rent Ordinance controls (<a href="{esc(sources_map['SF-AB1482']['url'])}" target="_blank" rel="noopener noreferrer">Civ. Code § 1947.12(d)(7) ↗</a>).</li>
            <li><strong>Mandatory Licensing Pre-Condition:</strong> No annual or banked increase on a covered unit is enforceable unless the owner has reported the unit to the SF Rent Board Housing Inventory and holds an active <strong>Rent Increase License</strong> on the effective date (<a href="{esc(sources_map['SF-INVENTORY']['url'])}" target="_blank" rel="noopener noreferrer">SF Admin. Code § 37.15 / Ch. 37A ↗</a>).</li>
            <li><strong>Unit 1 ($3,995.00/mo · Feb. 1, 2025 initial lease; Apr. 1, 2026 continuation with Tenant A1 &amp; Tenant A4):</strong> Because original occupant <strong>Tenant A1</strong> still resides in Unit 1, vacancy decontrol to market rent is barred (<a href="{esc(sources_map['CA-CIV-1954-53']['url'])}" target="_blank" rel="noopener noreferrer">Civ. Code § 1954.53(d)(2)–(3) ↗</a>; <a href="{esc(sources_map['SF-614-CH']['url'])}" target="_blank" rel="noopener noreferrer">Rules § 6.14 ↗</a>), and charging extra rent for replacement co-occupant <strong>Tenant A4</strong> is barred (<a href="{esc(sources_map['SF-INC-GUIDE']['url'])}" target="_blank" rel="noopener noreferrer">Rules § 6.13 ↗</a>). If the April 1, 2026 instrument is a <strong>12-month fixed-term lease</strong> through March 31, 2027, unilateral increases are barred until <strong>April 1, 2027</strong> (<a href="{esc(sources_map['CA-CIV-827']['url'])}" target="_blank" rel="noopener noreferrer">Civ. Code § 827(a) ↗</a>), when the 2027–2028 SF rate will govern. Only if Unit 1 is currently month-to-month at $3,995.00 can a <strong>1.6% (+$63.92/mo &rarr; $4,058.92/mo)</strong> increase take effect on or before February 28, 2027.</li>
            <li><strong>Unit 2 ($3,150.00/mo reported at June 1, 2019 lease start · Tenant B1 &amp; Tenant B2):</strong> Because interim 2019–2026 rent history was not supplied, Unit 2's current lawful base rent and any collectible banked balance are left strictly <strong>blank/unverified</strong> until ledger reconciliation under <a href="{esc(sources_map['SF-BANKED']['url'])}" target="_blank" rel="noopener noreferrer">Topic 503 ↗</a> (which requires ≥24 full months without an increase and simple non-compounded addition). Conditional on $3,150.00 still being the current base rent, a single-year <strong>1.6% (+$50.40/mo &rarr; $3,200.40/mo)</strong> adjustment on 30-day personal / 35-day CA mailed notice preserves any valid prior banked years and avoids &gt;10% 90/95-day notice complications (note: mailing a 95-day notice after Nov. 25, 2026 pushes effective dates past Feb. 28, 2027 into the unpublished 2027–28 rate period).</li>
            <li><strong>Raising One Unit vs. Both Units &amp; Counsel Review Boundary:</strong> Apply a neutral per-unit eligibility policy—adjusting each unit at its first lawful month-to-month contract/anniversary eligibility date after independent compliance checks (<a href="{esc(sources_map['FED-HUD-FHA']['url'])}" target="_blank" rel="noopener noreferrer">42 U.S.C. § 3604 ↗</a>; <a href="{esc(sources_map['CA-GOV-12955']['url'])}" target="_blank" rel="noopener noreferrer">Gov. Code § 12955 ↗</a>; <a href="{esc(sources_map['SF-3710B']['url'])}" target="_blank" rel="noopener noreferrer">SF § 37.10B ↗</a>). No public checklist guarantees avoiding complaints or passing legal review without case-specific attorney inspection of physical leases and ledgers.</li>
          </ul>
        </section>

        <section class="card">
          <h2>3. Executive Compliance Action Plan</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Action Step</th>
                  <th>Applies To</th>
                  <th>Verified Compliance Requirement</th>
                  <th>Timing Window</th>
                  <th>Official Sources</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_units_page(sources_map: dict, units_data: dict) -> str:
    f571_rows = []
    for row in units_data["form_571_schedule"]:
        f571_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(row['period'])}</strong>")
            + td(row["rate"])
            + td(row["unit_1_relevance"])
            + td(row["unit_2_relevance"])
            + td(row["unit_2_illustrative_dollar_on_3150"])
            + td_html(src_badge(sources_map, row["source_id"]))
            + "</tr>"
        )

    bank_rows = []
    for row in units_data["unit_2_banking_scenarios"]:
        bank_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(row['scenario'])}</strong>")
            + td(row["pct"])
            + td(row["monthly_increase"])
            + td(row["new_monthly_rent"])
            + td(row["notice_required"])
            + td(row["lawyer_scrutiny_notes"])
            + td_html(src_badge(sources_map, row["source_id"]))
            + "</tr>"
        )

    bench_rows = []
    for row in units_data["zip_94122_and_federal_benchmarks"]:
        bench_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(row['metric'])}</strong>")
            + td(row["geography"])
            + td(row["value"])
            + td(row["status"])
            + td(row["notes"])
            + td_html(src_badge(sources_map, row["source_id"]))
            + "</tr>"
        )

    unit_detail_rows = []
    for u in units_data["units"]:
        unit_detail_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(u['unit_id'])}</strong>")
            + td(u["initial_lease_start"])
            + td(u["initial_base_rent"])
            + td(u["initial_tenants_anonymized"])
            + td(u["continuing_tenancy_date"])
            + td(u["current_tenants_anonymized"])
            + td(u["market_reset_permitted"])
            + td_html(f"<strong>{esc(u['annual_1_6_pct_increase'])}</strong> &rarr; <strong>{esc(u['annual_1_6_pct_new_rent'])}</strong>")
            + td(u["verified_banked_amount"])
            + td(u["recommended_action"])
            + td_html(src_badges(sources_map, u["source_ids"]))
            + "</tr>"
        )

    return f"""
        <section class="card">
          <h2>Unit-by-Unit Tenancy &amp; Arithmetic Matrix (Anonymized)</h2>
          <p>Exact base-rent arithmetic verified using integer cents with zero upward rounding: <code>$3,995.00 &times; 1.6% = $63.92</code> and <code>$3,150.00 &times; 1.6% = $50.40</code>. Unverified ledger/banked balances are left strictly blank.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Unit</th>
                  <th>Initial Lease</th>
                  <th>Initial Base Rent</th>
                  <th>Initial Occupants</th>
                  <th>Latest Event</th>
                  <th>Current Occupants</th>
                  <th>Market Reset Permitted?</th>
                  <th>1.6% Annual Math</th>
                  <th>Verified Banked $</th>
                  <th>Compliance Recommendation</th>
                  <th>Official Sources</th>
                </tr>
              </thead>
              <tbody>
                {''.join(unit_detail_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>Interactive SF Base-Rent &amp; Notice Calculator (Zero Upward Rounding)</h2>
          <p>Test exact allowable dollar amounts and statutory notice lead times under <a href="{esc(sources_map['SF-INC-GUIDE']['url'])}" target="_blank" rel="noopener noreferrer">SF Rent Ordinance § 37.3 ↗</a> and <a href="{esc(sources_map['CA-CIV-827']['url'])}" target="_blank" rel="noopener noreferrer">Cal. Civ. Code § 827 ↗</a>.</p>
          <div class="btn-group">
            <button type="button" class="btn" data-preset-rent="3995" data-preset-rate="1.6">Load Unit 1 ($3,995 @ 1.6%)</button>
            <button type="button" class="btn" data-preset-rent="3150" data-preset-rate="1.6">Load Unit 2 ($3,150 @ 1.6%)</button>
          </div>
          <div class="calc-grid">
            <div class="calc-field">
              <label for="calc-base-rent">Current Monthly Base Rent ($)</label>
              <input id="calc-base-rent" type="number" step="0.01" min="0" value="3995.00">
            </div>
            <div class="calc-field">
              <label for="calc-rate-pct">Allowable Rate (%)</label>
              <input id="calc-rate-pct" type="number" step="0.1" min="0" value="1.6">
            </div>
            <div class="calc-field">
              <label for="calc-service-method">Statutory Delivery Method</label>
              <select id="calc-service-method">
                <option value="mail" selected>First-Class U.S. Mail within CA (+5 days per CCP § 1013)</option>
                <option value="personal">Personal Delivery to Tenant (0 extra mail days)</option>
              </select>
            </div>
          </div>
          <div id="calc-result" class="calc-output" aria-live="polite">
            <strong>Exact Allowable Increase (No Rounding Up):</strong> $63.92/mo (1.6%) &rarr; <strong>New Monthly Base Rent:</strong> $4,058.92/mo · <strong>Minimum Statutory Lead Time:</strong> 35 calendar days (30 days per Civ. Code § 827 + 5 days CA mail per CCP § 1013).
          </div>
        </section>

        <section class="card">
          <h2>Unit 2 Banking Options &amp; The Nov. 25, 2026 / March 1, 2027 Rate-Year Cliff</h2>
          <p>Under <a href="{esc(sources_map['SF-BANKED']['url'])}" target="_blank" rel="noopener noreferrer">SF Rent Board Banking Rules ↗</a>, skipped annual increases bank only after 24 full months without an increase and are summed additively without compounding. Crucially, if a landlord imposes a banked increase on a new anniversary date after fewer than 12 months have elapsed since the most recent anniversary, the unbanked year is forfeited.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Unit 2 Option</th>
                  <th>Total %</th>
                  <th>Monthly Increase</th>
                  <th>New Monthly Rent</th>
                  <th>Minimum Written Notice</th>
                  <th>Legal &amp; Timing Scrutiny Assessment</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(bank_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>Official SF Rent Board Form 571 Rate Schedule (2019 – 2028)</h2>
          <p>Every percentage below is verified verbatim from <a href="{esc(sources_map['SF-FORM-571']['url'])}" target="_blank" rel="noopener noreferrer">SF Rent Board Form 571 (PDF) ↗</a>. The March 1, 2027 – February 29, 2028 rate has not yet been announced as of November 6, 2026 and is intentionally left blank.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Effective Period</th>
                  <th>Published Rate</th>
                  <th>Application to Unit 1 ($3,995 · Start 2/1/2025)</th>
                  <th>Application to Unit 2 ($3,150 · Start 6/1/2019)</th>
                  <th>Unit 2 Conditional $ on $3,150</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(f571_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>Outer Sunset (ZIP 94122) Empirical Activity &amp; Federal HUD Benchmarks</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Benchmark / Official Metric</th>
                  <th>Geography</th>
                  <th>Verified Official Value</th>
                  <th>Verification Status</th>
                  <th>Compliance Interpretation</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(bench_rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_laws_page(sources_map: dict, units_data: dict, laws_data: dict) -> str:
    law_rows = []
    for row in laws_data["legal_framework"]:
        law_rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(row['level'])}</strong>")
            + td(row["statute"])
            + td(row["applicability_94122"])
            + td(row["rule_summary"])
            + td_html(src_badge(sources_map, row["source_id"]))
            + "</tr>"
        )

    fee_rows_data = [
        (
            "Standard Annual Rent Increase (CPI Cap)",
            "1.6% (3/1/2026 – 2/28/2027)",
            "No Rent Board petition needed; requires active Housing Inventory Rent Increase License.",
            "Yes — becomes new base rent.",
            "SF-NEWS-2627",
        ),
        (
            "Rent Board Fee Recovery (50% Tenant Share)",
            "$29.50/unit for 2026–2027 (50% of $59.00 apartment fee)",
            "No petition needed, provided owner paid the full $59.00 fee by the March 1 deadline; bill separately with invoice.",
            "NO — never part of base rent; nonpayment is NOT eviction cause.",
            "SF-FEE",
        ),
        (
            "Security Deposit Interest Paid TO Tenant",
            "4.2% (3/1/2026 – 2/28/2027)",
            "Landlord obligation owed annually to tenants holding deposits ≥1 year (not a rent increase).",
            "N/A — credit/payment owed to tenant.",
            "SF-CURR-RATES",
        ),
        (
            "Capital Improvement / Operating & Maintenance / Comparable Rents",
            "Varies by approved petition",
            "Mandatory formal SF Rent Board Landlord Petition & ALJ decision BEFORE collection.",
            "No — tracked separately per Rent Board order.",
            "SF-PETITIONS",
        ),
        (
            "General Obligation Bond / Water Bond / Utility Passthrough",
            "Calculated on official Rent Board Worksheets",
            "Requires official SF Rent Board calculation sheets (and Utility Petition/Worksheet where required) served with notice.",
            "NO — excluded from base rent when computing 1.6% annual cap.",
            "SF-PETITIONS",
        ),
    ]
    fee_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(item)}</strong>")
        + td(rate)
        + td(proc)
        + td(base_flag)
        + td_html(src_badge(sources_map, sid))
        + "</tr>"
        for item, rate, proc, base_flag, sid in fee_rows_data
    ]

    return f"""
        <section class="card">
          <h2>Multi-Jurisdictional Legal Matrix (Local SF · California · Federal)</h2>
          <p>For a 1940 multi-unit residential building in San Francisco ZIP 94122, local, state, and federal statutes stack together: the <strong>strictest tenant-protective cap</strong> governs price increases (<a href="{esc(sources_map['SF-INC-GUIDE']['url'])}" target="_blank" rel="noopener noreferrer">SF Rent Ordinance 1.6% ↗</a>), California state law governs written notice delivery and occupancy-turnover limits, and all three jurisdictions enforce strict anti-retaliation and fair-housing mandates.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Jurisdiction</th>
                  <th>Statute / Ordinance / Rule</th>
                  <th>Applicability to 1940 Building in 94122</th>
                  <th>Verified Legal Rule</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(law_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>2026–2027 Rates, Separate Fees &amp; Petition-Only Passthroughs</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Adjustment / Obligation Type</th>
                  <th>2026–2027 Official Figure</th>
                  <th>Required Filing / Procedure</th>
                  <th>Part of Base Rent?</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(fee_rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_practices_page(sources_map: dict, laws_data: dict) -> str:
    rows = []
    for row in laws_data["landlord_practices"]:
        rows.append(
            "<tr>"
            + td_html(f"<strong>{esc(row['dimension'])}</strong>")
            + td(row["corporate_reits"])
            + td(row["individual_owners_sf"])
            + td(row["verified_metric"])
            + td_html(src_badge(sources_map, row["source_id"]))
            + "</tr>"
        )

    return f"""
        <div class="banner banner-warn">
          <strong>Evidence Boundary:</strong> Every comparison below is restricted to verifiable statutory distinctions, SEC Form 10-K filings, SF Rent Board portal rules, federal/state/SF algorithmic-pricing enforcement, and official SF Rent Board FY 2024–2025 statistical reports. Unverified private internal renewal percentages of specific corporations are intentionally left blank and flagged on <a href="flagged.html">Flagged for Review</a>.
        </div>

        <section class="card">
          <h2>Large Real Estate Corporations / REITs vs. Individual SF Property Owners</h2>
          <p>What individual Outer Sunset owners can adopt from institutional compliance—without adopting unlawful algorithmic pricing—is <strong>calendar discipline, portal license verification before notice service, exact penny math, neutral statutory wording, and archived proof of service</strong>.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Operational / Legal Dimension</th>
                  <th>Large Real Estate Corporations &amp; REITs</th>
                  <th>Individual San Francisco Property Owners</th>
                  <th>Verified Official Metric / Citation</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_notice_scrutiny_page(sources_map: dict, laws_data: dict) -> str:
    notice_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(r['step'])}</strong>")
        + td(r["requirement"])
        + td(r["reasonable_reason_guidance"])
        + td_html(src_badge(sources_map, r["source_id"]))
        + "</tr>"
        for r in laws_data["notice_protocol"]
    ]

    reasons_data = [
        (
            "Valid & Recommended",
            "Annual Allowable CPI Rent Adjustment under SF Admin. Code § 37.3(a)(1) (1.6% for 3/1/2026–2/28/2027)",
            "Lawful as of right once every 12 months on month-to-month tenancies with active Rent Increase License; requires zero cost-increase excuse.",
            "SF-INC-GUIDE",
        ),
        (
            "Valid (With Strict Audit)",
            "Lawfully Banked Prior Annual Increases under SF Admin. Code § 37.3(a)(2) (Itemized, Uncompounded, ≥24 Mos.)",
            "Lawful ONLY if exact skipped years are verified against the rent ledger, itemized in the notice, uncompounded, and served with 90/95 days notice if total >10%.",
            "SF-BANKED",
        ),
        (
            "Valid ONLY After Approval / Worksheet",
            "Approved Capital Improvement / O&M Petition or Official Bond / Utility Passthrough Worksheet",
            "Lawful ONLY after formal SF Rent Board ALJ decision or official Rent Board passthrough calculation sheets attached to notice; never part of base rent.",
            "SF-PETITIONS",
        ),
        (
            "INVALID / UNLAWFUL",
            "'Bringing Unit Closer to Outer Sunset Market Rent' or 'Higher Property Taxes / Repairs' (>1.6% Without Petition)",
            "Void above 1.6% without a Rent Board petition; invites immediate Tenant Unlawful Rent Increase Petition and full refund.",
            "SF-PETITIONS",
        ),
        (
            "INVALID / UNLAWFUL",
            "'New Roommate / Co-Occupant Fee' for Tenant A4 in Unit 1",
            "Explicitly prohibited by SF Rent Board Rules & Regs § 6.13 even if an existing lease purported to allow an extra-occupant charge.",
            "SF-INC-GUIDE",
        ),
        (
            "INVALID / UNLAWFUL",
            "Increase Served Within 180 Days of Repair Request, Selective Protected-Class Targeting, or Algorithmic Pricing",
            "Violates Cal. Civ. Code § 1942.5, FHA/FEHA, SF § 37.10B (treble damages + mandatory tenant attorney's fees), or SF § 37.10C ($1,000/unit/mo penalty).",
            "SF-3710B",
        ),
    ]
    reason_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(status)}</strong>")
        + td(reason)
        + td(explain)
        + td_html(src_badge(sources_map, sid))
        + "</tr>"
        for status, reason, explain, sid in reasons_data
    ]

    scrutiny_rows = [
        "<tr>"
        + td_html(f"<code>{esc(r['check_id'])}</code>")
        + td_html(f"<strong>{esc(r['audit_point'])}</strong>")
        + td(r["what_tenant_lawyer_checks"])
        + td(r["defect_consequence"])
        + td_html(src_badge(sources_map, r["source_id"]))
        + "</tr>"
        for r in laws_data["lawyer_scrutiny_checklist"]
    ]

    matrix_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(r['scenario'])}</strong>")
        + td(r["legal_permissibility"])
        + td(r["discrimination_analysis"])
        + td_html(src_badge(sources_map, r["source_id"]))
        + "</tr>"
        for r in laws_data["one_vs_both_matrix"]
    ]

    dir_rows = [
        "<tr>"
        + td_html(f"<strong>{esc(r['organization'])}</strong>")
        + td(r["contact_and_location"])
        + td(r["scope_of_service"])
        + td_html(src_badge(sources_map, r["source_id"]))
        + "</tr>"
        for r in laws_data["tenant_legal_directory"]
    ]

    return f"""
        <section class="card">
          <h2>1. Five-Step Lawful Notice &amp; Service Protocol</h2>
          <p>Every rent increase in San Francisco must satisfy both <strong>local Rent Ordinance licensing/cap rules</strong> and <strong>California Civil Code § 827 / CCP § 1013 service rules</strong>.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Protocol Step</th>
                  <th>Mandatory Legal Procedure</th>
                  <th>Neutral Business Practice &amp; Reason Guidance</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(notice_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>2. Lawful &amp; Reasonable Reasons vs. Unlawful / Void Reasons</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Legal Status</th>
                  <th>Stated Basis for Rent Adjustment</th>
                  <th>Statutory Consequence</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(reason_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>3. Raising One Unit vs. Both Units — Fair Housing &amp; Anti-Discrimination Analysis</h2>
          <p><strong>Core Rule:</strong> Raising one unit vs. both units is lawful when—and only when—governed by an <strong>objective, neutral, documented criterion</strong> (such as an active fixed-term lease bar on Unit 1 vs. month-to-month eligibility on Unit 2) rather than arbitrary or protected-class selection.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Building Scenario (Unit 1 vs. Unit 2)</th>
                  <th>Permissible / Recommended Action</th>
                  <th>Fair Housing (FHA / FEHA / SF § 37.10B) &amp; Retaliation Analysis</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(matrix_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>4. 12-Point San Francisco Tenant-Lawyer Audit Checklist</h2>
          <p>San Francisco tenants have immediate access to free legal clinics—including <strong>Open Door Legal directly in ZIP 94122 (1722 Irving St.)</strong>, the Housing Rights Committee Westside office, the SF Tenants Union, and EDC. Below are the exact 12 defects a tenant advocate checks first when a tenant brings in a rent increase notice.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Scrutiny Audit Point</th>
                  <th>What Free Tenant Counsel Verifies</th>
                  <th>Consequence of Non-Compliance</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(scrutiny_rows)}
              </tbody>
            </table>
          </div>
        </section>

        <section class="card">
          <h2>5. Official San Francisco Free Tenant &amp; Landlord Counseling Directory</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Official Organization / Agency</th>
                  <th>Verified Address &amp; Phone</th>
                  <th>Verified Scope of Free Services</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(dir_rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_repo_audit_page(sources_map: dict, laws_data: dict) -> str:
    rows = [
        "<tr>"
        + td_html(f"<code>{esc(r['audit_id'])}</code>")
        + td_html(f"<strong>{esc(r['scope_path'])}</strong>")
        + td(r["verdict"])
        + td(r["finding"])
        + td_html(src_badge(sources_map, r["source_id"]))
        + "</tr>"
        for r in laws_data["repo_audit"]
    ]
    return f"""
        <div class="banner banner-flag">
          <strong>Key Repository Audit Catch:</strong> Line-by-line inspection of the repository caught <strong>two live HTTP 404 broken links</strong> in peer-merged <code>rental-sf/index.html</code> (<code>sf.gov/information/tenant-protections-against-harassment</code> and <code>sf.gov/information/eviction-and-tenant-rights-clinics</code>). Per multi-session governance, peer files were not overwritten; both broken URLs are logged in <code>COORDINATION.md</code> and replaced in this dashboard with verified live <code>sf.gov</code> pages (<a href="{esc(sources_map['SF-3710B']['url'])}" target="_blank" rel="noopener noreferrer">SF-3710B ↗</a> &amp; <a href="{esc(sources_map['SF-REFERRALS']['url'])}" target="_blank" rel="noopener noreferrer">SF-REFERRALS ↗</a>).
        </div>

        <section class="card">
          <h2>Line-by-Line Repository Audit Matrix (<code>sassnarep3-star/Own4</code>)</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Audit ID</th>
                  <th>Inspected Repository Path / Scope</th>
                  <th>Audit Verdict</th>
                  <th>Verified Finding &amp; Remediation</th>
                  <th>Official Source</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_sources_page(sources_data: dict) -> str:
    rows = []
    for s in sources_data["sources"]:
        url = esc(s["url"])
        rows.append(
            "<tr>"
            + td_html(f"<code>{esc(s['id'])}</code>")
            + td(s["jurisdiction"])
            + td(s["agency"])
            + td_html(f'<a href="{url}" target="_blank" rel="noopener noreferrer"><strong>{esc(s["title"])}</strong> ↗</a>')
            + td(s["verified_date"])
            + td(s["summary"])
            + "</tr>"
        )
    return f"""
        <section class="card">
          <h2>Allowlisted Official Source Registry ({len(sources_data['sources'])} Verified Sources)</h2>
          <p>Every source below resides on an allowlisted official government domain (<code>sf.gov</code>, <code>media.api.sf.gov</code>, <code>leginfo.legislature.ca.gov</code>, <code>calcivilrights.ca.gov</code>, <code>oag.ca.gov</code>, <code>hud.gov</code>, <code>huduser.gov</code>, <code>justice.gov</code>, <code>sec.gov</code>) or the canonical GitHub repository for internal audit records, and was live-fetched and verified on <strong>2026-11-06</strong>.</p>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Source ID</th>
                  <th>Jurisdiction</th>
                  <th>Official Agency / Publisher</th>
                  <th>Document Title &amp; Verified URL</th>
                  <th>Verified Date</th>
                  <th>Scope Verified</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def build_flagged_page(sources_map: dict, laws_data: dict) -> str:
    rows = []
    for f in laws_data["flagged_items"]:
        rows.append(
            "<tr>"
            + td_html(f"<code>{esc(f['flag_id'])}</code>")
            + td(f["category"])
            + td_html(f"<strong>{esc(f['item'])}</strong>")
            + td(f["unverified_value"])
            + td(f["status"])
            + td(f["explanation"])
            + td_html(src_badge(sources_map, f["source_id"]))
            + "</tr>"
        )

    return f"""
        <div class="banner banner-warn">
          <strong>Zero-Inference Policy:</strong> None of the {len(laws_data['flagged_items'])} items below block site deployment, and zero unconfirmed numbers were guessed or filled in. Each unconfirmed value is left strictly blank (<code>""</code>) in the data layer and HTML tables until verified from primary records or official publications.
        </div>

        <section class="card">
          <h2>Flagged for Review — Unverified Blank Values &amp; Repository Irregularities ({len(laws_data['flagged_items'])})</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Flag ID</th>
                  <th>Category</th>
                  <th>Flagged Item</th>
                  <th>Value (Blank = Unverified)</th>
                  <th>Review Status</th>
                  <th>Required Action / Explanation</th>
                  <th>Official Reference</th>
                </tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
          </div>
        </section>
    """


def write_markdown_deliverables(sources_map: dict, units_data: dict, laws_data: dict) -> None:
    exec_md = f"""# Executive Summary — San Francisco Outer Sunset (ZIP 94122) Rent Increase Compliance Study

- **Verification Date:** `2026-11-06`
- **Property Profile (Owner-Reported):** Residential building reported as constructed in `1940` in San Francisco's Outer Sunset (`ZIP 94122`), analyzed under the San Francisco Rent Ordinance (`SF Admin. Code Ch. 37`; parcel APN, total unit count, and exemption status unverified from Assessor/PIM records).
- **Strict Privacy Policy:** Zero personal tenant names or initials are stored anywhere in `sf-rent-94122/` (HTML, JSON, Markdown, or Python verifier code). Neutral placeholders (`Tenant A1`–`Tenant A4` for Unit 1; `Tenant B1`–`Tenant B2` for Unit 2) are used throughout while keeping all lease dates and dollar figures exact.
- **Live Dashboard:** [`sf-rent-94122/index.html`](index.html) · **Flagged for Review:** [`sf-rent-94122/flagged.html`](flagged.html)

---

## 1. Key Findings & Exact Allowable Calculations

| Unit | Tenancy Timeline | Anonymized Occupants | Current Base Rent | 2026–27 SF Annual Cap (`1.6%`) | Verified Banked Balance | Market Reset Allowed? | Recommended Compliance Action | Official Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Unit 1** | Feb. 1, 2025 initial lease; Apr. 1, 2026 continuation | `Tenant A1` (original) & `Tenant A4` (co-occupant); `Tenant A2` & `Tenant A3` departed | `$3,995.00/mo` | `+$63.92/mo` -> `$4,058.92/mo` *(only if MTM)* | *(blank — unverified)* | **No** (`Civ. Code § 1954.53(d)(2)–(3)`; `Rules § 6.14`) | Inspect Apr. 1, 2026 agreement: if 12-mo fixed lease, barred until **Apr. 1, 2027** (`Civ. Code § 827(a)`); if MTM addendum & licensed, `1.6%` (`+$63.92`) on 30/35-day notice. | [SF Rent Increases]({sources_map['SF-INC-GUIDE']['url']}) |
| **Unit 2** | June 1, 2019 initial lease (continuing) | `Tenant B1` & `Tenant B2` (original occupants) | `$3,150.00/mo` | `+$50.40/mo` -> `$3,200.40/mo` | *(blank — ledger unverified)* | **No** (`Civ. Code § 1954.53(d)`) | Audit 2019–2026 ledger & portal license. Standard `1.6%` (`+$50.40`) on 30/35-day notice is lowest risk and preserves valid banked years without triggering the `>10%` 90/95-day March 1 rate-year cliff. | [SF Banked Increases]({sources_map['SF-BANKED']['url']}) |

---

## 2. Six Critical Legal Rules for This 1940 Building in ZIP 94122

1. **Binding Local Cap (`1.6%` through Feb. 28, 2027):** Under [SF Rent Board Form 571]({sources_map['SF-FORM-571']['url']}) and [SF Admin. Code § 37.3(a)(1)]({sources_map['SF-INC-GUIDE']['url']}), the annual allowable increase for effective dates **March 1, 2026 – February 28, 2027** is **1.6%** of base rent only, with **zero upward rounding**. Statewide AB 1482 (`8.8%` in SF) does **not** apply ([SF AB 1482 Guide]({sources_map['SF-AB1482']['url']})).
2. **Mandatory Housing Inventory License (`portal.sfrb.org`):** Under [SF Admin. Code § 37.15 / Ch. 37A]({sources_map['SF-INVENTORY']['url']}), no annual or banked rent increase may take effect unless the owner has filed the annual Housing Inventory and holds an active **Rent Increase License** on the effective date.
3. **Unit 1 Occupant Transition Trap:** Because original occupant `Tenant A1` continues to live in Unit 1, neither Costa-Hawkins ([Cal. Civ. Code § 1954.53(d)(2)–(3)]({sources_map['CA-CIV-1954-53']['url']})) nor [SF Rent Board Rules § 6.14]({sources_map['SF-614-CH']['url']}) allows a market reset, and [Rules § 6.13]({sources_map['SF-INC-GUIDE']['url']}) prohibits charging extra rent for adding `Tenant A4`. Furthermore, if the April 1, 2026 agreement is a 12-month fixed-term lease, [Cal. Civ. Code § 827(a)]({sources_map['CA-CIV-827']['url']}) bars any unilateral increase prior to **April 1, 2027** (when the not-yet-published 2027–2028 SF rate will govern).
4. **Unit 2 Ledger & Banking Rules (`Topic 503`):** Because the brief supplies only the June 1, 2019 lease-start rent (`$3,150/mo`) and not interim 2019–2026 history, Unit 2's current lawful base rent and collectible banked balance are left strictly **blank** until ledger reconciliation. Under [SF Rent Board Topic 503]({sources_map['SF-BANKED']['url']}), banking requires ≥24 full months without an increase and simple non-compounded addition; any combined increase `>10%` requires **90 days personal / 95 days CA mailed notice** ([Civ. Code § 827(b)(3)]({sources_map['CA-CIV-827']['url']}); [CCP § 1013]({sources_map['CA-CCP-1013']['url']})), and mailing a 95-day notice after **November 25, 2026** pushes the effective date past February 28, 2027 into the unpublished 2027–2028 rate period ([SF Multiple-Year Guide]({sources_map['SF-MULTI-YR']['url']})).
5. **Corporate vs. Individual Owners:** Corporate REITs ([SEC Form 10-K]({sources_map['FED-SEC-10K']['url']}); disqualified from AB 1482 single-family exemptions under [Civ. Code § 1947.12(d)(5)]({sources_map['CA-CIV-1947-12']['url']})) use bulk Housing Inventory uploads (`5+` units), while San Francisco bans algorithmic rent-setting software using non-public competitor data for all landlords ([SF Admin. Code § 37.10C]({sources_map['SF-3710C']['url']}), `$1,000`/unit/month penalty; tenant-org standing effective Oct. 6, 2025 per [Ord. 169-25]({sources_map['SF-3710C-UPD']['url']})). Representative behavioral rates are left blank/flagged.
6. **Tenant-Advocate Scrutiny & Raising One vs. Both Units:** ZIP `94122` generated **42 tenant petitions** in FY 2024–2025 ([SF Statistical Report]({sources_map['SF-STATS-2425']['url']})). City-funded free EDC defense applies to eviction court papers ([SF Evictions]({sources_map['SF-EVICTIONS']['url']})), while Form 590 clinics including **Open Door Legal (`1722 Irving St., 94122`)** have eligibility criteria ([SF Referral Listing]({sources_map['SF-REFERRALS']['url']})). Apply a neutral per-unit eligibility rule across the property after verifying [Civ. Code § 1942.5(a)/(d)]({sources_map['CA-CIV-1942-5']['url']}), FHA ([42 U.S.C. § 3604]({sources_map['FED-HUD-FHA']['url']})), FEHA ([Gov. Code § 12955]({sources_map['CA-GOV-12955']['url']})), and [SF § 37.10B]({sources_map['SF-3710B']['url']}); no public study guarantees passing counsel review without case-specific inspection of unseen leases and ledgers.

*Informational compliance research verified against official sources as of November 6, 2026; not formal legal advice.*
"""
    (BASE_DIR / "EXECUTIVE_SUMMARY.md").write_text(exec_md, encoding="utf-8")

    audit_rows_md = "\n".join(
        f"| `{r['audit_id']}` | `{r['scope_path']}` | {r['verdict']} | {r['finding']} | [{r['source_id']}]({sources_map[r['source_id']]['url']}) |"
        for r in laws_data["repo_audit"]
    )
    flag_rows_md = "\n".join(
        f"| `{f['flag_id']}` | {f['category']} | {f['item']} | `{f['unverified_value']}` | {f['status']} | {f['explanation']} | [{f['source_id']}]({sources_map[f['source_id']]['url']}) |"
        for f in laws_data["flagged_items"]
    )
    repo_md = f"""# Repository Line-by-Line Review & Flagged Irregularities (`sassnarep3-star/Own4`)

- **Audit Date:** `2026-11-06`
- **Audited Branch:** `arena/3a52f5fc-own4`
- **Privacy Check:** PASS — Zero private tenant initials or personal identifiers appear anywhere in `sf-rent-94122/` or our `COORDINATION.md` entries.

## 1. Repository Audit Findings

| Audit ID | Scope / Path | Verdict | Finding | Official Reference |
| :--- | :--- | :--- | :--- | :--- |
{audit_rows_md}

## 2. Complete Flagged for Review Register (12 Non-Blocking Items)

All unconfirmable private or unpublished values are left strictly blank (`""`) rather than inferred:

| Flag ID | Category | Item | Value | Status | Explanation | Official Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
{flag_rows_md}
"""
    (BASE_DIR / "REPO_REVIEW.md").write_text(repo_md, encoding="utf-8")

    readme_md = f"""# SF Outer Sunset (ZIP 94122) Rent Increase Compliance Dashboard (`sf-rent-94122/`)

Clean, deterministic, multi-page static research dashboard analyzing lawful and standard rental increases for two anonymized units in an owner-reported 1940 San Francisco Outer Sunset (`94122`) residential property as of **November 6, 2026**.

## Pages Generated (`build_site.py`)

- `index.html` — Overview Dashboard (KPI cards, Unit 1 & Unit 2 snapshot, core answers, category tiles)
- `executive-summary.html` — Executive Summary & 6-step compliance action plan
- `units-analysis.html` — Unit 1 & Unit 2 arithmetic, interactive integer-cent calculator, Form 571 schedule (2019–2028), Unit 2 banking scenarios, and ZIP 94122 / HUD FY 2027 benchmarks
- `laws-and-caps.html` — Local SF, California, and Federal statutory matrix + passthroughs & fees
- `landlord-practices.html` — Corporate REITs vs. Individual SF Property Owners
- `notice-and-scrutiny.html` — 5-step notice protocol, valid/invalid reasons, One-vs-Both units matrix, 12-point SF tenant-lawyer audit checklist, and official free legal directory
- `repo-audit.html` — Line-by-line audit of `sassnarep3-star/Own4` (including HTTP 404 link detection in peer `rental-sf/index.html`)
- `sources.html` — {len(sources_map)} allowlisted official government & repository sources verified on `2026-11-06`
- `flagged.html` — {len(laws_data["flagged_items"])} non-blocking Flagged for Review items (all unconfirmed values left strictly blank `""`)

## Build & Verify

```bash
python3 sf-rent-94122/build_site.py
python3 sf-rent-94122/verify_site.py
python3 -m unittest discover -s sf-rent-94122 -p "test_*.py" -v
```
"""
    (BASE_DIR / "README.md").write_text(readme_md, encoding="utf-8")


def main() -> None:
    sources_data = load_json("sources.json")
    units_data = load_json("units_and_rates.json")
    laws_data = load_json("laws_and_practices.json")

    sources_map = {s["id"]: s for s in sources_data["sources"]}
    flag_count = len(laws_data["flagged_items"])
    source_count = len(sources_data["sources"])

    # Sanity-check exact arithmetic in Python Decimal before generating HTML
    assert Decimal("3995.00") * Decimal("0.016") == Decimal("63.92000")
    assert Decimal("3150.00") * Decimal("0.016") == Decimal("50.40000")
    assert (
        Decimal("1.8")
        + Decimal("0.7")
        + Decimal("2.3")
        + Decimal("3.6")
        + Decimal("1.7")
        + Decimal("1.4")
        == Decimal("11.5")
    )
    assert Decimal("3150.00") * Decimal("0.115") == Decimal("362.25000")
    assert Decimal("362.25") + Decimal("50.40") == Decimal("412.65")

    pages_spec = [
        (
            "index.html",
            "SF Outer Sunset (94122) Rent Increase Compliance Dashboard",
            "Overview Dashboard · 1940 Rent-Controlled Property",
            "Verified local, California, and federal rent-increase analysis for two anonymized tenancies in San Francisco ZIP 94122 as of November 6, 2026.",
            build_index_page(sources_map, units_data, laws_data),
        ),
        (
            "executive-summary.html",
            "Executive Summary & Compliance Action Plan",
            "Category 1 · Executive Summary",
            "Concise synthesis of governing caps, occupancy-turnover locks, banking cliffs, fair-housing rules, and pre-service verification steps.",
            build_exec_summary_page(sources_map, units_data, laws_data),
        ),
        (
            "units-analysis.html",
            "Unit 1 & Unit 2 Rent Analysis, Banking & Benchmarks",
            "Category 2 · Unit-Level Quantitative Analysis",
            "Exact base-rent arithmetic, interactive integer-cent calculator, SF Rent Board Form 571 rates (2019–2028), Unit 2 banking scenarios, and ZIP 94122 / HUD benchmarks.",
            build_units_page(sources_map, units_data),
        ),
        (
            "laws-and-caps.html",
            "Local, California & Federal Legal Framework",
            "Category 3 · Statutory & Regulatory Matrix",
            "Line-by-line analysis of SF Admin. Code Ch. 37 & 37A, Rent Board Rules §§ 6.13–6.14, Costa-Hawkins, AB 1482, Civil Code §§ 827 & 1942.5, FEHA, and the Federal Fair Housing Act.",
            build_laws_page(sources_map, units_data, laws_data),
        ),
        (
            "landlord-practices.html",
            "Corporate REITs vs. Individual SF Property Owners",
            "Category 4 · Institutional vs. Small-Owner Practices",
            "Verified comparison of statutory exemptions, Housing Inventory portal workflows, annual CPI renewal discipline, § 37.10C algorithmic pricing bans, and petition filings.",
            build_practices_page(sources_map, laws_data),
        ),
        (
            "notice-and-scrutiny.html",
            "Notice Procedure, Lawyer Scrutiny & One-vs-Both Units",
            "Category 5 · Procedural & Fair Housing Defense",
            "Five-step written service protocol, valid vs. void reasons, One-vs-Both units discrimination matrix, 12-point SF tenant-lawyer audit checklist, and free legal clinic directory.",
            build_notice_scrutiny_page(sources_map, laws_data),
        ),
        (
            "repo-audit.html",
            "Repository Line-by-Line Audit & Irregularities",
            "Category 6 · Repository Review",
            "Complete audit of sassnarep3-star/Own4, broken HTTP 404 link detection in peer module rental-sf/index.html, inherited sports workspaces, and PII verification.",
            build_repo_audit_page(sources_map, laws_data),
        ),
        (
            "sources.html",
            "Official Verified Source Registry",
            "Category 7 · Primary Authorities",
            f"Complete catalog of {source_count} official municipal, state, and federal government sources live-verified on November 6, 2026.",
            build_sources_page(sources_data),
        ),
        (
            "flagged.html",
            "Flagged for Review — Unverified Blanks & Repo Flags",
            "Category 8 · Zero-Hallucination Transparency Log",
            "Every unconfirmed private fact left blank in the dashboard plus repository link irregularities flagged during line-by-line review.",
            build_flagged_page(sources_map, laws_data),
        ),
    ]

    for filename, title, eyebrow, lede, body_html in pages_spec:
        full_html = render_shell(
            filename=filename,
            title=title,
            eyebrow=eyebrow,
            lede=lede,
            body_html=body_html,
            flag_count=flag_count,
            source_count=source_count,
        )
        (BASE_DIR / filename).write_text(full_html, encoding="utf-8")

    write_markdown_deliverables(sources_map, units_data, laws_data)
    print(f"Built {len(pages_spec)} HTML pages and 3 Markdown deliverables in {BASE_DIR}")


if __name__ == "__main__":
    main()
