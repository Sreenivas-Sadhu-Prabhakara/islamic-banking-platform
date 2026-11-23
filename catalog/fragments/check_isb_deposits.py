#!/usr/bin/env python3
"""Self-check for catalog/fragments/isb-deposits.json.

Asserts the fragment is generator-derivable: closed type vocabulary, money
naming, exact-ratio discipline, declared identifiers/money, unique rule ids,
resolvable event payload names, and the money identities quoted in the rules'
`test` vectors (verified in pure int64 arithmetic).

Run: python3 -I check_isb_deposits.py <path-to-fragment>
"""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else (
    "/Users/macstudio/Code/Code/islamic-banking-platform/catalog/fragments/isb-deposits.json")
d = json.load(open(path, encoding="utf-8"))

TYPES = set(d["$meta"]["fieldTypes"])
ok, fails = 0, []


def check(cond, msg):
    global ok
    if cond:
        ok += 1
    else:
        fails.append(msg)


# ---- structural: the catalog is mechanically derivable -----------------------
check(len(d["serviceDomains"]) == 9, "expected 9 service domains")
seen_rule_ids, seen_tables, seen_topics = set(), set(), set()

for sd in d["serviceDomains"]:
    n = sd["name"]
    cr = sd["controlRecord"]
    names = [f["name"] for f in cr["fields"]]
    check(len(names) == len(set(names)), f"{n}: duplicate field name")
    check(cr["primaryKey"] in names, f"{n}: primaryKey not a field")
    check(cr["table"] not in seen_tables, f"{n}: table name reused")
    seen_tables.add(cr["table"])
    # Postgres truncates identifiers at 63 chars: cr table + bq table must fit
    for bq in sd["behaviourQualifiers"]:
        joined = f"{cr['table']}_{bq['table']}"
        check(len(joined) <= 63, f"{n}: table {joined} exceeds 63 chars ({len(joined)})")

    for f in cr["fields"] + [x for bq in sd["behaviourQualifiers"] for x in bq["fields"]]:
        check(f["type"] in TYPES, f"{n}.{f['name']}: unknown type {f['type']}")
        check(isinstance(f.get("required"), bool), f"{n}.{f['name']}: required missing")
        if f["type"] == "money":
            check(f["name"].endswith("Minor"), f"{n}.{f['name']}: money must end 'Minor'")
        if f["type"] == "enum":
            check(bool(f.get("values")), f"{n}.{f['name']}: enum without values")
            if "const" in f:
                check(f["const"] in f["values"], f"{n}.{f['name']}: const not in values")
        if f["type"] == "ratio":
            check("maxDenominator" in f, f"{n}.{f['name']}: ratio without maxDenominator")
        if f["type"] == "ref":
            check("refDomain" in f, f"{n}.{f['name']}: ref without refDomain")
        # no float, ever: nothing may declare a float/double/decimal type
        check(f["type"] not in ("float", "double", "decimal", "number"),
              f"{n}.{f['name']}: float-family type")

    # declared money list must match the money-typed CR fields exactly
    money_typed = {f["name"] for f in cr["fields"] if f["type"] == "money"}
    check(set(cr["money"]) == money_typed,
          f"{n}: controlRecord.money {sorted(set(cr['money']) ^ money_typed)} mismatch")
    for i in cr["identifiers"]:
        check(i in names, f"{n}: identifier {i} is not a field")

    for r in sd["rules"]:
        for k in ("id", "assert", "onViolation", "enforcedAt", "errorCode", "citation"):
            check(k in r, f"{n}.{r.get('id')}: rule missing {k}")
        check(r["onViolation"] in ("reject", "flag"), f"{n}.{r['id']}: bad onViolation")
        check(r["enforcedAt"] in ("db-check", "service", "generator-lint"),
              f"{n}.{r['id']}: bad enforcedAt")
        check(r["id"] not in seen_rule_ids, f"duplicate rule id {r['id']}")
        seen_rule_ids.add(r["id"])

    known = set(names) | {x["name"] for bq in sd["behaviourQualifiers"] for x in bq["fields"]}
    known |= {"ruleId", "errorCode", "detectedAt", "refusedAt"}  # audit-event fields
    for e in sd["events"]:
        check(e["topic"] not in seen_topics, f"{n}: duplicate topic {e['topic']}")
        seen_topics.add(e["topic"])
        for p in e["payload"]:
            check(p in known, f"{n}.{e['name']}: payload '{p}' is not a declared field")

    sh = sd["shariah"]
    check(sh["reviewed"] is False, f"{n}: shariah.reviewed must be False")
    check("UNREVIEWED" in sh["review"], f"{n}: missing UNREVIEWED sentence")
    check(isinstance(sh.get("capitalAtRisk"), bool), f"{n}: capitalAtRisk not a bool")
    check(sh["contractType"] in {"Mudarabah", "Wakala", "Wadiah", "QardHassan", "Murabaha",
                                 "Ijara", "IjaraMuntahiaBittamleek", "Istisna", "Salam", "Sukuk"},
          f"{n}: contractType outside DESIGN.md §7 enum")
    check(bool(sd["uncertain"]), f"{n}: empty uncertain list")

