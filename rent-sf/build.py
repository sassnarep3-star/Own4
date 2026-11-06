#!/usr/bin/env python3
"""Build the isolated, static San Francisco rental research dashboard."""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = {
 'annual': ('SF Rent Board · annual increases', 'https://www.sf.gov/learn-about-rent-increases-san-francisco'),
 'rates': ('SF Rent Board · current rates', 'https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit'),
 'bank': ('SF Rent Board · banking', 'https://www.sf.gov/information--banked-rent-increases'),
 'housing': ('SF Rent Board · coverage', 'https://www.sf.gov/learn-about-san-francisco-rental-laws'),
 'inventory': ('SF Rent Board · inventory', 'https://www.sf.gov/rent-board-housing-inventory'),
 'state': ('SF Rent Board · AB 1482', 'https://www.sf.gov/reports--california-tenant-protection-act-2019-ab-1482'),
 'notice': ('California Civil Code § 827', 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=827&lawCode=CIV'),
 'retaliation': ('California Civil Code § 1942.5', 'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1942.5.&lawCode=CIV'),
 'fair': ('California Civil Rights Department', 'https://calcivilrights.ca.gov/housing/'),
 'hud': ('HUD · fair housing', 'https://archives.hud.gov/offices/cpd/affordablehousing/modelguides/200510.pdf'),
 'room': ('SF Rent Board · roommate replacement', 'https://www.sf.gov/information--replacement-roommates'),
 'costa': ('SF Rent Board · subsequent occupants', 'https://www.sf.gov/information--rent-increases-under-section-614-and-costa-hawkins'),
 'petitions': ('SF Rent Board · landlord petitions', 'https://www.sf.gov/landlord-petitions-and-passthroughs'),
 'comps': ('SF Rent Board · special circumstances form', 'https://sf.gov/sites/default/files/2024-03/531%20Comps%20Petition%203.24.pdf'),
 'help': ('SF · tenant and landlord resources', 'https://www.sf.gov/tenant-and-landlord-resources'),
 'tenant': ('SF Rent Board · tenant petition', 'https://www.sf.gov/report-unlawful-rent-increase-or-request-review-your-rent-history'),
 'referral': ('SF Rent Board · referrals', 'https://sf.gov/information/rent-board-referral-listing'),
}
NAV = [('index.html','Overview'),('units.html','Unit analysis'),('rules.html','Rules & timing'),('fairness.html','Fairness & practice'),('notice.html','Notice & resources'),('flagged.html','Flagged for review')]

def link(key):
    label, url = S[key]
    return f'<a href="{escape(url, quote=True)}">{escape(label)} <span aria-hidden="true">↗</span></a>'
def table(headers, rows):
    h = ''.join(f'<th scope="col">{escape(x)}</th>' for x in headers) + '<th scope="col">Official source</th>'
    out = []
    for cells, sources in rows:
        assert len(cells) == len(headers) and sources
        out.append('<tr>' + ''.join(f'<td>{escape(x)}</td>' for x in cells) + '<td>' + '<br>'.join(link(s) for s in sources) + '</td></tr>')
    return '<div class="table-wrap"><table><thead><tr>'+h+'</tr></thead><tbody>'+''.join(out)+'</tbody></table></div>'

def page(file, title, kicker, intro, content):
    nav = ''.join('<a ' + ('aria-current="page" ' if f == file else '') + f'href="{f}">{label}</a>' for f,label in NAV)
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="An official-source San Francisco rent increase research dashboard."><title>{escape(title)} | Rent review SF</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to content</a><div class="shell"><aside><a class="brand" href="index.html"><span class="brand-icon">R</span><span>Rent review<small>SAN FRANCISCO</small></span></a><div class="nav-label">RESEARCH DASHBOARD</div><nav aria-label="Main navigation">{nav}</nav><div class="aside-note">Independent research<br><strong>Not legal advice</strong><br>Reviewed 06 Nov 2026</div></aside><main id="main"><header class="top"><span>RENTAL RESEARCH <span class="slash">/</span> {escape(kicker.upper())}</span><span class="status"><i></i> SOURCE-LED</span></header><section class="hero"><p class="eyebrow">SAN FRANCISCO · 94122</p><h1>{escape(title)}</h1><p class="intro">{intro}</p></section>{content}<footer>Prepared 6 November 2026 · Rates and rules can change. No tenant identities are published. <a href="flagged.html">Review limitations →</a></footer></main></div></body></html>'''
    (HERE / file).write_text(html, encoding='utf-8')

def section(title, subtitle, body):
    return f'<section class="section"><div class="section-heading"><div><h2>{title}</h2><p>{subtitle}</p></div></div>{body}</section>'

summary = table(['Question','Finding'],[
 (['Current local benchmark','1.6% annual allowable increase for effective dates March 1, 2026–February 28, 2027; not an obligation to raise rent.'],['rates','annual']),
 (['Conservative approach','Consider the same 0–1.6% annual-only policy for both units, applied only when each unit is eligible; do not assume banked amounts.'],['annual','bank']),
 (['Before any increase','Confirm lawful base rent, tenancy history, lease restrictions, last increase and a current rent increase license.'],['annual','inventory']),
 (['Fairness','Applying the same objective policy consistently is prudent; increasing only one unit is not automatically discrimination, and increasing both is not immunity.'],['fair','hud']),
 (['Independent review','A tenant may challenge an unlawful increase; a lawyer has not reviewed these specific tenancies.'],['tenant','help']),
])
page('index.html','A clearer view of rent increases','Overview','A practical, privacy-conscious guide to evaluating two reported rent-controlled units in the Outer Sunset.', '''<div class="metrics"><article><span>ANNUAL ALLOWABLE</span><strong>1.6<small>%</small></strong><p>Mar 2026 – Feb 2027</p></article><article><span>NOTICE AT ≤10%</span><strong>30 <small>days</small></strong><p>Plus mailing time, if applicable</p></article><article><span>RECOMMENDED LENS</span><strong>Annual only</strong><p>No assumed banked increases</p></article></div><div class="callout"><strong>Decision brief</strong><p>Use the local annual allowance as a ceiling for a cautious annual-only option, not a market-rate target. Eligibility, lawful rent and notice must be confirmed independently for each unit. A lower increase or no increase is also possible.</p></div>''' + section('Executive summary','The short answer, with official sources.',summary) + '''<div class="next"><div><span>START HERE</span><h2>See the unit-by-unit analysis</h2><p>Conditional arithmetic, tenancy changes, and open questions.</p></div><a class="button" href="units.html">Explore unit analysis <span>→</span></a></div><p class="fine">Information is educational, not legal advice or a legal opinion. Exact dates and rents below are user-reported, not verified property records; the official citations explain the rules, not those private facts.</p>''')

units_table = table(['Item','Officially verified property value','Status / next check'],[
 (['Unit 1: current lawful base rent and lease history','', 'Unverified. Review original lease, continuing agreement and full ledger privately.'],['annual','tenant']),
 (['Unit 1: original occupant remains','', 'User reports continuity, but original-occupancy and permanent-residence status are not independently verified.'],['room','costa']),
 (['Unit 2: current lawful base rent and last increase','', 'Unverified. Starting rent does not establish current base rent or an unused bank.'],['annual','tenant']),
 (['Both: rent control and license','', 'Reported covered; assess exemptions and confirm current license on effective date.'],['housing','inventory']),
])
page('units.html','Unit-by-unit analysis','Unit analysis','The math is illustrative—not a determination of lawful rent or a notice ready to serve.', '''<div class="callout warning"><strong>Private facts are not official-source verified.</strong><p>The following dates and amounts were supplied by the owner. They are preserved as reported, not verified facts. No names, initials, street address or identifying lease documents are published. Publishing exact dates, rents and neighborhood still creates some re-identification risk.</p></div><div class="unit-grid"><article class="unit"><div class="unit-top"><span>UNIT 01</span><span class="tag">REPORTED · UNVERIFIED</span></div><h2>Continuing tenancy</h2><p>Lease began February 1, 2025 at $3,995/month. A continuing tenancy was reported April 1, 2026 at $3,995/month, with one original occupant remaining and a replacement occupant.</p><div class="example"><span>ILLUSTRATIVE ANNUAL-ONLY MATH</span><strong>$3,995 × 1.6% = $63.92</strong><p>Hypothetical new base: $4,058.92/month, only if $3,995 is the lawful current base and all timing, lease, notice and license conditions are satisfied within the 1.6% period.</p></div><p class="fine">The February 1, 2026 anniversary fell in the 1.4% period. A later increase uses the rate effective on its actual effective date. A replacement roommate alone is not a basis for an extra charge. ''' + link('annual') + '''</p></article><article class="unit"><div class="unit-top"><span>UNIT 02</span><span class="tag">REPORTED · UNVERIFIED</span></div><h2>Longer tenancy</h2><p>Lease began June 1, 2019 at $3,150/month. The current rent and full increase history were not provided.</p><div class="example"><span>ILLUSTRATIVE ANNUAL-ONLY MATH</span><strong>$3,150 × 1.6% = $50.40</strong><p>Hypothetical new base: $3,200.40/month only if $3,150 is still the lawful current base and all timing, lease, notice and license conditions are satisfied within the 1.6% period.</p></div><p class="fine">A June anniversary is not a confirmed current anniversary: a later increase could have changed it. Do not treat the 2019 starting rent as verified current rent. ''' + link('annual') + '''</p></article></div>''' + section('Verification register','A blank value means property-specific confirmation is unavailable.',units_table) + '''<p class="fine">A first increase ordinarily becomes available after 12 months; later increases must be at least 12 months apart. If an increase occurs later, the effective date becomes the new anniversary. The 1.6% rate ends February 28, 2027; do not assume the subsequent rate. ''' + link('annual') + '''</p>''')

rules = table(['Topic','Rule or boundary'],[
 (['Coverage','Many pre–June 14, 1979 units may be covered; exceptions exist. The reported 1940 construction date and coverage are not independently verified.'],['housing']),
 (['Annual amount','The effective-date rate is 1.6% from March 1, 2026 through February 28, 2027; 1.4% applied March 1, 2025 through February 28, 2026.'],['rates']),
 (['Base and timing','Calculate on base rent, not temporary passthroughs; no rounding up to a dollar. Normally wait 12 months after the last increase.'],['annual']),
 (['Banking','A fully skipped increase banks only after 24 full months without any increase; partial-increase rules differ. Add eligible percentages; do not compound or prorate.'],['bank']),
 (['License','A current Rent Board rent increase license must be on file when an annual or banked increase takes effect.'],['inventory']),
 (['State law','The state AB 1482 cap is not a substitute for the stricter local annual cap for these assumed locally controlled units. Its 8.8% figure applies only to qualifying AB 1482 units during its stated period.'],['state']),
 (['Federal protections','Fair housing law prohibits covered discriminatory rental terms and retaliation; it is not a general nationwide annual percentage for these ordinary units. Subsidies or other programs may add rules.'],['hud','fair']),
 (['Other increases','Capital and operating-cost petitions have separate rules; some utility or bond passthroughs use worksheets. Do not simply add expenses to rent.'],['petitions']),
])
page('rules.html','Rules & timing','Rules and timing','Different legal layers apply. These are the official rules most relevant to the reported scenario.',section('The rulebook','Select any source to inspect the underlying agency guidance.',rules) + '<div class="callout"><strong>Rate is tied to the effective date.</strong><p>Do not assume a new annual rate after February 28, 2027. Different rules may apply to subsidies, fixed-term leases, special petitions or exemptions.</p></div>')

fairness = table(['Question','Evidence-based assessment'],[
 (['One unit or both?','Neither a one-unit increase nor a uniform increase alone establishes or disproves discrimination. Use documented, neutral criteria; assess each tenancy separately.'],['hud','fair']),
 (['Equal percentage or equal dollars?','A consistent annual-only percentage is a conservative policy choice, not a legal safe harbor. Different lawful histories can produce different dates or amounts.'],['annual','fair']),
 (['Tenant-friendly scrutiny','Check repairs, reductions in services, prior increases, protected complaints, affordability concerns and notice; offer a way to question or contest the calculation. No attorney has approved it.'],['tenant','retaliation']),
 (['Change in occupants','A replacement roommate with an existing tenant does not itself justify an extra increase. Vacancy-decontrol rules depend on specific facts and exceptions.'],['room','costa']),
 (['Corporate vs individual practice','No official source located quantifying typical SF increases by owner type. Do not assume either group always increases rent or uses the maximum. The same relevant rent-control and fair-housing rules apply irrespective of size, subject to coverage and exceptions.'],['annual','fair']),
 (['Costs and market rent','A routine annual allowance need not be described as a reimbursement for a particular expense. A low rent relative to market alone is not an extraordinary circumstance for a special-circumstances petition.'],['annual','comps']),
])
page('fairness.html','Fairness & practice','Fairness and practice','A defensible process is consistent, transparent and open to tenant scrutiny—not a guarantee against a claim.',section('Questions owners ask','Separate legal requirements from recommended business practice.',fairness) + '''<div class="callout"><strong>A conservative recommendation, not a market survey</strong><p>Consider the same annual-only policy for both units, up to 1.6% during the stated period, without assuming any banked increases. Offer more notice than the minimum and consider a smaller increase or none. Document neutral reasons and check each unit’s individual eligibility; do not use protected traits, complaints, or roommate replacement as a reason.</p></div>''')

notice = table(['Step','Action'],[
 (['1 · Audit privately','Obtain the leases, complete rent ledgers, records of increases and notices, license status, and any relevant repair or petition records. Do not publish them.'],['tenant','inventory']),
 (['2 · Check dates and amount','Confirm the lawful base and eligibility; apply the rate in effect on the effective date. Check fixed-term lease and any longer applicable notice requirements.'],['annual','notice']),
 (['3 · Serve written notice','For an increase of 10% or less counting relevant prior increases, provide at least 30 days; for more than 10%, 90 days. The Rent Board says add 5 days if mailed. Check the statute and method of service.'],['notice','annual']),
 (['4 · Explain transparently','Show old base, dollar and percentage increase, new base, effective date, and any banked portion. Provide a contact for questions. Do not treat this guide as a notice form.'],['annual','bank']),
 (['5 · Provide review options','The Rent Board can review lawful rent on a tenant petition. For independent legal advice use a qualified lawyer or tenant organization; city counseling is not a legal opinion.'],['tenant','referral']),
 (['6 · Keep proof','Keep a private copy of the notice, service record and calculation; consistently document neutral decisions.'],['notice','fair']),
])
resources = table(['Resource','What it offers'],[
 (['Rent Board counseling · 415-252-4600','Free information for tenants and landlords; not legal advice.'],['help','state']),
 (['Rent Board tenant petition','Tenant may challenge an increase or request determination of lawful rent.'],['tenant']),
 (['Eviction Defense Collaborative · 415-659-9184','The city identifies free legal help for tenants with eviction court papers; availability for ordinary increase review is not established.'],['help']),
 (['Tenant and landlord referral list','The city lists legal and counseling organizations; eligibility and availability vary.'],['referral']),
])
page('notice.html','Notice & resources','Notice and resources','A careful process supports an informed, challengeable decision. Do not serve a notice until the facts are checked.',section('Before communicating','A practical sequence for both units.',notice) + section('Independent help','Availability and scope depend on the provider.',resources))

flags = table(['ID / issue','What remains unverified or needs review'],[
 (['F01 · Coverage and building','1940 build year, exact property classification, ownership and exemptions are user-reported or unknown. The address was intentionally not collected or published.'],['housing']),
 (['F02 · Base rents and timing','All private lease dates and amounts are unverified. Unit 2 current rent, both lawful bases, actual anniversary dates and full ledgers are unknown.'],['annual','tenant']),
 (['F03 · License','Current Housing Inventory reporting and rent increase license status are unknown.'],['inventory']),
 (['F04 · Occupancy','Unit 1 continuity and occupancy status are user-reported only. Do not assume a new tenancy, market reset, or a §6.14/Costa-Hawkins entitlement.'],['room','costa']),
 (['F05 · Banked increases','No full history was provided; eligible banked percentages and total lawful rent remain blank. Do not impose them based on this report.'],['bank','tenant']),
 (['F06 · Lease and service','Fixed-term lease provisions, prior notices, service method, repair issues, subsidies and additional restrictions are unknown.'],['notice','tenant']),
 (['F07 · No legal clearance','No tenant advocate, attorney or Rent Board decision reviewed these facts. Legal compliance or absence of discrimination cannot be guaranteed.'],['fair','referral']),
 (['F08 · Typical market practice','No official dataset was found establishing typical Outer Sunset increases by corporate versus individual owners; any rate or comparison is unverified and left blank.'],['rates']),
 (['F09 · Public privacy','The repository and Pages site are public. Even without names or addresses, exact dates and rents alongside the neighborhood can be linkable to a property or household.'],['inventory']),
 (['F10 · Source irregularity','The Rent Board annual-increase page includes date inconsistencies in some worked examples. Use its rate table and general timing rules, not the erroneous example dates.'],['annual','rates']),
 (['F11 · Future rates','The official 2027–28 local annual rate is not established in the reviewed sources; leave future rate blank until published.'],['rates']),
])
page('flagged.html','Flagged for review','Flagged for review','Open issues are visible by design. A source link supplies the relevant rule; it does not verify a private fact.',section('Review register','These items are not legal findings and do not certify the property.',flags))
