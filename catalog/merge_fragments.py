#!/usr/bin/env python3
"""Fold the Phase-4 design fragments into catalog/islamic-service-landscape.json.

Five area agents plus the missing-cores agent each wrote a fragment in their own
dialect.  This script is the ONLY writer of the enriched catalog: it normalises
those dialects into catalog schema v2 (islamic-service-landscape.schema.json)
and merges them into the existing top-level shape
(version / title / note / functionalPatterns / businessAreas) so an
un-upgraded reader still sees {name, functionalPattern, assetType}.

Re-runnable and deterministic: same fragments in, byte-identical catalog out.

    python3 catalog/merge_fragments.py            # write the catalog
    python3 catalog/merge_fragments.py --check    # report only, write nothing

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAGMENTS = HERE / "fragments"
CATALOG = HERE / "islamic-service-landscape.json"
REPORT = HERE / "merge-report.json"

CATALOG_SCHEMA_VERSION = "2.0.0"

# ---------------------------------------------------------------- dialect maps

# Field-type aliases.  Left = what a fragment wrote, right = schema v2 type.
# Every alias here is a rename only; none changes the meaning of the datum.
TYPE_ALIASES = {
    "moneyMinor": "money",      # isb-financing's name for the same int64 minor units
    "text": "string",
    "uuid": "string",
    "digest": "string",
    "uri": "string",
    "iso4217": "currency",
    "iso3166Alpha2": "countryCode",
    "rate": "ratio",            # isb-treasury; a rate is an exact ratio, never a float
    "quantity": "int64",        # unit counts (sukuk certificates); integral by construction
}

# A ratio is compared by cross-multiplication in int64, so its denominator must
# be bounded or the comparison can overflow.  Fragments that gave a ratio field
# no bound get this one, flagged, so the bound is visible rather than implicit.
# 10^6 keeps every product of two ratios below 10^12.
DEFAULT_MAX_DENOMINATOR = 1_000_000

# Standards bodies this estate cites.  Used only to lift a body out of a code
# string that already names it — never to attribute a citation that does not.
KNOWN_BODIES = {"AAOIFI", "IFSB", "BNM", "ISO", "OBIE", "SAMA", "CBB", "DFSA",
                "IASB", "REGULATOR"}

CANONICAL_TYPES = {
    "id", "ref", "string", "enum", "bool", "int32", "int64",
    "money", "ratio", "currency", "countryCode", "date", "timestamp",
    "period", "array",
}

# Per-domain rule keys: fragments used three names for the citation and four for
# the free-text rationale.  Collapse, never drop: a dropped citation is a lost
# provenance claim.
RULE_CITATION_KEYS = ("citation", "cite", "standards")
RULE_NOTE_KEYS = ("note", "rationale", "statement")

BQ_ACTION_KEYS = ("actions", "actionTerms")

# Functional pattern -> control-record noun.  Duplicated from generate.py on
# purpose: the merge must be runnable without importing the generator.
PATTERN_NOUN = {
    "Direct": "Strategy", "Manage": "Management Plan",
    "Administer": "Administrative Plan", "Process": "Procedure",
    "Operate": "Operating Session", "Maintain": "Maintenance Agreement",
    "Catalog": "Directory Entry", "Monitor": "Monitoring State",
    "Track": "Tracking Position", "Fulfill": "Fulfillment Arrangement",
    "Transact": "Transaction", "Register": "Registration",
    "Assess": "Assessment", "Distribute": "Distribution", "Plan": "Plan",
}


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def snake(text: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", s.lower())).strip("_")


def as_list(value) -> list:
    """A fragment wrote either a list or one comma-joined string. Accept both."""
    if value is None:
        return []
    if isinstance(value, list):
        return [v for v in value if v not in (None, "")]
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    return [value]


def named_list(value) -> list[dict]:
    """controlRecord.money / .identifiers / .ratios came as either a list of
    field names or a list of objects keyed `field` or `name`.  Return objects."""
    out = []
    for item in as_list(value):
        if isinstance(item, dict):
            name = item.get("field") or item.get("name")
            if name:
                out.append({**item, "name": name})
        elif isinstance(item, str):
            out.append({"name": item})
    return out


# ------------------------------------------------------------- fragment reader

def fragment_domains(path: Path) -> tuple[list[dict], dict]:
    """Yield service domains from either fragment shape, carrying businessDomain."""
    doc = json.loads(path.read_text())
    out = []
    if "serviceDomains" in doc:                      # isb-deposits shape
        for sd in doc["serviceDomains"]:
            out.append(dict(sd))
    for bd in doc.get("businessDomains", []):        # every other fragment
        for sd in bd.get("serviceDomains", []):
            sd = dict(sd)
            sd.setdefault("businessDomain", bd.get("name"))
            out.append(sd)
    for sd in out:
        sd["$fragment"] = path.name
    return out, doc


# -------------------------------------------------------------- normalisation

def normalise_field(fld: dict, where: str, errors: list[str]) -> dict:
    name = fld.get("name")
    if not name:
        errors.append(f"{where}: a field has no name")
        return {}
    raw_type = fld.get("type")
    ftype = TYPE_ALIASES.get(raw_type, raw_type)
    if ftype not in CANONICAL_TYPES:
        errors.append(f"{where}.{name}: unknown field type {raw_type!r}")
    out = {"name": name, "type": ftype, "required": bool(fld.get("required"))}
    if raw_type != ftype:
        out["sourceType"] = raw_type          # keep the fragment's word, auditable
    for key in ("values", "const", "default", "note", "description", "items",
                "itemsRef", "min", "max", "maxLength", "maxDenominator",
                "signed", "derived", "immutableAfter", "nonNegative", "unitField"):
        if key in fld:
            out[key] = fld[key]
    # refDomain / sourceDomain are the same datum under two names.
    ref = fld.get("refDomain") or fld.get("sourceDomain")
    if ref:
        out["refDomain"] = ref
    # currencyField / currency both point at the field carrying the ISO code.
    cur = fld.get("currencyField") or fld.get("currency")
    if cur:
        # two fragments wrote `record.<field>` / `cr.<field>`
        out["currencyField"] = str(cur).split(".")[-1]
    if ftype == "ratio" and "maxDenominator" not in out:
        out["maxDenominator"] = DEFAULT_MAX_DENOMINATOR
        out["maxDenominatorDefaulted"] = True
    # `items` for an array field came as a type word, an object, or a list of
    # field definitions.  Normalise the list form so the renderer has one shape.
    if isinstance(out.get("items"), list):
        out["items"] = [nf for nf in (normalise_field(i, f"{where}.{name}[]", errors)
                                      for i in out["items"]) if nf]
    out["column"] = snake(name)
    return out


def normalise_rule(rule: dict, where: str, errors: list[str]) -> dict:
    rid = rule.get("id")
    expr = rule.get("assert")
    if not rid or not expr:
        errors.append(f"{where}: a rule is missing id or assert")
        return {}
    out = {
        "id": rid,
        "assert": expr,
        "onViolation": rule.get("onViolation", "reject"),
    }
    code = rule.get("errorCode") or rule.get("code")
    if code:
        out["errorCode"] = code
    cite = []
    for k in RULE_CITATION_KEYS:
        cite.extend(as_list(rule.get(k)))
    if cite:
        out["citation"] = cite
    note = [str(rule[k]) for k in RULE_NOTE_KEYS if rule.get(k)]
    if note:
        out["note"] = " — ".join(note)
    for key in ("enforcedAt", "severity", "appliesTo", "scope", "emits",
                "dependsOn", "test", "testVectors", "examples", "citationStatus"):
        if key in rule:
            out[key] = rule[key]
    return out


def normalise_bq(bq: dict, where: str, errors: list[str]) -> dict:
    name = bq.get("name")
    if not name:
        errors.append(f"{where}: a behaviour qualifier has no name")
        return {}
    actions = []
    for k in BQ_ACTION_KEYS:
        actions.extend(as_list(bq.get(k)))
    out = {
        "name": name,
        "path": bq.get("path") or slug(name),
        "table": bq.get("table") or snake(name),
        "cardinality": bq.get("cardinality", "0..n"),
        "actions": sorted(set(actions)) or ["Retrieve"],
        "fields": [],
    }
    for fld in bq.get("fields", []):
        nf = normalise_field(fld, f"{where}.bq[{name}]", errors)
        if nf:
            out["fields"].append(nf)
    for key in ("note", "bianBQ", "bianProvenance", "bianArchetype",
                "backingField", "evidence"):
        if key in bq:
            out[key] = bq[key]
    # A BQ with no fields is a documented intent, not a sub-resource. Keep it
    # flagged rather than silently generating an empty table.
    if not out["fields"]:
        out["noSchema"] = True
    return out


def normalise_event(ev: dict, where: str, area_ns: str, sd_slug: str,
                    errors: list[str]) -> dict:
    name = ev.get("name")
    if not name:
        errors.append(f"{where}: an event has no name")
        return {}
    topic = ev.get("topic") or f"{area_ns.replace('-', '.')}.{sd_slug}.{slug(name)}"
    out = {"name": name, "topic": topic, "payload": as_list(ev.get("payload"))}
    for key in ("trigger", "keyField", "consumers", "note"):
        if key in ev:
            out[key] = ev[key]
    return out


def normalise_domain(sd: dict, area: str, area_ns: str,
                     errors: list[str]) -> dict:
    name = sd["name"]
    where = name
    pattern = sd["functionalPattern"]
    asset = sd["assetType"]
    cr_in = sd.get("controlRecord") or {}
    sd_slug = slug(name)

    fields = []
    for fld in cr_in.get("fields", []):
        nf = normalise_field(fld, where, errors)
        if nf:
            fields.append(nf)

    by_name = {f["name"]: f for f in fields}

    # money[] / identifiers[] / ratios[] restate fields[] and carry extra
    # attributes (currencyField, signed, nonNegative, format).  Fold those onto
    # the field — fields[] is the single authority the generator reads — and
    # report any name that is not a field rather than trusting the restatement.
    money_decl = named_list(cr_in.get("money"))
    ident_decl = named_list(cr_in.get("identifiers"))
    ratio_decl = named_list(cr_in.get("ratios"))
    declared_pk = None
    for group, decls in (("money", money_decl), ("identifiers", ident_decl),
                         ("ratios", ratio_decl)):
        for decl in decls:
            fld = by_name.get(decl["name"])
            if fld is None:
                errors.append(f"{where}: controlRecord.{group} names "
                              f"{decl['name']!r} which is not a control-record field")
                continue
            for key in ("currencyField", "signed", "nonNegative", "format",
                        "constraint", "unit"):
                if key in decl and key not in fld:
                    fld[key] = decl[key]
            if decl.get("primary") is True or decl.get("role") == "primary" \
                    or decl.get("kind") == "primary":
                declared_pk = decl["name"]

    pk = cr_in.get("primaryKey") or declared_pk
    if pk and pk in by_name and by_name[pk]["type"] == "string":
        # `id` and `string` both generate VARCHAR(64)/String, so a primary key
        # the fragment typed `string` is retyped rather than rejected — but the
        # fragment's word is kept so the slip stays visible.
        by_name[pk]["sourceType"] = by_name[pk].get("sourceType", "string")
        by_name[pk]["type"] = "id"
    if not pk:
        ids = [f["name"] for f in fields if f["type"] == "id"]
        pk = ids[0] if ids else None
    if pk and pk not in by_name:
        errors.append(f"{where}: primaryKey {pk!r} is not a control-record field")
        pk = None
    if not pk:
        errors.append(f"{where}: no primary key — no field of type 'id' and none declared")

    cr = {
        "name": cr_in.get("name") or sd.get("controlRecordName")
                or f"{asset} {PATTERN_NOUN.get(pattern, 'Record')}",
        "table": cr_in.get("table") or snake(name),
        "primaryKey": pk,
        "identifiers": [d["name"] for d in ident_decl if d["name"] in by_name],
        "money": sorted(f["name"] for f in fields if f["type"] == "money"),
        "ratios": sorted(f["name"] for f in fields if f["type"] == "ratio"),
        "fields": fields,
    }
    if cr_in.get("stageField"):
        cr["stageField"] = cr_in["stageField"]
    if cr_in.get("note"):
        cr["note"] = cr_in["note"]

    shariah = dict(sd.get("shariah") or {})
    # Two fragments keyed the standard number `ref`, four keyed it `code`.
    stds = []
    for std in as_list(shariah.get("standards")):
        if isinstance(std, dict):
            std = dict(std)
            if "code" not in std and std.get("ref"):
                std["code"] = std.pop("ref")
            if "body" not in std:
                # isb-treasury wrote {status, code} with the body folded into the
                # code string.  Lift it back out when the leading token names a
                # known standards body; never guess one that is not written down.
                head = str(std.get("code", "")).split()[:1]
                if head and head[0].rstrip(":").upper() in KNOWN_BODIES:
                    std["body"] = head[0].rstrip(":").upper()
            std["clauseVerified"] = False   # no clause here was read from a primary text
        stds.append(std)
    if stds:
        shariah["standards"] = stds
    # Honesty invariant: nothing here is reviewed, whatever a fragment wrote.
    if shariah.get("reviewed") is True:
        errors.append(f"{where}: shariah.reviewed is true — no SSB has signed anything")
    shariah["reviewed"] = False
    shariah.setdefault("review", "UNREVIEWED — requires named Shariah board sign-off")

    out = {
        # the three original keys, byte-identical to catalog v1
        "name": name,
        "functionalPattern": pattern,
        "assetType": asset,
        # schema v2 additions
        "controlRecord": cr,
        "behaviourQualifiers": [b for b in
                                (normalise_bq(b, where, errors)
                                 for b in sd.get("behaviourQualifiers", []))
                                if b],
        "rules": [r for r in (normalise_rule(r, where, errors)
                              for r in sd.get("rules", [])) if r],
        "events": [e for e in (normalise_event(e, where, area_ns, sd_slug, errors)
                               for e in sd.get("events", [])) if e],
        "shariah": shariah,
        "uncertain": as_list(sd.get("uncertain")),
        "source": sd.get("$fragment"),
    }
    for key in ("openBankingMapping", "summary", "designNote", "arithmetic",
                "isTheGate", "gateHonesty"):
        if key in sd:
            out[key] = sd[key]

    ids = [r["id"] for r in out["rules"]]
    if len(ids) != len(set(ids)):
        errors.append(f"{where}: duplicate rule ids")
    return out


# --------------------------------------------------------------------- merge

AREA_NAMESPACE = {
    "Shariah Governance and Compliance": "isb-governance",
    "Deposits and Investment Accounts": "isb-deposits",
    "Islamic Financing": "isb-financing",
    "Treasury Markets and Sukuk": "isb-treasury",
    "Takaful and Shared Operations": "isb-operations",
    "Islamic Account Servicing and Positions": "isb-accounts",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    if not FRAGMENTS.is_dir():
        print(f"FATAL: no fragments directory at {FRAGMENTS}", file=sys.stderr)
        return 1

    errors: list[str] = []
    unparseable: list[str] = []
    enriched: dict[str, dict] = {}
    per_fragment: dict[str, int] = {}

    for path in sorted(FRAGMENTS.glob("*.json")):
        try:
            domains, doc = fragment_domains(path)
        except Exception as exc:                      # noqa: BLE001 - reported, not raised
            unparseable.append(f"{path.name}: {exc}")
            continue
        per_fragment[path.name] = len(domains)
        namespace = doc.get("namespace", "")
        area = next((a for a, n in AREA_NAMESPACE.items() if n == namespace), "")
        if not area:
            errors.append(f"{path.name}: namespace {namespace!r} is not a known "
                          f"business-area namespace")
        for sd in domains:
            if sd["name"] in enriched:
                errors.append(f"{sd['name']}: defined in two fragments "
                              f"({enriched[sd['name']]['source']} and {path.name})")
            enriched[sd["name"]] = normalise_domain(
                sd, area, AREA_NAMESPACE.get(area, "isb"), errors)

    catalog = json.loads(CATALOG.read_text())
    catalog["version"] = CATALOG_SCHEMA_VERSION
    catalog["catalogSchema"] = "islamic-service-landscape.schema.json"
    catalog["mergedFrom"] = sorted(per_fragment)
    catalog["shariahReview"] = {
        "reviewed": False,
        "status": "UNREVIEWED — requires named Shariah board sign-off",
        "statement": "Every Shariah-bearing field, rule and standard reference in "
                     "this catalog was modelled by an engineer from the research "
                     "record. None has been reviewed by a Shariah supervisory "
                     "board. Standards are cited by body and number only; no "
                     "clause was read from a primary text.",
    }

    matched, unmatched_catalog = 0, []
    for area in catalog["businessAreas"]:
        for bdom in area["businessDomains"]:
            new_sds = []
            for sd in bdom["serviceDomains"]:
                rich = enriched.pop(sd["name"], None)
                if rich is None:
                    unmatched_catalog.append(sd["name"])
                    new_sds.append(sd)
                    continue
                # catalog's own three fields win: the fragment must not rename a domain
                for k in ("functionalPattern", "assetType"):
                    if rich[k] != sd[k]:
                        errors.append(f"{sd['name']}: fragment says {k}={rich[k]!r}, "
                                      f"catalog says {sd[k]!r} — catalog wins")
                        rich[k] = sd[k]
                rich["businessDomain"] = bdom["name"]
                rich["businessArea"] = area["name"]
                new_sds.append(rich)
                matched += 1
            bdom["serviceDomains"] = new_sds

    orphans = sorted(enriched)
    report = {
        "fragments": per_fragment,
        "unparseable": unparseable,
        "enrichedDomains": matched,
        "catalogDomainsWithoutFragment": sorted(unmatched_catalog),
        "fragmentDomainsNotInCatalog": orphans,
        "normalisationErrors": errors,
    }

    print(f"fragments read      : {len(per_fragment)} "
          f"({', '.join(f'{k}={v}' for k, v in sorted(per_fragment.items()))})")
    if unparseable:
        print("UNPARSEABLE         :", *unparseable, sep="\n  ")
    print(f"domains enriched    : {matched}")
    if unmatched_catalog:
        print(f"NOT enriched ({len(unmatched_catalog)}) :", ", ".join(sorted(unmatched_catalog)))
    if orphans:
        print(f"fragment-only ({len(orphans)}):", ", ".join(orphans))
    if errors:
        print(f"normalisation errors: {len(errors)}")
        for e in errors[:40]:
            print("  -", e)
        if len(errors) > 40:
            print(f"  … {len(errors) - 40} more (see {REPORT.name})")

    if args.check:
        print("--check: nothing written")
        return 1 if (errors or unparseable or orphans) else 0

    CATALOG.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {CATALOG.relative_to(HERE.parent)} and {REPORT.relative_to(HERE.parent)}")
    return 1 if (errors or unparseable or orphans) else 0


if __name__ == "__main__":
    sys.exit(main())