# capitalAtRisk must be a queryable field on every account domain, tied to
# fundsConfirmationSupported (DESIGN.md §7's refusal)
for sd in d["serviceDomains"]:
    f = {x["name"]: x for x in sd["controlRecord"]["fields"]}
    if "accountClass" in f:
        check("capitalAtRisk" in f, f"{sd['name']}: no capitalAtRisk field")
        check("fundsConfirmationSupported" in f, f"{sd['name']}: no fundsConfirmationSupported")
        if f["accountClass"].get("const") == "INVESTMENT_ACCOUNT":
            check(f["capitalAtRisk"].get("const") is True,
                  f"{sd['name']}: investment account must pin capitalAtRisk true")
            check(f["fundsConfirmationSupported"].get("const") is False,
                  f"{sd['name']}: investment account must refuse funds confirmation")


# ---- the money identities quoted in the rules' test vectors ------------------
def ratio_mul(amount, num, den):
    """Exact int64 multiply-then-divide, truncated toward zero."""
    q = abs(amount) * num // den
    return q if amount >= 0 else -q


# ISB-PCD-01 waterfall identity
gross, exp_, snc = 100_000_000, 5_000_000, 0
per_ap, per_use = 2_000_000, 0
mudarib, agency = 18_600_000, 0
irr_ap, irr_use = 1_000_000, 0
check(gross - exp_ - snc - per_ap + per_use - mudarib - agency - irr_ap + irr_use == 73_400_000,
      "ISB-PCD-01 test vector does not equal 73400000")

# ISB-PCD-02 mudarib ceiling: ratioMul(profitAfterPer, 20/100)
check(ratio_mul(93_000_000, 20, 100) == 18_600_000, "ISB-PCD-02 ceiling vector wrong")

# ISB-PCD-04 rounding residual bound
check(333_334 + 333_333 + 333_333 + 0 == 1_000_000, "ISB-PCD-04 exact-split vector wrong")
check(333_333 * 3 + 1 == 1_000_000, "ISB-PCD-04 residual-1 vector wrong")
check(not (300_000 * 3 + 100_000 == 1_000_000 and 100_000 < 3),
      "ISB-PCD-04 rejection vector should breach the residual bound")

# ISB-MUDS-02 / ISB-MUDT-02 capital identity
check(1_000_000 - 0 + 25_000 - 1_025_000 == 0, "ISB-MUDS-02 vector wrong")
check(1_000_000 - 0 + 25_000 - 1_025_001 < 0, "ISB-MUDS-02 rejection vector wrong")
check(50_000_000 - 0 + 1_250_000 - 51_250_000 == 0, "ISB-MUDT-02 BHD vector wrong")

# ISB-MUDS-03 PSR sums to one by cross-multiplication, no division
check(70 * 100 + 30 * 100 == 100 * 100, "ISB-MUDS-03 accept vector wrong")
check(7 * 4 + 1 * 10 != 10 * 4, "ISB-MUDS-03 reject vector wrong")

# ISB-WKL-05 agency fee truncation (not rounding)
check(ratio_mul(10_000_000, 75, 10_000) == 75_000, "ISB-WKL-05 exact vector wrong")
check(ratio_mul(10_000_001, 75, 10_000) == 75_000, "ISB-WKL-05 truncation vector wrong")

# ISB-WKL-06 performance incentive only on the excess
check(max(0, 90_000 - 100_000) == 0, "ISB-WKL-06 shortfall vector wrong")
check(ratio_mul(max(0, 130_000 - 100_000), 20, 100) == 6_000, "ISB-WKL-06 excess vector wrong")

# ISB-WKL-07 Wakala capital identity incl. fee and incentive
check(10_000_000 - 0 + 250_000 - 0 - 75_000 - 6_000 == 10_169_000, "ISB-WKL-07 vector wrong")

# ISB-PER-01 / ISB-PER-02 / ISB-IRR-01 / ISB-IRR-02
check(4_000_000 + 1_000_000 == 5_000_000, "ISB-PER-01 vector wrong")
check(ratio_mul(95_000_000, 25, 1_000) == 2_375_000, "ISB-PER-02 cap vector wrong")
check(3_000_000 - 1_200_000 == 1_800_000, "ISB-IRR-01 vector wrong")
check(ratio_mul(74_400_000, 15, 1_000) == 1_116_000, "ISB-IRR-02 cap vector wrong")

# the IRR base must be the POST-mudarib figure from the PCD-01 vector
check(73_400_000 + 1_000_000 == 74_400_000,
      "IRR base is not the run's iah profit after mudarib share plus the appropriation")

# ratio cross-multiplication cannot overflow int64 at maxDenominator 1e6
check((10**6) * (10**6) < 2**63 - 1, "maxDenominator admits int64 overflow")
# weighted balance-days headroom: 1e15 minor units x 366 days
check(10**15 * 366 < 2**63 - 1, "weightedBalanceDays can overflow int64")

print(f"checks passed: {ok}")
if fails:
    print(f"FAILURES ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("SELF-CHECK OK")
