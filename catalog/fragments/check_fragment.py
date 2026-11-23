#!/usr/bin/env python3
"""Self-check for a Phase-4 catalog fragment (default: isb-operations.json).

Usage: python3 check_fragment.py [path/to/fragment.json]

Asserts the fragment conforms to its OWN declared conventions and to the existing
generator's assumptions. Exits non-zero on any failure.
"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # catalog/fragments/
FRAG = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "isb-operations.json"
LAND = HERE.parent / "islamic-service-landscape.json"
GEN = HERE.parent.parent / "generator" / "generate.py"

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)

d = json.loads(FRAG.read_text())
land = json.loads(LAND.read_text())

# --- 1. domain list matches the catalog for this business area, exactly
area = next(a for a in land["businessAreas"] if a["name"] == d["businessArea"])
expected = {(bd["name"], sd["name"], sd["functionalPattern"], sd["assetType"])
            for bd in area["businessDomains"] for sd in bd["serviceDomains"]}
actual = {(bd["name"], sd["name"], sd["functionalPattern"], sd["assetType"])
          for bd in d["businessDomains"] for sd in bd["serviceDomains"]}
check(expected == actual,
      f"domain list diverges from the catalog: missing={expected - actual} extra={actual - expected}")
check(d["serviceDomainCount"] == len(actual), "serviceDomainCount wrong")

# --- 2. functional patterns are ones generate.py already knows
patterns = dict(re.findall(r'"([A-Za-z ]+)": "([A-Za-z ]+)",', GEN.read_text()))
sds = [sd for bd in d["businessDomains"] for sd in bd["serviceDomains"]]
for sd in sds:
    check(sd["functionalPattern"] in patterns,
          f"{sd['name']}: pattern {sd['functionalPattern']} unknown to generate.py")
    # --- 3. controlRecord.name matches the generator's own derivation
    want = f"{sd['assetType']} {patterns.get(sd['functionalPattern'], '?')}"
    check(sd["controlRecord"]["name"] == want,
          f"{sd['name']}: controlRecord.name {sd['controlRecord']['name']!r} != generator "
          f"derivation {want!r}")

TYPES = set(d["conventions"]["fieldTypes"])
OPS = set(d["conventions"]["assertGrammar"]["op"])

for sd in sds:
    n = sd["name"]
    cr = sd["controlRecord"]
    fields = {f["name"]: f for f in cr["fields"]}
    check(len(fields) == len(cr["fields"]), f"{n}: duplicate field name")

    # --- 4. closed type vocabulary; enums carry values; money carries a currency field
    for f in cr["fields"]:
        check(f["type"] in TYPES, f"{n}.{f['name']}: type {f['type']!r} not in vocabulary")
        if f["type"] == "enum":
            check(f.get("values"), f"{n}.{f['name']}: enum with no values")
        if f["type"] == "money":
            check(f.get("currencyField") in fields,
                  f"{n}.{f['name']}: currencyField missing or not a field")
            check(f["name"].endswith("Minor"),
                  f"{n}.{f['name']}: money field must use the estate's *Minor suffix")

    # --- 5. controlRecord.money agrees with the typed fields
    for m in cr["money"]:
        check(m["name"] in fields and fields[m["name"]]["type"] == "money",
              f"{n}: money[] entry {m['name']} is not a money-typed field")
        check("currencyField" in m and "signed" in m,
              f"{n}: money[] entry {m['name']} missing currencyField/signed")
    typed_money = {f["name"] for f in cr["fields"] if f["type"] == "money"}
    check(typed_money == {m["name"] for m in cr["money"]},
          f"{n}: money[] {sorted(m['name'] for m in cr['money'])} != typed money fields "
          f"{sorted(typed_money)}")

    # --- 6. identifiers reference real fields (or are declared notes on refs)
    for i in cr["identifiers"]:
        check(i["name"] in fields, f"{n}: identifier {i['name']} is not a field")

    # --- 7. behaviour qualifiers: path slug, cardinality, typed fields
    bq_fields = {}
    for b in sd["behaviourQualifiers"]:
        check(re.fullmatch(r"[a-z0-9-]+", b["path"]),
              f"{n}: BQ path {b['path']!r} is not a URL slug")
        check(re.fullmatch(r"\d\.\.(\d|n)", b["cardinality"]),
              f"{n}: BQ {b['name']} cardinality {b['cardinality']!r} malformed")
        for f in b["fields"]:
            check(f["type"] in TYPES, f"{n}/{b['name']}.{f['name']}: bad type {f['type']!r}")
            if f["type"] == "enum":
                check(f.get("values"), f"{n}/{b['name']}.{f['name']}: enum with no values")
            if f["type"] == "money":
                check(f.get("currencyField"), f"{n}/{b['name']}.{f['name']}: money, no currency")
                check(f["name"].endswith("Minor"),
                      f"{n}/{b['name']}.{f['name']}: money field needs *Minor suffix")
            bq_fields[f["name"]] = b["name"]

    # --- 8. rules: complete, ids/codes unique, onViolation closed, cites non-empty
    ids, codes = set(), set()
    for r in sd["rules"]:
        for k in ("id", "assert", "onViolation", "code", "cite"):
            check(k in r, f"{n}: rule missing {k}: {r.get('id')}")
        check(r["onViolation"] in ("reject", "flag"),
              f"{n}/{r['id']}: onViolation {r['onViolation']!r} not reject|flag")
        check(re.fullmatch(r"ISB-[A-Z]{3}-\d{2}", r["id"]), f"{n}: rule id {r['id']!r} malformed")
        check(r["id"] not in ids, f"{n}: duplicate rule id {r['id']}")
        check(re.fullmatch(r"[A-Z0-9_]+", r["code"]), f"{n}/{r['id']}: code {r['code']!r} not UPPER_SNAKE")
        check(r["code"] not in codes, f"{n}: duplicate rule code {r['code']}")
        check(isinstance(r["cite"], list) and r["cite"], f"{n}/{r['id']}: empty cite")
        ids.add(r["id"]); codes.add(r["code"])

    # --- 9. events: topic namespace, payload fields resolvable
    known = set(fields) | set(bq_fields)
    for e in sd["events"]:
        check(re.fullmatch(r"isb\.[a-z0-9-]+\.[a-z0-9-]+", e["topic"]),
              f"{n}: topic {e['topic']!r} off convention isb.<group>.<subject>")
        check(isinstance(e["payload"], list) and e["payload"], f"{n}/{e['name']}: empty payload")
        for p in e["payload"]:
            check(p in known, f"{n}/{e['name']}: payload field {p!r} is not a CR or BQ field")

    # --- 10. shariah block honesty
    s = sd["shariah"]
    check(s["reviewed"] is False, f"{n}: shariah.reviewed is not False")
    check("UNREVIEWED" in s["reviewNote"], f"{n}: missing UNREVIEWED note")
    check(isinstance(s["standards"], list), f"{n}: standards not a list")
    for st in s["standards"]:
        for k in ("ref", "title", "clauseText", "source"):
            check(k in st, f"{n}: standard {st.get('ref')} missing {k}")
    check(isinstance(sd["uncertain"], list) and sd["uncertain"],
          f"{n}: uncertain[] empty — every domain must say what it could not model")

# --- 11. no float anywhere: money is int64 minor units, ratios are int pairs
def walk(o, path="$"):
    if isinstance(o, float):
        fails.append(f"FLOAT at {path}: {o}")
    elif isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]")
walk(d)

# --- 12. the fragment claims design-only
check("DESIGN" in d["status"].upper() and "generator was NOT run" in d["phase"],
      "fragment does not declare design-only status")

print(f"checked {len(sds)} service domains, "
      f"{sum(len(s['rules']) for s in sds)} rules, "
      f"{sum(len(s['events']) for s in sds)} events, "
      f"{sum(len(s['behaviourQualifiers']) for s in sds)} behaviour qualifiers")
if fails:
    print(f"\nFAIL ({len(fails)}):")
    for m in fails:
        print("  -", m)
    sys.exit(1)
print("PASS")
