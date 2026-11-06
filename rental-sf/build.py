#!/usr/bin/env python3
"""Build the isolated, source-linked San Francisco rental review site."""
from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AS_OF = "November 6, 2026"

SOURCES = {
    "SF01": {
        "title": "Current rates including rent increase, relocation, and security deposit rates",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit",
        "use": "Current city rate and effective-date boundary.",
        "note": "Official city page checked November 6, 2026.",
    },
    "SF02": {
        "title": "Annual rent increase for March 1, 2026–February 28, 2027 announced",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/news--annual-rent-increase-3126-22827-announced",
        "use": "Confirms the 1.6% annual allowance and its dates.",
        "note": "Official city announcement dated January 14, 2026.",
    },
    "SF03": {
        "title": "571 Allowable Annual Increases, 2026–27",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/documents/34344/571_Allowable_Annual_Increases_26-27_1.pdf",
        "use": "Official historical annual-rate schedule used for the Unit B illustration.",
        "note": "Official Rent Board PDF; historical rates listed in the unit analysis.",
    },
    "SF04": {
        "title": "Learn about rent increases in San Francisco",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/learn-about-rent-increases-san-francisco",
        "use": "Annual increase timing, notice, and general local process.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF05": {
        "title": "Banked rent increases",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--banked-rent-increases",
        "use": "Banking eligibility, arithmetic, license, notice, and effective-date rules.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF06": {
        "title": "Annual rent increase for multiple years",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--annual-rent-increase-multiple-years",
        "use": "Adding allowed annual percentages for a multi-year interval without compounding.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF07": {
        "title": "Learn about San Francisco rental laws",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/learn-about-san-francisco-rental-laws",
        "use": "Local rent-control coverage, pre-1979 construction, and unit-level exceptions.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF08": {
        "title": "San Francisco Rent Ordinance section 37.3 — Rent Limitations",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information/sec-373-rent-limitations",
        "use": "Local rent limits, special pathways, additional-occupant rule, and itemized notice contents.",
        "note": "Official ordinance text published by the City; checked November 6, 2026.",
    },
    "SF09": {
        "title": "The Rent Board Housing Inventory",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/rent-board-housing-inventory",
        "use": "Annual inventory reporting and current rent-increase-license prerequisite.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF10": {
        "title": "Replacement of roommates",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--replacement-roommates",
        "use": "Roommate replacement/additional-occupant procedures and no surcharge solely for an additional occupant.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF11": {
        "title": "Rent increases under section 6.14 and Costa-Hawkins",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--rent-increases-under-section-614-and-costa-hawkins",
        "use": "Narrow vacancy/roommate market-reset rules and the all-original-occupants condition.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF12": {
        "title": "Landlord petitions and passthroughs",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/landlord-petitions-and-passthroughs",
        "use": "Rent Board petition routes and specified passthroughs beyond the annual allowance.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF13": {
        "title": "Capital improvement petitions",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--capital-improvement-petitions",
        "use": "Certification/petition requirements; ordinary maintenance is not automatically a capital-improvement increase.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF14": {
        "title": "Special-circumstances petitions based on rents for comparable units",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--special-circumstances-petitions-based-rents-comparable-units",
        "use": "Limits on petitions invoking comparable rents; being below market alone is not enough.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF15": {
        "title": "California Tenant Protection Act of 2019 (AB 1482)",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/reports--california-tenant-protection-act-2019-ab-1482",
        "use": "How the state rent cap relates to San Francisco local rent control; current local summary of the state cap.",
        "note": "Official city guidance checked November 6, 2026; use the statute for the controlling text.",
    },
    "CA01": {
        "title": "California Civil Code section 1947.12 — rental-rate cap",
        "agency": "California Legislative Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1947.12&lawCode=CIV",
        "use": "State rent cap, applicability, exemptions, and required exemption notice.",
        "note": "Official California code text checked November 6, 2026.",
    },
    "CA02": {
        "title": "California Civil Code section 827 — notice of change in tenancy terms/rent",
        "agency": "California Legislative Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=827&lawCode=CIV",
        "use": "Written notice, service method, and 30/90-day periods for periodic residential tenancies.",
        "note": "Official California code text checked November 6, 2026.",
    },
    "CA03": {
        "title": "California Civil Code section 1942.5 — retaliation",
        "agency": "California Legislative Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1942.5&lawCode=CIV",
        "use": "State anti-retaliation protections relevant to rent and tenancy terms.",
        "note": "Official California code text checked November 6, 2026.",
    },
    "CA04": {
        "title": "California Government Code section 12955 — housing discrimination",
        "agency": "California Legislative Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12955&lawCode=GOV",
        "use": "State fair-housing protections relevant to rental terms and increases.",
        "note": "Official California code text checked November 6, 2026.",
    },
    "US01": {
        "title": "42 U.S.C. section 3604 — Fair Housing Act",
        "agency": "United States House of Representatives, U.S. Code",
        "url": "https://uscode.house.gov/us/usc/119-124/t42/s3604/",
        "use": "Federal fair-housing protections in rental terms and conditions.",
        "note": "Official U.S. Code text checked November 6, 2026.",
    },
    "US02": {
        "title": "24 CFR section 100.65 — discrimination in housing terms and conditions",
        "agency": "Electronic Code of Federal Regulations",
        "url": "https://www.ecfr.gov/current/title-24/subtitle-B/chapter-I/part-100/subpart-B/section-100.65",
        "use": "Federal rule examples involving rental charges and terms/conditions.",
        "note": "Official eCFR text checked November 6, 2026.",
    },
    "US03": {
        "title": "24 CFR section 982.507 — rent to owner under Housing Choice Voucher program",
        "agency": "Electronic Code of Federal Regulations",
        "url": "https://www.ecfr.gov/current/title-24/subtitle-B/chapter-IX/part-982/subpart-K/section-982.507",
        "use": "Program-specific rent-reasonableness review if voucher assistance applies.",
        "note": "Official eCFR text checked November 6, 2026.",
    },
    "SF16": {
        "title": "Tenant and landlord resources",
        "agency": "San Francisco Mayor’s Office of Housing and Community Development",
        "url": "https://www.sf.gov/tenant-and-landlord-resources",
        "use": "Current City directory for tenant counseling, eviction legal help, and related services.",
        "note": "Official City resource page checked November 6, 2026; provider hours/intake can change.",
    },
    "SF17": {
        "title": "Speak with a Rent Board counselor",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/speak-rent-board-counselor",
        "use": "Free Rent Board counseling and its express limitation that it is not legal advice.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF18": {
        "title": "Report an unlawful rent increase or request a review of your rent history",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/report-unlawful-rent-increase-or-request-review-your-rent-history",
        "use": "No-fee rent-history/unlawful-increase petition, process, and lawyer-not-required statement.",
        "note": "Official city guidance checked November 6, 2026.",
    },
    "SF19": {
        "title": "Rent Board referral listing — January 2025",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/reports--january-2025--rent-board-referral-listing",
        "use": "Dated referral information, including free counseling and a limited free legal-advice clinic listing.",
        "note": "Official listing dated January 2025; verify the current provider, schedule, eligibility, and capacity.",
    },
    "SF20": {
        "title": "San Francisco Rent Board News Archive: 2020 — temporary rent-increase moratorium",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/reports--december-2020--san-francisco-rent-board-news-archive-2020",
        "use": "Historical COVID-era freeze on specified increases effective April 7–October 21, 2020, including the notice/reinstatement process.",
        "note": "Official historical City guidance; relevant only if a claimed increase was to take effect during the freeze.",
    },
    "SF21": {
        "title": "Operating and Maintenance Expense Petitions",
        "agency": "San Francisco Rent Board",
        "url": "https://www.sf.gov/information--operating-and-maintenance-expense-petitions",
        "use": "Eligible comparison periods, the additional petition amount, expense allocation, filing, and notice timing.",
        "note": "Official city guidance checked November 6, 2026.",
    },
}


def cite(source_id: str, label: str | None = None) -> str:
    source = SOURCES[source_id]
    text = label or source["title"]
    return (
        f'<a class="source-link" data-source="{escape(source_id)}" '
        f'href="{escape(source["url"], quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">{escape(text)} <span aria-hidden="true">↗</span></a>'
    )


PAGES = [
    {
        "file": "index.html",
        "nav": "Overview",
        "title": "San Francisco rental increase review",
        "eyebrow": "Owner-supplied facts · official-source research · attorney review requested",
        "description": "A source-linked, record-limited San Francisco rent-increase analysis for two reported units in ZIP 94122.",
        "body": f'''<section class="hero-grid">
  <div class="hero-copy">
    <p class="kicker">San Francisco · ZIP 94122 · two reported units</p>
    <h1>Rent increase review, built for a careful second look.</h1>
    <p class="lead">A practical map of the local, California, and federal rules that may apply, with the known unit facts separated from what still needs proof.</p>
    <div class="pill-row"><span class="pill">Prepared {AS_OF}</span><span class="pill pill-muted">No tenant names or initials published</span><span class="pill pill-muted">Not legal advice</span></div>
  </div>
  <aside class="hero-note"><span class="label">Key date boundary</span><strong>1.6%</strong><p>San Francisco’s published annual allowance is 1.6% only for increases effective <b>March 1, 2026 through February 28, 2027</b>. No official 2027–28 rate was located as of {AS_OF}; do not carry 1.6% forward.</p><p class="source-row">{cite("SF01", "Current rates")} · {cite("SF02", "2026–27 announcement")}</p></aside>
</section>

<section class="notice-strip"><div class="notice-icon" aria-hidden="true">!</div><div><h2>Conservative review position</h2><p><b>Do not serve an increase based on this summary alone.</b> The lawful base rent, last effective increase, exact lease term, tenant continuity, unit coverage, and current Rent Board license are not established by the materials reviewed. Close those record gaps first, then have the proposed amount and notice checked.</p></div></section>

<section class="section-block">
  <div class="section-heading"><div><p class="kicker">At a glance</p><h2>What the facts can—and cannot—support</h2></div><p class="section-intro">These are conditional readings, not findings that a particular rent is lawful.</p></div>
  <div class="card-grid two">
    <article class="card card-blue"><span class="card-index">UNIT A</span><h3>$3,995 reported</h3><p>The record gives a February 1, 2025 lease/start figure and an April 1, 2026 occupant/rent snapshot at the same amount. It does <b>not</b> establish that April 1 was an increase or the last increase date. One original occupant reportedly remains, so a roommate change alone is not a market-reset basis.</p><p class="source-row">{cite("SF10", "Roommate rules")} · {cite("SF11", "Section 6.14 / Costa-Hawkins")}</p><p class="mini-warning">If April 1, 2026 was the last actual increase, the next annual increase date would be no earlier than April 1, 2027; its City rate is not yet established.</p></article>
    <article class="card card-sand"><span class="card-index">UNIT B</span><h3>$3,150 reported at 2019 start</h3><p>No later lawful-rent ledger or increase history was supplied. A 1.6% annual-only arithmetic example is $50.40, if $3,150 is still the lawful base and the effective date falls within the published window.</p><p class="source-row">{cite("SF03", "Official annual-rate table")} · {cite("SF05", "Banking rules")}</p><p class="mini-warning">If there truly were no increases since June 2019, a much larger cumulative increase may be arithmetically possible. That is a records-dependent scenario, not a verified entitlement or recommendation.</p></article>
  </div>
</section>

<section class="section-block">
  <div class="section-heading"><div><p class="kicker">Navigate the review</p><h2>Nine focused pages for the review</h2></div></div>
  <div class="card-grid three">
    <a class="nav-card" href="unit-analysis.html"><span>01</span><h3>Unit-by-unit analysis</h3><p>Reported inputs, missing proof, rate math, and roommate implications.</p><b>Review the units →</b></a>
    <a class="nav-card" href="law-and-coverage.html"><span>02</span><h3>Which law applies?</h3><p>San Francisco, California, and federal rules—plus the coverage questions.</p><b>Read the rule map →</b></a>
    <a class="nav-card" href="lawful-paths.html"><span>03</span><h3>Lawful increase paths</h3><p>Annual, banked, petition, passthrough, and narrow vacancy pathways.</p><b>Compare grounds →</b></a>
    <a class="nav-card" href="notice-process.html"><span>04</span><h3>Notice and process</h3><p>What the notice must say, how much time to allow, and what to retain.</p><b>Open the checklist →</b></a>
    <a class="nav-card" href="owner-practices.html"><span>05</span><h3>Corporate vs. individual owners</h3><p>What law actually distinguishes—and what practice data does not establish.</p><b>See the comparison →</b></a>
    <a class="nav-card" href="tenant-help.html"><span>06</span><h3>Tenant help and scrutiny</h3><p>Free Rent Board counseling, available legal-help channels, and review rights.</p><b>Find resources →</b></a>
    <a class="nav-card" href="review-checklist.html"><span>07</span><h3>Records for counsel</h3><p>A private evidence checklist and the unresolved questions to close.</p><b>Prepare the file →</b></a>
    <a class="nav-card" href="sources.html"><span>08</span><h3>Official source register</h3><p>Primary statutes and City guidance, with links and checked dates.</p><b>Inspect sources →</b></a>
    <a class="nav-card" href="repository-audit.html"><span>09</span><h3>Repository and deployment</h3><p>Why this rental site is isolated from the unrelated NBA project.</p><b>View scope notes →</b></a>
  </div>
</section>

<section class="section-block compact"><div class="section-heading"><div><p class="kicker">Privacy and scope</p><h2>Public site, private tenancy records</h2></div></div><div class="two-col"><p>Only generic labels <b>Unit A</b> and <b>Unit B</b> are used. Tenant names and initials, street address, leases, and payment records are not published. Owner-reported dates and rent figures appear only as reported inputs; they are not independently authenticated.</p><p>The official links establish legal rules, not private tenancy facts. The building’s reported 1940 construction year is suggestive of local coverage but is not a unit-level Rent Board determination. See the <a href="review-checklist.html">private records checklist</a> before relying on any calculation.</p></div></section>''',
    },
    {
        "file": "unit-analysis.html",
        "nav": "Unit analysis",
        "title": "Unit-by-unit analysis",
        "eyebrow": "Private facts are reported, not independently verified",
        "description": "San Francisco rent-increase analysis for two owner-reported units, with conditional arithmetic and unresolved questions.",
        "body": f'''<header class="page-intro"><p class="kicker">01 / Unit review</p><h1>Two units, two separate rent histories.</h1><p class="lead">A shared building address does not establish a shared lawful base rent, anniversary date, or banked-increase balance. Assess each tenancy on its own record.</p></header>

<div class="callout callout-blue"><b>Evidence boundary:</b> the inputs below were provided by the owner. No lease, Rent Board rent history, payment ledger, or official unit-level coverage determination was supplied. The official links are legal context only; they do not verify the private facts.</div>

<section class="section-block">
  <div class="section-heading"><div><p class="kicker">Reported information</p><h2>What is on the record today</h2></div><p class="section-intro">Current lawful rent and last increase date are deliberately left blank where they cannot be established.</p></div>
  <div class="table-wrap"><table><thead><tr><th scope="col">Item</th><th scope="col">Unit A</th><th scope="col">Unit B</th><th scope="col">Verification status / official context</th></tr></thead><tbody>
  <tr><th scope="row">Location / age</th><td>ZIP 94122; building reported as built in 1940.</td><td>Same reported building.</td><td><b>Unverified.</b> No street address was provided or published, so the official property record was not checked. If built before June 14, 1979 and not used as a single-family dwelling, a unit may have local rent control; coverage exceptions still matter. {cite("SF07", "City coverage rules")}</td></tr>
  <tr><th scope="row">Reported rent/start record</th><td>Lease/start reported February 1, 2025 at <b>$3,995/month</b>; April 1, 2026 occupant/rent snapshot also reported at <b>$3,995/month</b>.</td><td>Lease start reported June 1, 2019 at <b>$3,150/month</b>. No later rent figure supplied.</td><td><b>Owner-reported; not authenticated.</b> These figures do not by themselves prove current lawful base rent. Official calculation guidance uses base rent and the effective date. {cite("SF06", "Multi-year calculation")}</td></tr>
  <tr><th scope="row">Current lawful base rent</th><td><span class="blank">&nbsp;</span> <b>Blank — unverified.</b></td><td><span class="blank">&nbsp;</span> <b>Blank — unverified.</b></td><td>Obtain the full rent ledger, all notices and receipts, and a lawful-rent/rent-history review if needed. {cite("SF18", "Rent-history review process")}</td></tr>
  <tr><th scope="row">Last effective rent increase</th><td><span class="blank">&nbsp;</span> <b>Blank — unverified.</b> April 1, 2026 is a reported snapshot, not proof an increase took effect that day.</td><td><span class="blank">&nbsp;</span> <b>Blank — unverified.</b> June 1, 2019 is a reported lease-start date, not proof no later increase occurred.</td><td>Ordinary annual/banked timing depends on the last increase and the effective date; a tenancy or roster date is not a substitute for the rent-increase ledger. {cite("SF04", "Annual increase timing")} · {cite("SF05", "Banked increase rules")}</td></tr>
  <tr><th scope="row">Occupant continuity</th><td>Owner reports that at least one original occupant remains; identities omitted.</td><td>Continuity after June 2019 not established; identities omitted.</td><td><b>Unverified tenancy history.</b> No surcharge is allowed solely because an occupant is added/replaced; the market-reset rules are narrow and turn on original-occupant status and other requirements. {cite("SF10", "Roommate replacement") } · {cite("SF11", "Section 6.14 / Costa-Hawkins")}</td></tr>
  <tr><th scope="row">Rent Board license / lease term</th><td><span class="blank">&nbsp;</span> <b>Not checked.</b></td><td><span class="blank">&nbsp;</span> <b>Not checked.</b></td><td>A current Housing Inventory rent-increase license is required before a covered annual/banked increase takes effect. Fixed-term lease terms also need review. {cite("SF09", "Housing Inventory and license")}</td></tr>
  </tbody></table></div>
  <p class="table-note">The column titled “verification status / official context” identifies what remains unverified and links the legal rule. It does not imply the City authenticated the rent, date, or occupancy facts.</p>
</section>

<section class="section-block">
  <div class="section-heading"><div><p class="kicker">Arithmetic only</p><h2>Illustrations—not proposed rents</h2></div><p class="section-intro">The 1.6% rate is tied to an effective date within March 1, 2026–February 28, 2027, not to the date a notice is drafted.</p></div>
  <div class="table-wrap"><table><thead><tr><th scope="col">Scenario</th><th scope="col">Illustrative math</th><th scope="col">What must be true first</th><th scope="col">Official source</th></tr></thead><tbody>
  <tr><th scope="row">Unit A — annual-only example</th><td>$3,995 × 1.6% = <b>$63.92</b>; illustrative total $4,058.92.</td><td>$3,995 must still be the lawful base; the unit must be locally covered; 12-month timing, lease terms, license, and valid notice must permit it; effective date must be by February 28, 2027. If April 1, 2026 was the last actual increase, the next ordinary date is no earlier than April 1, 2027, for which the rate is unknown.</td><td>{cite("SF01", "Rate window")} · {cite("SF04", "Timing rules")}</td></tr>
  <tr><th scope="row">Unit B — annual-only example</th><td>$3,150 × 1.6% = <b>$50.40</b>; illustrative total $3,200.40.</td><td>$3,150 must still be the lawful base and the relevant effective date must fall within the published window. The later rent history is missing, so this is not a calculation of the actual lawful increase.</td><td>{cite("SF01", "Rate window")} · {cite("SF06", "Base-rent calculation")}</td></tr>
  <tr><th scope="row">Unit B — no-increase-since-2019 hypothesis</th><td>2020–2025 annual percentages total 11.5%; add the 2026 annual 1.6% = <b>13.1%</b>. If $3,150 were still the lawful base: $3,150 × 13.1% = <b>$412.65</b>; illustrative total $3,562.65.</td><td><b>Hypothetical only.</b> Requires proof that the lawful base remained $3,150, the same tenancy/tenant history continued, no rent increase was imposed since June 1, 2019, all relevant rates are properly banked, the effective date falls within the stated rate periods, the increase is otherwise allowed, the license is current, and notice is valid. The 2020 1.8% period overlaps San Francisco’s temporary COVID rent-increase freeze for increases effective April 7–October 21, 2020; any deferred 2020 notice/reinstatement history must be checked before counting that amount. At over 10%, the notice period is generally 90 days (plus 5 days if mailed). Do not use this figure without the complete ledger and lawyer review.</td><td>{cite("SF03", "Official annual-rate table")} · {cite("SF05", "Banking conditions")} · {cite("SF06", "Multi-year method")} · {cite("SF20", "2020 freeze history")} · {cite("CA02", "30/90-day notice")}</td></tr>
  </tbody></table></div>
  <p class="table-note"><b>Arithmetic boundary:</b> the 13.1% sum includes the 2025 1.4% and 2026 1.6% rates and does not compound. It is not a verified entitlement. In particular, the 2020 rate overlaps the temporary City freeze; whether it was deferred, reinstated, or otherwise remains available depends on the actual notices and rent history. {cite("SF20", "2020 freeze and reinstatement guidance")}</p>
</section>

<section class="section-block">
  <div class="section-heading"><div><p class="kicker">Historical rates</p><h2>Rates relevant to the Unit B hypothesis</h2></div><p class="section-intro">The table is the City’s published annual schedule. The “year” is the effective-date period containing the reported June 1 anniversary.</p></div>
  <div class="table-wrap"><table><thead><tr><th scope="col">Effective-date period</th><th scope="col">Annual rate</th><th scope="col">Use in the hypothetical</th><th scope="col">Official rate schedule</th></tr></thead><tbody>
  <tr><th scope="row">March 1, 2020–February 28, 2021</th><td>1.8%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2021–February 28, 2022</th><td>0.7%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2022–February 28, 2023</th><td>2.3%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2023–February 29, 2024</th><td>3.6%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2024–February 28, 2025</th><td>1.7%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2025–February 28, 2026</th><td>1.4%</td><td>Potentially banked only if eligibility/history are proven.</td><td>{cite("SF03", "Rent Board rate table")}</td></tr>
  <tr><th scope="row">March 1, 2026–February 28, 2027</th><td><b>1.6%</b></td><td>Current published period as of the report date; not a known rate for March 1, 2027 or later.</td><td>{cite("SF01", "Current City rate page")}</td></tr>
  </tbody></table></div>
</section>

<section class="section-block compact"><div class="section-heading"><div><p class="kicker">Unit A: roommate change</p><h2>Do not treat a roster update as a rent reset.</h2></div></div><p>The owner-reported facts say at least one original occupant remains. San Francisco’s additional-occupant rule bars a rent increase solely because another occupant is added; the 6.14/Costa-Hawkins market-rate pathways generally require the last original occupant to leave and other conditions to be met. Verify the lease and whether each person is a co-tenant or subtenant before drawing a conclusion. {cite("SF08", "Ordinance §37.3(a)(11)")} {cite("SF10", "Roommate replacement")} {cite("SF11", "Market-reset guidance")}</p></section>

<section class="notice-strip"><div class="notice-icon" aria-hidden="true">→</div><div><h2>Assess each unit on its own record</h2><p>There is no obligation to raise both rents for symmetry. A neutral policy can result in different outcomes where lawful base rents, last increase dates, occupancy histories, or coverage differ. Applying the same dollar increase to both is not a substitute for correct, non-discriminatory calculations.</p><p class="source-row">{cite("CA04", "California fair-housing law")} · {cite("US01", "Federal Fair Housing Act")} · {cite("CA03", "Anti-retaliation law")}</p></div></section>''',
    },
    {
        "file": "law-and-coverage.html",
        "nav": "Law & coverage",
        "title": "Which law may apply?",
        "eyebrow": "Local first · state overlays/exemptions · federal protections",
        "description": "A source-linked map of San Francisco, California, and federal rent-increase rules for the reported units.",
        "body": f'''<header class="page-intro"><p class="kicker">02 / Legal framework</p><h1>Start with the unit—not the landlord’s size.</h1><p class="lead">The first legal question is whether each dwelling is locally rent-controlled, state-cap-covered, exempt, subsidized, or governed by a contract. A 1940 building date is a useful lead, not a legal determination.</p></header>

<div class="callout callout-sand"><b>Coverage remains open.</b> San Francisco says many residential units built on or before June 13, 1979 have rent control. A pre-June 14, 1979 unit that is not used as a single-family dwelling may qualify, but single-family/condo, substantial-rehabilitation, subsidy, and other exceptions can change the result. The reported building year and ZIP do not resolve unit classification. {cite("SF07", "City coverage guide")}</div>

<section class="section-block"><div class="table-wrap"><table><thead><tr><th scope="col">Layer</th><th scope="col">Rule relevant to an increase</th><th scope="col">Application to these facts</th><th scope="col">Official sources</th></tr></thead><tbody>
<tr><th scope="row">San Francisco Rent Ordinance</th><td>For covered units, the annual allowance is set by the Rent Board; an annual or properly banked increase is generally limited by the 12-month rule. Above-allowance increases require a specific petition, passthrough, or other legal authority. The published 1.6% rate applies only to effective dates March 1, 2026–February 28, 2027. The City publishes a San Francisco rate; no separate ZIP 94122/Outer Sunset percentage appears in the official schedule.</td><td>The 1940 date, if accurate, points toward possible local coverage. The exact dwelling type, prior use, rent history, and any exemption must be verified for each unit.</td><td>{cite("SF07", "Coverage")} · {cite("SF08", "§37.3") } · {cite("SF01", "Current rate")}</td></tr>
<tr><th scope="row">California AB 1482 rent cap</th><td>For units subject to the state cap, the general cap is 5% plus the applicable CPI change, up to 10%. San Francisco’s published cap for qualifying AB 1482 units is 8.8% for effective dates August 1, 2026–July 31, 2027. State coverage and exemption notices must be checked.</td><td>The City says its stricter local rent-increase limits govern locally rent-controlled units rather than this state cap. Do not substitute 8.8% for the 1.6% local allowance if a unit is locally controlled. If local control does not apply, analyze AB 1482 coverage and exemptions separately.</td><td>{cite("SF15", "City AB 1482 guide")} · {cite("CA01", "Civil Code §1947.12")}</td></tr>
<tr><th scope="row">California notice law</th><td>For periodic residential tenancies covered by Civil Code §827, written notice is generally at least 30 days for a rent increase of 10% or less and 90 days if it is greater than 10%, with statutory service rules; mailing adds the applicable service time. More protective lease/program rules may apply.</td><td>The Unit B hypothetical is 13.1%, so it crosses the 90-day threshold if it were otherwise allowed. Unit A’s actual amount and lease term are not known.</td><td>{cite("CA02", "Civil Code §827")} · {cite("SF05", "Rent Board notice summary")}</td></tr>
<tr><th scope="row">State and federal fair housing</th><td>Rental terms and conditions cannot be discriminatory on protected grounds. California protections supplement the federal Fair Housing Act. A uniform increase applied to everyone does not cure an otherwise discriminatory decision.</td><td>Use neutral, documented, unit-specific eligibility and arithmetic. Do not select or time an increase because of a protected characteristic, family status, disability, source of income, or other protected activity/status.</td><td>{cite("CA04", "Government Code §12955")} · {cite("US01", "42 U.S.C. §3604")} · {cite("US02", "24 CFR §100.65")}</td></tr>
<tr><th scope="row">Retaliation</th><td>California law restricts rent increases and other adverse actions taken in retaliation for protected tenant conduct, such as asserting legal rights or making certain complaints.</td><td>Check recent repair/code complaints, requests for legally protected accommodation, and other protected activity before deciding timing. A chronology alone does not decide the legal issue.</td><td>{cite("CA03", "Civil Code §1942.5")}</td></tr>
<tr><th scope="row">Federal assistance / contract rules</th><td>The federal Fair Housing Act does not set a general annual rent percentage for an ordinary, unsubsidized private tenancy. If a Housing Choice Voucher applies, the PHA’s rent-reasonableness review and program requirements are relevant; other subsidies/contracts may add rules.</td><td>No subsidy, voucher, regulatory agreement, or contract information was provided. Verify before using a private-market calculation.</td><td>{cite("US01", "Fair Housing Act")} · {cite("US03", "24 CFR §982.507")}</td></tr>
</tbody></table></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Ownership-type caveat</p><h2>Some exemptions do depend on ownership—but narrowly.</h2></div></div><p>California’s state-cap exemptions for certain single-family homes or condominiums have specific ownership-entity and written-notice conditions. The statutory exemption language excludes, among others, property owned by a real estate investment trust, a corporation, or an LLC with a corporate member; failure to give the required notice can defeat that exemption. State law also has a separate, fact-specific exemption for a two-unit structure where the owner occupied one unit as a principal residence at the beginning of the tenancy and continues to occupy it, subject to statutory details. None of those facts is established here. These are not blanket rules that “corporations get a different rent increase” or “individual owners are exempt.” {cite("CA01", "Civil Code §1947.12")} {cite("SF15", "City AB 1482 guide")}</p></section>

<section class="section-block compact"><div class="section-heading"><div><p class="kicker">Effective-date discipline</p><h2>Use the rate on the date rent changes—not the notice date.</h2></div></div><p>The Rent Board’s guidance directs landlords to use the percentage in effect when the increase takes effect. As of {AS_OF}, 1.6% is established through February 28, 2027; a later rate was not found. A notice issued before the new rate is published does not make the old rate safe for a post-February effective date. Confirm again before serving. {cite("SF05", "Banking and notice guidance")} {cite("SF01", "Current rates")}</p></section>''',
    },
    {
        "file": "lawful-paths.html",
        "nav": "Lawful paths",
        "title": "What can lawfully support an increase?",
        "eyebrow": "A percentage is not a reason by itself; the legal pathway controls",
        "description": "San Francisco pathways for annual, banked, petition-based, passthrough, and roommate-related rent changes.",
        "body": f'''<header class="page-intro"><p class="kicker">03 / Lawful grounds</p><h1>Match every dollar to a recognized path.</h1><p class="lead">For a locally controlled unit, general costs, market demand, or a new roommate are not free-standing authority to add an arbitrary surcharge. Identify the legal category, calculate it under the City rules, and document the supporting records.</p></header>

<section class="section-block"><div class="table-wrap"><table><thead><tr><th scope="col">Potential path</th><th scope="col">What may support it</th><th scope="col">Process / limit to check</th><th scope="col">Official source</th></tr></thead><tbody>
<tr><th scope="row">Annual allowable increase</th><td>The Rent Board’s published annual percentage for the effective date. It is a formula-based allowance; a landlord need not invent a repair or cost story to explain it.</td><td>Generally no more than once every 12 months; calculate on lawful base rent, use effective-date rate, verify current Housing Inventory license and written notice. For these facts, 1.6% is only the March 1, 2026–February 28, 2027 rate.</td><td>{cite("SF01", "Rate schedule")} · {cite("SF04", "Annual increase guide")} · {cite("SF09", "License requirement")}</td></tr>
<tr><th scope="row">Banked annual increase</th><td>Annual percentages that were not used may be combined if the City’s eligibility/timing conditions are met.</td><td>The City requires 24 full months without a rent increase for a skipped amount to be banked; at least 12 months must pass between imposed increases. Add percentages—do not compound or prorate—and use the current lawful base. Keep the year-by-year ledger and rate table. Check any deferred/reinstated 2020 increase separately because of the temporary COVID freeze.</td><td>{cite("SF05", "Banked-increase rules")} · {cite("SF06", "Multi-year arithmetic")} · {cite("SF03", "Historical rate table")} · {cite("SF20", "2020 freeze history")}</td></tr>
<tr><th scope="row">Operating and maintenance expenses</th><td>If the annual allowance does not cover the qualifying yearly expense increase, the City allows an O&amp;M petition for an additional base-rent increase of up to 7% under its rules.</td><td>Compare the required expense periods (two consecutive calendar years or a qualifying 24-month period), allocate per unit, and file the petition before notice. The same landlord’s total O&amp;M increase is limited to 7% in any five-year period for a property with six or more residential units. A change-in-ownership tax increase is disallowed; ordinary expenses do not create a self-help surcharge.</td><td>{cite("SF21", "O&M petition criteria")} · {cite("SF12", "Petitions and passthroughs")} · {cite("SF08", "Ordinance §37.3")}</td></tr>
<tr><th scope="row">Capital improvements</th><td>Completed, eligible work that materially adds value, prolongs useful life, or adapts the property may qualify for a Rent Board passthrough; ordinary repairs/maintenance do not.</td><td>Rules depend on the residential-unit count for the entire property. For 1–5 units, up to 100% of certified costs may be passed through, subject to a per-12-month cap of the greater of $30 or 5% of petition base rent and 10/15/20-year amortization. For 6+ units, the general rule is 50% with a cap of the greater of $30 or 10%; exceptions apply. Work must be complete; file the petition within five years and before serving notice. The passthrough stays separate from base rent. Unit count is not verified here.</td><td>{cite("SF13", "Capital-improvement petition rules")} · {cite("SF12", "Landlord petition overview")}</td></tr>
<tr><th scope="row">Comparable-rent / special circumstances</th><td>A narrow petition route exists for specified special circumstances involving comparable units.</td><td>Being below current market rent, standing alone, is not enough. Verify the City’s criteria and file the required petition; do not use online asking rents as a self-help percentage.</td><td>{cite("SF14", "Special-circumstances criteria")}</td></tr>
<tr><th scope="row">Specified passthroughs</th><td>Only the named charges and calculations permitted by the Ordinance (for example, certain utility or bond-related items) may be passed through.</td><td>Use the current City form and calculation; itemize the charge; observe any eligibility, timing, hardship, and separate-base-rent rules. A generic “taxes/insurance went up” line is not enough.</td><td>{cite("SF08", "Ordinance §37.3")} · {cite("SF12", "Passthrough guidance")}</td></tr>
<tr><th scope="row">New or replacement occupant</th><td>Adding or replacing an occupant alone does not authorize a rent increase. A market reset may be possible only in narrow situations after the last original occupant leaves and the legal requirements are met.</td><td>Do not charge more solely for a new roommate. Check whether an occupant is a co-tenant or subtenant, original-tenant continuity, any timely §6.14 notice, and Costa-Hawkins conditions. One original occupant reportedly remains in Unit A.</td><td>{cite("SF08", "Ordinance §37.3(a)(11)")} · {cite("SF10", "Replacement-roommate rules")} · {cite("SF11", "Market-reset rules")}</td></tr>
</tbody></table></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Prudent explanation</p><h2>Explain the actual legal category—do not embellish.</h2></div></div><div class="two-col"><article class="card"><h3>For an annual increase</h3><p>A straightforward explanation is that the proposed amount is the annual adjustment published by the San Francisco Rent Board for the stated effective date. State the exact dollar and percentage calculation on the lawful base rent. The annual allowance is not an individualized invoice for repairs or insurance.</p><p>{cite("SF01", "Published rate")} · {cite("SF04", "Rent Board guidance")}</p></article><article class="card"><h3>For banked or petition amounts</h3><p>Name the banked years and percent, or the specific approved petition/passthrough and its attached calculation. Do not call an unverified estimate “banked,” or describe an ordinary expense as a certified improvement without the City’s decision.</p><p>{cite("SF05", "Banked amount disclosure")} · {cite("SF08", "Itemized notice")}</p></article></div></section>

<section class="notice-strip"><div class="notice-icon" aria-hidden="true">✓</div><div><h2>Recommended decision rule</h2><p>For each unit, independently confirm (1) coverage and lawful base rent, (2) the last effective increase and full history, (3) the applicable path, (4) license and effective-date rate, (5) a compliant itemized notice, and (6) neutral, non-retaliatory treatment. If any input is unknown, pause rather than round up or assume.</p><p class="source-row">{cite("SF09", "License")} · {cite("SF18", "Rent-history review")}</p></div></section>''',
    },
    {
        "file": "notice-process.html",
        "nav": "Notice & process",
        "title": "Notice and process checklist",
        "eyebrow": "Clear, accurate, provable, and served with enough time",
        "description": "A source-linked San Francisco rent-increase notice checklist, with statutory notice periods and required breakdowns.",
        "body": f'''<header class="page-intro"><p class="kicker">04 / Notice and process</p><h1>A sound notice starts with a sound record.</h1><p class="lead">A legally permissible amount can still fail if the base, timing, licensing, category breakdown, or service is wrong. Use this as a review checklist, not as a ready-to-serve legal form.</p></header>

<section class="section-block"><div class="table-wrap"><table><thead><tr><th scope="col">Checkpoint</th><th scope="col">Practical requirement</th><th scope="col">Why it matters here</th><th scope="col">Official source</th></tr></thead><tbody>
<tr><th scope="row">1. Confirm the tenancy and lawful base</th><td>Review the signed lease and addenda, current term, lawful rent history, every prior increase, and all separate passthroughs. Annual percentages apply to base rent, not a guessed total including separate charges.</td><td>Unit A’s April 2026 record is not shown to be a rent increase. Unit B’s $3,150 is a 2019 start figure, not a confirmed current lawful base.</td><td>{cite("SF06", "Base-rent and multi-year guide")} · {cite("SF18", "Rent-history process")}</td></tr>
<tr><th scope="row">2. Confirm coverage and license</th><td>Determine local/state coverage and verify that a current Housing Inventory rent-increase license is on file before a covered annual/banked increase takes effect.</td><td>The street address and unit classification were not supplied; no license lookup was possible.</td><td>{cite("SF07", "Coverage guide")} · {cite("SF09", "Housing Inventory")}</td></tr>
<tr><th scope="row">3. Calculate for the effective date</th><td>Use the percentage in effect when the increase takes effect. Add properly banked percentages without compounding; keep each year’s rate and the base-rent calculation.</td><td>1.6% is established only through February 28, 2027. If notice timing pushes an effective date beyond that, verify the newly published rate rather than reusing 1.6%.</td><td>{cite("SF01", "Current rate window")} · {cite("SF05", "Banked calculation")}</td></tr>
<tr><th scope="row">4. Give enough written notice</th><td>For periodic residential tenancies covered by Civil Code §827, generally at least 30 days if the total increase is 10% or less and 90 days if greater than 10%; personal delivery or statutory mail service applies. The City says allow 5 extra days when mailing.</td><td>The conditional Unit B 13.1% scenario is over 10% and would generally require 90 days plus the mail buffer. The exact lease/assistance rules still need review.</td><td>{cite("CA02", "Civil Code §827")} · {cite("SF05", "City notice guidance")}</td></tr>
<tr><th scope="row">5. Break out each component</th><td>On or before legal notice, identify which portion is annual and/or banked; separately identify any operating/maintenance, comparable-rent, capital-improvement, rehabilitation, energy, renewable, utility/bond passthrough, or RAP component that applies. Provide required City forms/calculations.</td><td>A single blended figure can obscure whether the amount is lawful. Unit B’s hypothetical banked portion would need years and math stated clearly.</td><td>{cite("SF08", "Ordinance §37.3(b)")} · {cite("SF05", "Banked notice contents")}</td></tr>
<tr><th scope="row">6. Preserve proof and review fairness</th><td>Keep the served notice, service date/method proof, calculation worksheet, rate source, license evidence, ledger, petition/order, and a short neutral rationale. Check for protected-class discrimination and retaliation risk.</td><td>Raising both units is not a cure for an unsupported or discriminatory increase; each unit’s eligibility/history must stand on its own.</td><td>{cite("CA04", "State fair-housing law")} · {cite("CA03", "Anti-retaliation law")} · {cite("US01", "Federal Fair Housing Act")}</td></tr>
</tbody></table></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Tenant-facing language</p><h2>Be clear about what the amount represents.</h2></div></div><div class="draft-box"><span class="label">Communication outline only — not a statutory notice form</span><p>“The proposed monthly rent change is <b>$[amount]</b> (<b>[percentage]%</b>), effective <b>[date]</b>. The increase is composed of: annual allowance <b>[rate / amount]</b>; banked annual increases <b>[years / total rate / amount]</b>; and any separately authorized item <b>[type / amount / attached City form or decision]</b>. The calculation uses base rent of <b>$[verified base]</b>. Please review the attached breakdown and contact the San Francisco Rent Board or your own advisor with questions.”</p><p class="fine-print">Do not send this text as a substitute for a legally compliant notice. Do not fill in a banked amount until the ledger, eligibility, and City rate schedule are verified. Use any prescribed Rent Board form/order and confirm service requirements with counsel.</p><p>{cite("SF08", "Required local notice components")} · {cite("SF05", "Banked notice guidance")}</p></div></section>

<section class="section-block compact"><div class="section-heading"><div><p class="kicker">What not to say</p><h2>Avoid unsupported explanations.</h2></div></div><ul class="check-list"><li>Do not say an increase is required because “market rent went up” unless a specific legal pathway actually permits it.</li><li>Do not say “insurance, taxes, or repairs” independently authorize a surcharge; use only an applicable petition/passthrough route and its substantiation.</li><li>Do not imply a roommate replacement itself raised the legal rent.</li><li>Do not describe a 2027 effective-date rate as 1.6% until the Rent Board publishes it.</li></ul><p>{cite("SF12", "Petition/passthrough routes")} · {cite("SF14", "Comparable-rent petition standard")} · {cite("SF10", "Roommate rules")} · {cite("SF01", "Rate dates")}</p></section>''',
    },
    {
        "file": "owner-practices.html",
        "nav": "Owner types",
        "title": "Corporate and individual landlords",
        "eyebrow": "Separate legal differences from unverified business-practice claims",
        "description": "What official law says about landlord entity type and what evidence does not establish about corporate versus individual practices.",
        "body": f'''<header class="page-intro"><p class="kicker">05 / Ownership and practice</p><h1>Size is not a substitute for the legal test.</h1><p class="lead">A company may have a standardized rent-management process and an individual owner may keep a manual ledger—but that is a plausible operational observation, not a verified fact about how these landlords behave.</p></header>

<div class="callout callout-sand"><b>Evidence limit:</b> I did not identify an official San Francisco, California, or federal study in the sources reviewed that establishes “normal” rent-increase practices or average increase amounts by landlord size/entity type in San Francisco. This report does not claim that corporations increase more, less, or more uniformly than individual owners.</div>

<section class="section-block"><div class="section-heading"><div><p class="kicker">What the law supports</p><h2>Rules that do—and do not—vary by owner type</h2></div></div><div class="table-wrap"><table><thead><tr><th scope="col">Question</th><th scope="col">Verified rule / research finding</th><th scope="col">Practical implication</th><th scope="col">Official source</th></tr></thead><tbody>
<tr><th scope="row">Does San Francisco set one local annual rate for companies and another for individuals?</th><td>The published local annual schedule and Ordinance §37.3 describe unit/tenancy rules; no general owner-size tier is identified in those rules.</td><td>For locally controlled units, use the same City schedule regardless of whether the owner is a person or an entity, subject to the unit’s actual coverage and other exceptions.</td><td>{cite("SF01", "Annual-rate schedule")} · {cite("SF08", "Ordinance §37.3")}</td></tr>
<tr><th scope="row">Can ownership structure matter under state law?</th><td>Yes, but for narrow statutory exemptions. For some single-family/condominium exemptions, ownership by a REIT, corporation, or LLC with a corporate member is disqualifying, and required written notice is part of the test. Other exemptions have their own criteria.</td><td>Entity type can affect whether AB 1482 applies in a specific property scenario; it does not create a blanket corporate rent cap or blanket individual-owner exemption. No entity/property documentation was supplied.</td><td>{cite("CA01", "Civil Code §1947.12")} · {cite("SF15", "City AB 1482 guide")}</td></tr>
<tr><th scope="row">Should both units be raised to avoid a discrimination complaint?</th><td>Fair-housing and anti-retaliation rules govern rental terms and decision-making. Equal treatment is not a defense to an unlawful amount or discriminatory motive.</td><td>Do not raise both solely for appearances. Apply objective, documented criteria to each tenancy; different histories can lawfully produce different results, subject to counsel’s review.</td><td>{cite("CA04", "Government Code §12955")} · {cite("CA03", "Civil Code §1942.5")} · {cite("US02", "Federal terms/conditions rule")}</td></tr>
<tr><th scope="row">Is there a verified “normal” corporate or individual practice for 94122?</th><td>No owner-size-specific practice data was identified in the official material reviewed. No neighborhood-specific “normal increase” source was identified either.</td><td>Do not use anecdotes or a market listing as legal authority. Separate empirical practice questions from the legal amount that may be imposed on a particular unit.</td><td>{cite("SF01", "City rate schedule")} · {cite("SF14", "Limits on comparable-rent petitions")}</td></tr>
</tbody></table></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Prudent practice, not a claim about the market</p><h2>A defensible owner workflow</h2></div></div><div class="card-grid two"><article class="card"><h3>Keep a unit-level ledger</h3><p>For each tenancy, record lawful base rent, every effective increase, the notice and service proof, separate passthroughs, tenant/occupant continuity, current lease term, annual-rate source, and license status.</p><p>{cite("SF05", "Banking records")} · {cite("SF09", "License status")}</p></article><article class="card"><h3>Use a neutral policy</h3><p>Apply the same checklist—not necessarily the same dollar figure—to similarly situated units. Document why each unit is eligible on its own facts; avoid decisions linked to protected status or protected tenant activity.</p><p>{cite("CA04", "Fair-housing rule")} · {cite("CA03", "Retaliation rule")}</p></article><article class="card"><h3>Substantiate exceptional paths</h3><p>Do not self-create capital, O&amp;M, comparable-rent, or passthrough charges. Identify the exact Rent Board procedure, supporting invoices/calculation, and decision or form.</p><p>{cite("SF12", "Petitions and passthroughs")} · {cite("SF13", "Capital improvements")} · {cite("SF14", "Comparable-rent petitions")}</p></article><article class="card"><h3>Invite review without overstating</h3><p>Give a plain-language component breakdown and preserve records. Do not say “attorney approved” unless an attorney actually reviewed the complete records and expressly approved the specific notice.</p><p>{cite("SF08", "Notice breakdown")} · {cite("SF18", "Tenant review route")}</p></article></div></section>

<section class="notice-strip"><div class="notice-icon" aria-hidden="true">i</div><div><h2>Bottom line on company vs. individual owners</h2><p>The key variables here are the dwelling’s legal status, tenancy history, lawful base rent, effective date, and any subsidy/contract—not a generalized stereotype about owner size. A specific AB 1482 exemption may turn on entity type, but the evidence must satisfy every statutory condition.</p><p class="source-row">{cite("SF07", "Local coverage")} · {cite("CA01", "State exemption text")}</p></div></section>''',
    },
    {
        "file": "tenant-help.html",
        "nav": "Tenant help",
        "title": "Tenant counseling and legal help",
        "eyebrow": "Free help exists; full attorney representation is not guaranteed",
        "description": "Official San Francisco resources for rent-increase questions, free counseling, legal help, and rent-history petitions.",
        "body": f'''<header class="page-intro"><p class="kicker">06 / Tenant resources</p><h1>Yes—free help is available, with important limits.</h1><p class="lead">San Francisco offers free Rent Board counseling and directs tenants to community organizations. Free lawyer help is available in some settings—especially a pending eviction case—but the City does not promise free attorney representation for every ordinary rent-increase dispute.</p></header>

<section class="section-block"><div class="table-wrap"><table><thead><tr><th scope="col">Resource</th><th scope="col">What the official source says</th><th scope="col">Limit / caution</th><th scope="col">Official directory or process</th></tr></thead><tbody>
<tr><th scope="row">San Francisco Rent Board counselor</th><td>Free counseling on Rent Ordinance topics, by phone or in person; multilingual support is available.</td><td>It is not legal advice. Phone calls are generally limited to 5 minutes and office visits to 10 minutes; wait times can occur.</td><td>{cite("SF17", "Cost, hours, and limits")}</td></tr>
<tr><th scope="row">Tenant counseling organizations</th><td>The City lists organizations that assist tenants who receive eviction or rent-increase notices and other housing issues.</td><td>Service, language, eligibility, appointment, and capacity vary. Call the current provider before relying on an older schedule.</td><td>{cite("SF16", "Current City resource directory")}</td></tr>
<tr><th scope="row">Free legal help for an eviction case</th><td>The City directs a tenant who has received eviction court papers to contact Eviction Defense Collaborative immediately for free legal help.</td><td>This specific free-lawyer statement is about pending eviction court papers. It is not a promise of counsel for a routine rent-increase review.</td><td>{cite("SF16", "City eviction-help guidance")}</td></tr>
<tr><th scope="row">Free/limited legal clinics and referrals</th><td>The Rent Board’s January 2025 referral listing described free counseling at Housing Rights Committee (with proof-of-income note) and a Bar Association clinic offering free, limited legal advice/referrals to low-income Bay Area residents.</td><td>This listing is dated. Confirm current schedule, income/area eligibility, case scope, and capacity. Limited advice is not the same as full representation.</td><td>{cite("SF19", "Dated City referral listing")}</td></tr>
<tr><th scope="row">Rent-history or unlawful-increase petition</th><td>A covered tenant may request a lawful-rent determination or report an unlawful increase; the City says there is no filing fee and no time limit. The hearing process is designed so a lawyer is not required, though a party may have one.</td><td>Coverage and forms still matter. The tenant must support the claim with leases, notices, receipts, or other rent-history records.</td><td>{cite("SF18", "Eligibility, fee, and hearing process")}</td></tr>
</tbody></table></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">What a tenant-side reviewer may check</p><h2>Expect the arithmetic and process to be tested.</h2></div></div><div class="card-grid two"><article class="card"><h3>Amount and coverage</h3><ul class="tight-list"><li>Is this unit subject to local rent control, AB 1482, a subsidy, or an exemption?</li><li>Is the stated rent the lawful base, separated from passthroughs?</li><li>Does the increase use the correct effective-date annual rate?</li><li>Were banked percentages actually available, added rather than compounded, and documented?</li></ul><p>{cite("SF07", "Coverage")} · {cite("SF05", "Banking")} · {cite("SF18", "Rent history")}</p></article><article class="card"><h3>Timing, license, and motive</h3><ul class="tight-list"><li>Was a current Rent Board license in place?</li><li>Was the notice delivered with the required lead time and component detail?</li><li>Did an occupant change get misused as a market reset?</li><li>Is there a fair-housing or retaliation concern based on the facts and timeline?</li></ul><p>{cite("SF09", "License")} · {cite("SF08", "Notice contents")} · {cite("SF10", "Roommates")} · {cite("CA03", "Retaliation")}</p></article></div></section>

<div class="callout callout-blue"><b>For a landlord preparing a review:</b> do not rely on the tenant’s access to counseling as a substitute for complying with the law. Preserve the complete unit file, make the amount reproducible, and have counsel review any banked or petition-based increase.</div>''',
    },
    {
        "file": "review-checklist.html",
        "nav": "Records for counsel",
        "title": "Records and questions for counsel",
        "eyebrow": "Keep sensitive records private; share them directly with counsel",
        "description": "A private-document checklist and unresolved fact questions for lawyer review of a San Francisco rent increase.",
        "body": f'''<header class="page-intro"><p class="kicker">07 / Attorney-review packet</p><h1>Close the record gaps before choosing a number.</h1><p class="lead">This list is designed to make a lawyer’s review faster and more reliable. Do not upload tenant names, signatures, lease scans, or payment records to a public repository or public website.</p></header>

<section class="section-block"><div class="card-grid two"><article class="card"><span class="card-index">A / COVERAGE</span><h2>Confirm each unit’s legal status</h2><ul class="check-list"><li>Private address and unit identifier for counsel’s confidential use; verify construction date and residential use.</li><li>Dwelling type: apartment, single-family home, condo, accessory unit, substantially rehabilitated unit, or other classification.</li><li>Prior Rent Board coverage/exemption determinations and any Costa-Hawkins issue.</li><li>Whether any voucher, subsidy, HAP contract, regulatory agreement, deed restriction, or other program applies.</li><li>Property ownership/management entity and any fact needed for a state-law exemption.</li><li>Current Housing Inventory submission and rent-increase license for each covered unit.</li></ul><p>{cite("SF07", "Local coverage guide")} · {cite("SF09", "Housing Inventory") } · {cite("CA01", "State-cap exemptions")} · {cite("US03", "Voucher rule, if relevant")}</p></article>
<article class="card"><span class="card-index">B / RENT RECORD</span><h2>Rebuild the lawful base and timeline</h2><ul class="check-list"><li>Every signed lease, renewal, addendum, and written occupancy/roommate agreement.</li><li>Complete rent ledger from the tenancy start: every rent amount, effective date, notice, and payment record.</li><li>Separate base rent from utility, tax, capital, or other passthroughs.</li><li>Copies of every prior notice and proof of personal service or mailing, including any 2020 notice effective during the COVID rent freeze and any later reinstatement notice.</li><li>Current month-to-month or fixed-term status and any term/renewal limits.</li><li>Tenant/occupant timeline: who was an original tenant, who remains, co-tenant vs. subtenant status, and any formal termination or assignment.</li></ul><p>{cite("SF05", "Banking records")} · {cite("SF06", "Multi-year method")} · {cite("SF11", "Original-occupant rules")} · {cite("CA02", "Notice law")}</p></article>
<article class="card"><span class="card-index">C / SUPPORT</span><h2>Substantiate anything beyond annual rent</h2><ul class="check-list"><li>Official annual-rate table for every relevant effective-date year.</li><li>For banked increases, a year-by-year calculation showing eligibility, no compounding, and the lawful base.</li><li>For a petition or passthrough: filed petition, Rent Board decision/certification, invoices, comparison periods, prescribed forms, hardship information if relevant, and service proof.</li><li>Any prior tenant petitions or Rent Board rent-history determinations.</li><li>Voucher/PHA approvals or program correspondence, if assistance applies.</li></ul><p>{cite("SF03", "Rate table")} · {cite("SF12", "Petitions/passthroughs")} · {cite("SF13", "Capital improvements")} · {cite("SF14", "Comparable-rent route")}</p></article>
<article class="card"><span class="card-index">D / NEUTRALITY</span><h2>Check fair-housing and retaliation context</h2><ul class="check-list"><li>Use the same eligibility checklist for similarly situated units, while calculating each unit separately.</li><li>Review the chronology of repair/code complaints, accommodation requests, protected tenant activity, and decision-making.</li><li>Document the lawful category and arithmetic—not a tenant’s protected status or an unsupported assumption.</li><li>Obtain attorney review of the proposed notice and service plan before use.</li></ul><p>{cite("CA04", "California fair-housing law")} · {cite("CA03", "California anti-retaliation law")} · {cite("US01", "Federal Fair Housing Act")}</p></article></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Questions to resolve</p><h2>Open issues for the attorney</h2></div></div><ol class="numbered-list"><li>What is the lawful base rent and last actual rent-increase date for each unit?</li><li>Is each unit covered by the San Francisco annual allowance, AB 1482, a more specific program/contract, or an exemption?</li><li>For Unit A, does the reported April 2026 occupant/rent snapshot represent a new lease, a roster change, a rent change, or only a bookkeeping date? Does at least one original tenant remain as a co-tenant?</li><li>For Unit B, were any increases imposed after June 1, 2019? If not, which annual percentages are banked and what is the first lawful effective date after valid notice?</li><li>Is the current Housing Inventory license effective for each unit on the proposed rent-increase date?</li><li>Which notice period, delivery method, forms, and component breakdown apply, considering the lease term and any subsidy?</li><li>Does any protected activity, accommodation, protected status, or disparate treatment create a timing or fair-housing concern?</li></ol><p class="fine-print">The public site intentionally omits the street address and tenant identities. Give counsel the complete, unredacted records privately; do not publish them.</p></section>

<div class="notice-strip"><div class="notice-icon" aria-hidden="true">!</div><div><h2>No attorney approval is implied</h2><p>This packet is research and issue spotting. It is not a legal opinion, does not guarantee compliance, and has not been approved by an attorney. A lawyer must review the actual leases, rent ledger, property classification, notices, and current law before any increase is served.</p></div></div>''',
    },
    {
        "file": "repository-audit.html",
        "nav": "Repository audit",
        "title": "Repository scope and deployment",
        "eyebrow": "Rental work is isolated; the prior NBA project remains untouched",
        "description": "Repository review and GitHub Pages configuration notes for the isolated San Francisco rental review site.",
        "body": f'''<header class="page-intro"><p class="kicker">09 / Repository audit</p><h1>This repository was not built for rental law.</h1><p class="lead">The existing root project is an unrelated NBA research/dashboard site. The rental review is deliberately served from its own directory and does not replace or modify the prior work.</p></header>

<section class="section-block"><div class="two-col"><article class="card"><span class="card-index">PRE-EXISTING PROJECT</span><h2>Root site preserved</h2><ul class="check-list"><li>The root <code>index.html</code>, generated NBA pages, NBA documentation, and existing canonical-site validation workflow belong to a separate project.</li><li>A repository search before adding this site found no existing rental-law analysis or tenant records.</li><li>No NBA HTML, generator, documentation, workflow, or root Pages configuration was changed for this deliverable.</li></ul></article><article class="card"><span class="card-index">ISOLATED DELIVERABLE</span><h2>One new path</h2><ul class="check-list"><li>All rental-site pages, source registry, styles, and checks are under <code>rental-sf/</code>.</li><li>The site is static HTML/CSS with no backend, analytics, external JavaScript, or private tenant data.</li><li>Pages navigation and assets use relative paths so the subdirectory works under the repository’s GitHub Pages URL.</li></ul></article></div></section>

<section class="section-block"><div class="section-heading"><div><p class="kicker">Pages configuration checked before publication</p><h2>Existing Pages uses the main-branch root.</h2></div></div><p>The GitHub Pages API reported the repository’s public site using the legacy Pages build, source branch <code>main</code>, path <code>/</code>, and HTTPS. Under that configuration, the isolated directory is served at the repository subpath after the change is merged and Pages rebuilds:</p><div class="url-box"><code>https://sassnarep3-star.github.io/Own4/rental-sf/</code></div><p>The root remains the pre-existing NBA site; the rental landing page is <code>/rental-sf/</code>. No Pages settings or existing workflow changes were required. After merge, confirm the deployment status and open the URL in a browser; a successful repository build alone does not prove the Pages deployment is live.</p></section>

<section class="section-block compact"><div class="section-heading"><div><p class="kicker">Integrity controls</p><h2>Scope and privacy checks</h2></div></div><ul class="check-list"><li>Only generic unit labels are used; tenant names and initials are omitted from public files.</li><li>Owner-supplied amounts/dates are labeled unverified and separated from legal conclusions.</li><li>Every data-table row links to an official government source for the legal rule it discusses; the site says expressly when that source cannot authenticate private tenancy facts.</li><li>The build verifier checks internal links, registered official-source links, HTTPS, and a source link in every table row.</li></ul><p><a href="sources.html">Open the source register →</a> · <a href="review-checklist.html">Open the private-record checklist →</a></p></section>''',
    },
]


def source_register_body() -> str:
    groups = [
        ("San Francisco: rates, coverage, and procedure", ["SF01", "SF02", "SF03", "SF04", "SF05", "SF06", "SF07", "SF08", "SF09", "SF10", "SF11", "SF12", "SF13", "SF14", "SF15", "SF20", "SF21"]),
        ("California, federal, and program rules", ["CA01", "CA02", "CA03", "CA04", "US01", "US02", "US03"]),
        ("Tenant assistance and review", ["SF16", "SF17", "SF18", "SF19"]),
    ]
    pieces = [
        '<header class="page-intro"><p class="kicker">08 / Primary-source register</p><h1>Every conclusion should be easy to check.</h1><p class="lead">This register prioritizes official City guidance, statutory text, and federal regulations. Each source was directly checked on the date shown or is explicitly marked as a dated directory.</p></header>',
        '<div class="callout callout-blue"><b>Rate status as of ' + AS_OF + ':</b> the official City sources establish 1.6% for effective dates through February 28, 2027. No official rate for March 1, 2027 onward was located. Current web pages can change; verify again before using a rate or notice.</div>',
    ]
    for heading, ids in groups:
        rows = []
        for source_id in ids:
            source = SOURCES[source_id]
            rows.append(
                '<tr>'
                f'<th scope="row">{escape(source_id)} · {escape(source["title"])}</th>'
                f'<td>{escape(source["agency"])}</td>'
                f'<td>{escape(source["use"])}<br><span class="fine-print">{escape(source["note"])}</span></td>'
                f'<td>{cite(source_id, "Open official source")}</td>'
                '</tr>'
            )
        pieces.append(
            '<section class="section-block">'
            f'<div class="section-heading"><div><p class="kicker">Official sources</p><h2>{escape(heading)}</h2></div></div>'
            '<div class="table-wrap"><table><thead><tr><th scope="col">Source</th><th scope="col">Publisher</th><th scope="col">How it is used</th><th scope="col">Link</th></tr></thead><tbody>'
            + ''.join(rows)
            + '</tbody></table></div></section>'
        )
    pieces.append(
        '<section class="section-block compact"><div class="section-heading"><div><p class="kicker">Research limits</p><h2>What these sources cannot prove</h2></div></div>'
        '<p>Government pages establish the legal framework and public rate tables. They do not prove the private rent paid, the last increase date, tenant identity/continuity, lease term, unit exemption, owner entity, or current license for an address not supplied. Those facts require private records or a unit-specific Rent Board/attorney review. The January 2025 referral listing is dated; contact providers to confirm current intake and availability.</p>'
        '<p>No official owner-size study documenting typical corporate-versus-individual increase practices in San Francisco was identified in the material reviewed. That is a research-scope limitation, not a claim that no such research exists anywhere.</p></section>'
    )
    return ''.join(pieces)


PAGES.append({
    "file": "sources.html",
    "nav": "Sources",
    "title": "Official source register",
    "eyebrow": "Primary and official sources · checked November 6, 2026",
    "description": "Official San Francisco, California, and federal sources for the rental increase analysis.",
    "body": source_register_body(),
})

NAV = [(page["file"], page["nav"]) for page in PAGES]


def render_page(page: dict[str, str]) -> str:
    nav_items = []
    for filename, label in NAV:
        active = ' aria-current="page" class="active"' if filename == page["file"] else ""
        nav_items.append(f'<a href="{escape(filename)}"{active}>{escape(label)}</a>')
    nav_html = ''.join(nav_items)
    title = f'{page["title"]} | SF rental review'
    body = page["body"]
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <meta name="description" content="{escape(page["description"], quote=True)}">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="assets/site.css">
  <link rel="icon" href="data:,">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="topline"><div class="container topline-inner"><span>SF RENT INCREASE REVIEW</span><span>Prepared {AS_OF} · Source-linked · For attorney review</span></div></div>
  <header class="site-header"><div class="container header-inner"><a class="brand" href="index.html" aria-label="SF rental review home"><span class="brand-mark">SF</span><span><b>Rental increase review</b><small>94122 · two reported units</small></span></a><nav class="site-nav" aria-label="Main navigation">{nav_html}</nav></div></header>
  <main id="main" class="container main-content">
    <div class="page-meta"><span>{escape(page["eyebrow"])}</span><span class="page-date">As of {AS_OF}</span></div>
    {body}
  </main>
  <footer class="site-footer"><div class="container footer-grid"><div><b>San Francisco rental increase review</b><p>Prepared {AS_OF}. Public source-linked research for two owner-reported units in ZIP 94122.</p></div><div><b>Important limitation</b><p>Not legal advice, a legal opinion, an attorney’s approval, or a guarantee of compliance. Verify current law and the complete private records with counsel.</p></div><div><b>Privacy</b><p>Tenant names and initials are not published. Do not upload leases, signatures, payment records, or private identities to this public site.</p></div></div><div class="container footer-bottom"><a href="sources.html">Official source register</a><span>Static site · no analytics · no external scripts</span></div></footer>
</body>
</html>
'''


def write_stylesheet() -> None:
    css = r'''@charset "UTF-8";
:root{--ink:#15283d;--muted:#5a6d7e;--navy:#12263d;--blue:#1c5974;--teal:#1d776d;--sand:#f4efe3;--paper:#fffefa;--canvas:#f5f7f6;--line:#dce4e5;--soft-blue:#eaf3f5;--soft-green:#e9f4ef;--soft-amber:#fff4dc;--danger:#7b4c10;--shadow:0 14px 34px rgba(20,43,60,.08);--radius:18px}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--canvas);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16px;line-height:1.62}a{color:#145875;text-decoration-thickness:1px;text-underline-offset:3px}a:hover{color:#0c3f59;text-decoration-thickness:2px}a:focus-visible,button:focus-visible{outline:3px solid #e5a83b;outline-offset:3px}.container{width:min(1190px,calc(100% - 40px));margin-inline:auto}.skip-link{position:absolute;left:-9999px;top:8px;background:#fff;padding:10px 14px;z-index:99}.skip-link:focus{left:12px}.topline{background:#0b1c2e;color:#ced9e0;font-size:.74rem;letter-spacing:.035em}.topline-inner{display:flex;justify-content:space-between;gap:16px;padding:8px 0}.site-header{background:var(--paper);border-bottom:1px solid var(--line)}.header-inner{min-height:78px;display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--ink);flex-shrink:0}.brand-mark{display:grid;place-items:center;width:43px;height:43px;border-radius:14px;background:var(--navy);color:white;font-size:.86rem;font-weight:800;letter-spacing:.04em}.brand b,.brand small{display:block;line-height:1.3}.brand b{font-size:.94rem}.brand small{color:var(--muted);font-size:.76rem;margin-top:3px}.site-nav{display:flex;align-items:center;gap:5px;overflow-x:auto;scrollbar-width:thin;padding:7px 1px;max-width:74%}.site-nav a{color:#42596b;text-decoration:none;white-space:nowrap;padding:7px 10px;border-radius:10px;font-size:.79rem;font-weight:650}.site-nav a:hover,.site-nav a.active{background:var(--soft-blue);color:#124b63}.site-nav a.active{box-shadow:inset 0 -2px 0 var(--teal)}.main-content{padding-top:34px;padding-bottom:70px}.page-meta{display:flex;justify-content:space-between;gap:14px;align-items:center;color:var(--muted);font-size:.77rem;border-bottom:1px solid var(--line);padding-bottom:13px;margin-bottom:30px}.page-date{white-space:nowrap}.hero-grid{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(280px,.7fr);gap:28px;align-items:stretch;padding:22px 0 18px}.hero-copy{padding:20px 0}.kicker{margin:0 0 8px;color:var(--teal);font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.hero-copy h1,.page-intro h1{margin:0 0 16px;font-size:clamp(2.1rem,5vw,3.65rem);line-height:1.06;letter-spacing:-.045em;max-width:850px}.lead{font-size:1.14rem;line-height:1.58;color:#4b6172;max-width:760px;margin:0 0 19px}.pill-row{display:flex;flex-wrap:wrap;gap:8px}.pill{background:var(--soft-green);color:#195a50;border:1px solid #cce3d8;border-radius:999px;padding:5px 11px;font-size:.74rem;font-weight:700}.pill-muted{background:#f0f3f4;color:#526676;border-color:#e1e7e8}.hero-note{background:var(--navy);color:white;border-radius:22px;padding:25px 26px;box-shadow:var(--shadow);position:relative;overflow:hidden}.hero-note:after{content:"";position:absolute;width:170px;height:170px;border:1px solid rgba(255,255,255,.12);border-radius:50%;right:-58px;top:-65px;box-shadow:0 0 0 20px rgba(255,255,255,.035),0 0 0 42px rgba(255,255,255,.025)}.hero-note .label,.label{display:block;font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.11em;color:#afd4d1}.hero-note strong{display:block;font-size:3.5rem;line-height:1.05;letter-spacing:-.05em;margin:10px 0}.hero-note p{position:relative;z-index:1;color:#d9e6ea;font-size:.9rem}.hero-note .source-row a{color:#bde2e4}.notice-strip{display:flex;gap:16px;align-items:flex-start;background:var(--soft-amber);border:1px solid #efdfb9;border-radius:var(--radius);padding:19px 22px;margin:22px 0 42px}.notice-strip h2{font-size:1.08rem;margin:0 0 5px}.notice-strip p{margin:0;color:#4d4a40}.notice-icon{display:grid;place-items:center;flex:0 0 31px;height:31px;border-radius:50%;background:#f0d28a;color:#513600;font-weight:900}.section-block{margin:49px 0}.section-block.compact{margin:34px 0}.section-heading{display:flex;justify-content:space-between;align-items:end;gap:22px;margin-bottom:17px}.section-heading h2{margin:0;font-size:1.75rem;line-height:1.22;letter-spacing:-.025em}.section-heading .kicker{margin-bottom:6px}.section-intro{max-width:410px;color:var(--muted);font-size:.91rem;margin:0}.card-grid{display:grid;gap:16px}.card-grid.two{grid-template-columns:repeat(2,minmax(0,1fr))}.card-grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.card{background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:22px;box-shadow:0 7px 20px rgba(28,54,70,.035)}.card h2,.card h3{margin:4px 0 9px;line-height:1.25;letter-spacing:-.015em}.card h2{font-size:1.32rem}.card h3{font-size:1.16rem}.card p{margin:9px 0;color:#43596a}.card-index{display:inline-block;color:var(--teal);font-size:.7rem;font-weight:850;letter-spacing:.12em}.card-blue{background:linear-gradient(145deg,#f0f7f8,#fffefa)}.card-sand{background:linear-gradient(145deg,#f7f1e6,#fffefa)}.mini-warning{background:#fff4dc;border-left:3px solid #d7a33e;padding:10px 12px;border-radius:0 10px 10px 0;font-size:.86rem!important}.source-row{font-size:.8rem;color:var(--muted);margin:13px 0 0!important}.source-link{display:inline-block;font-size:.8rem;font-weight:700;white-space:normal}.nav-card{display:block;min-height:190px;background:var(--paper);border:1px solid var(--line);border-radius:var(--radius);padding:20px;color:var(--ink);text-decoration:none;box-shadow:0 7px 20px rgba(28,54,70,.035);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}.nav-card:hover{transform:translateY(-3px);box-shadow:var(--shadow);border-color:#acc9ce;color:var(--ink)}.nav-card>span{color:var(--teal);font-size:.72rem;font-weight:850;letter-spacing:.12em}.nav-card h3{margin:10px 0 5px;font-size:1.05rem}.nav-card p{margin:0 0 13px;color:var(--muted);font-size:.88rem;line-height:1.48}.nav-card b{font-size:.82rem;color:#15546b}.two-col{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.two-col p{margin:0}.callout{border-radius:15px;padding:17px 20px;margin:22px 0;border:1px solid var(--line)}.callout-blue{background:var(--soft-blue);border-color:#cfe1e4}.callout-sand{background:#f8f2e7;border-color:#e9dcc2}.page-intro{padding:13px 0 11px;margin-bottom:26px}.page-intro h1{font-size:clamp(2rem,4vw,3.05rem);max-width:930px}.page-intro .lead{margin-bottom:0}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:15px;background:var(--paper);box-shadow:0 7px 20px rgba(28,54,70,.035)}table{border-collapse:collapse;width:100%;min-width:800px;font-size:.88rem;line-height:1.5}thead th{background:#eaf1f2;color:#234456;text-align:left;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;padding:13px 14px;border-bottom:1px solid var(--line)}tbody th,tbody td{padding:14px;border-bottom:1px solid #e5ebeb;vertical-align:top;text-align:left}tbody th{color:#20384b;font-size:.86rem;width:18%;background:#fbfcfa}tbody tr:last-child th,tbody tr:last-child td{border-bottom:0}tbody tr:nth-child(even) td{background:#fcfdfb}.table-note{color:var(--muted);font-size:.8rem;margin:10px 2px}.blank{display:inline-block;width:75px;height:1.1em;border-bottom:1px solid #8395a0;vertical-align:baseline}.fine-print{font-size:.78rem;color:var(--muted)}.draft-box{background:#f1f6f5;border:1px solid #cfe1dc;border-radius:16px;padding:22px}.draft-box .label{color:#20675e}.draft-box p{margin:8px 0}.check-list,.tight-list{padding-left:1.25rem;margin:11px 0}.check-list li,.tight-list li{padding:4px 0 4px 3px;color:#40586a}.check-list li::marker{color:var(--teal)}.numbered-list{padding-left:1.4rem}.numbered-list li{padding:7px 0 7px 5px}.numbered-list li::marker{color:var(--teal);font-weight:800}.url-box{background:#edf3f4;border:1px solid var(--line);border-radius:12px;padding:15px 18px;overflow-wrap:anywhere;margin:14px 0}.url-box code,code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;color:#174e65}.site-footer{background:#0d2034;color:#d9e4e8;padding:35px 0 22px}.footer-grid{display:grid;grid-template-columns:1.1fr 1.2fr 1fr;gap:28px}.footer-grid b{font-size:.88rem}.footer-grid p{font-size:.8rem;color:#b9c8d0;line-height:1.5;margin:7px 0}.footer-bottom{border-top:1px solid rgba(255,255,255,.18);margin-top:22px;padding-top:14px;display:flex;justify-content:space-between;gap:18px;font-size:.77rem;color:#afc0c9}.footer-bottom a{color:#bfe2e3}.page-meta span:first-child{max-width:76%}
@media(max-width:980px){.header-inner{align-items:flex-start;flex-direction:column;gap:6px;padding:13px 0}.site-nav{max-width:100%;width:100%}.hero-grid{grid-template-columns:1fr}.hero-note{max-width:700px}.card-grid.three{grid-template-columns:repeat(2,minmax(0,1fr))}.footer-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.footer-grid>div:last-child{grid-column:1/-1}}
@media(max-width:650px){.container{width:min(100% - 28px,1190px)}.topline-inner{font-size:.67rem;flex-direction:column;gap:0}.main-content{padding-top:23px}.page-meta{align-items:flex-start;flex-direction:column;gap:5px;margin-bottom:23px}.hero-grid{padding-top:4px}.hero-copy h1,.page-intro h1{font-size:2.22rem}.lead{font-size:1.02rem}.hero-note{padding:21px}.notice-strip{padding:16px;gap:11px}.section-block{margin:38px 0}.section-heading{align-items:flex-start;flex-direction:column;gap:8px}.section-heading h2{font-size:1.5rem}.card-grid.two,.card-grid.three,.two-col{grid-template-columns:1fr}.nav-card{min-height:0}.footer-grid{grid-template-columns:1fr;gap:15px}.footer-grid>div:last-child{grid-column:auto}.footer-bottom{flex-direction:column;gap:4px}.table-wrap{border-radius:12px}table{font-size:.82rem;min-width:740px}tbody th,tbody td,thead th{padding:11px}.card{padding:18px}}
@media print{body{background:white;font-size:11pt}.topline,.site-nav,.skip-link{display:none!important}.container{width:100%;max-width:none}.site-header{border:0}.main-content{padding-top:10px}.card,.table-wrap,.hero-note{box-shadow:none;break-inside:avoid}.site-footer{background:white;color:#222;border-top:1px solid #aaa}.footer-grid p,.footer-bottom{color:#444}.source-link{color:#111}.section-block{break-inside:auto}.table-wrap{overflow:visible}table{min-width:0;font-size:9pt}}
'''
    (ROOT / "assets").mkdir(parents=True, exist_ok=True)
    (ROOT / "assets" / "site.css").write_text(css, encoding="utf-8")


def build() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    write_stylesheet()
    for page in PAGES:
        (ROOT / page["file"]).write_text(render_page(page), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(PAGES)} pages in {ROOT}")


if __name__ == "__main__":
    build()
