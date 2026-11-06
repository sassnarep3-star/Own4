# Rent review SF

Static standalone research dashboard at `/Own4/rent-sf/`, as of November 6, 2026. Run `python3 rent-sf/build.py` and `python3 rent-sf/test_site.py` to reproduce and check. The tests cover every rendered table body row's official-domain link, local navigation, example arithmetic, and reproducibility; they do not certify truth or check the network. No client-side code, tracker or input form is used.

## Source review and limitations

Source URLs are printed on each relevant row. Read the San Francisco Rent Board annual-increase, current rates, banking, coverage, housing inventory, state AB 1482, roommate, Costa-Hawkins, landlord-petition, comparable-rents, unlawful-increase petition and referral pages; California Civil Code §§ 827 and 1942.5; the California Civil Rights Department housing page; HUD fair-housing guidance; and the city's tenant and landlord resources. The example calculations are derived arithmetic based on **unverified, user-reported** amounts, not official property data. The current base, lease terms, actual anniversary and licensing of each unit were not verified; property-specific verified-value cells are intentionally blank. Rate, notice and banking claims were reconciled against the linked agency text; the board's own worked examples have date inconsistencies, flagged on the site. Sources can change.

The public site intentionally omits all names, initials and specific address. User-requested exact lease dates, monthly rents and zip remain, and can increase re-identification risk. This public repository is not a private records vault. No attorney or agency reviewed the actual tenancies, and nothing here is a legal determination or notice to serve.
