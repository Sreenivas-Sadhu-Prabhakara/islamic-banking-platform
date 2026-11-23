#!/usr/bin/env python3
"""Validate a catalog entry against catalog/islamic-service-landscape.schema.json.

WHY THIS FILE EXISTS.  The generator used to accept a three-field service domain
and stamp a scaffold with `additionalProperties: true` and a ConcurrentHashMap.
That silent fallback is the root cause of 48 byte-identical services: a thin
entry produced a service rather than an error.  There is no fallback any more.
A malformed entry FAILS, loudly, naming the domain, the field and the reason.

Stdlib only, so the generator keeps its no-dependency promise.  When the
`jsonschema` package happens to be installed, validate_catalog() ALSO runs the
documented JSON Schema, which is the human-readable contract; the checks here
are the subset the generator cannot proceed without, plus the ones a JSON
Schema cannot express (identifier length, cross-field money/currency
resolution, event payloads resolving to real fields, the generator-lint rules).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CANONICAL_TYPES = {
    "id", "ref", "string", "enum", "bool", "int32", "int64",
    "money", "ratio", "currency", "countryCode", "date", "timestamp",
    "period", "array",
}

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while",
}

# Names the renderer emits as component schemas; a field may not collide.
RESERVED_SCHEMAS = {"ControlRecord", "ControlAction", "ServiceDomainInfo",
                    "Ratio", "Period", "Problem"}

FIELD_NAME_RE = re.compile(r"^[a-z][A-Za-z0-9]*$")
TABLE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
RULE_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
EVENT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
ON_VIOLATION = {"reject", "flag", "reject-or-flag", "warn"}

PG_MAX_IDENTIFIER = 63


class CatalogError(Exception):
    """A malformed catalog entry. The generator refuses to stamp."""


def _check_field(fld: dict, where: str, seen: set, errs: list,
                 record_currencies: list, visible: set | None = None) -> None:
    """`visible` is every field name a currencyField may point at: the record's
    own fields plus, for a behaviour qualifier, the parent record's."""
    name = fld.get("name", "")
    if not FIELD_NAME_RE.match(name):
        errs.append(f"{where}: field name {name!r} must be lowerCamelCase "
                    f"[a-z][A-Za-z0-9]* — it becomes a Java accessor and a "
                    f"JSON property")
    if name in seen:
        errs.append(f"{where}: duplicate field {name!r}")
    seen.add(name)
    if name.lower() in JAVA_KEYWORDS:
        errs.append(f"{where}.{name}: is a Java reserved word and cannot be a "
                    f"generated model property")
    if name in RESERVED_SCHEMAS:
        errs.append(f"{where}.{name}: collides with a generated schema name "
                    f"({', '.join(sorted(RESERVED_SCHEMAS))})")
    t = fld.get("type")
    if t not in CANONICAL_TYPES:
        errs.append(f"{where}.{name}: unknown type {t!r} — the vocabulary is "
                    f"{', '.join(sorted(CANONICAL_TYPES))}")
        return
    if "required" not in fld:
        errs.append(f"{where}.{name}: `required` is not optional; say true or false")
    if t == "enum" and not (fld.get("values") or "const" in fld):
        errs.append(f"{where}.{name}: an enum with no `values` generates a "
                    f"free-form string column — this is the silent-scaffold "
                    f"failure the schema exists to stop")
    if t == "enum":
        vals = [fld["const"]] if "const" in fld else fld.get("values", [])
        if len(set(vals)) != len(vals):
            errs.append(f"{where}.{name}: duplicate enum values")
    if t == "ref" and not fld.get("refDomain"):
        errs.append(f"{where}.{name}: a ref with no `refDomain` is an undeclared "
                    f"cross-service dependency")
    if t == "ratio":
        md = fld.get("maxDenominator")
        if not isinstance(md, int) or md < 1:
            errs.append(f"{where}.{name}: a ratio needs an integer "
                        f"`maxDenominator` so cross-multiplication stays inside "
                        f"int64. ProfitSharingRatio is an EXACT ratio, never a float")
        elif md > 10 ** 9:
            errs.append(f"{where}.{name}: maxDenominator {md} is too large — two "
                        f"ratios cross-multiplied must stay below 2^63")
    if t == "money":
        cf = fld.get("currencyField")
        if cf:
            allowed = {f["name"] for f in record_currencies} | (visible or set())
            if cf not in allowed:
                errs.append(f"{where}.{name}: currencyField {cf!r} is not a "
                            f"field of this record or of its parent record")
        elif len(record_currencies) != 1:
            errs.append(f"{where}.{name}: money is int64 MINOR units and cannot "
                        f"be scaled without an ISO 4217 code. This record has "
                        f"{len(record_currencies)} currency fields, so the field "
                        f"must name one with `currencyField`")
    if t == "array" and isinstance(fld.get("items"), list):
        # an element's money field may name a currency field on the same element
        item_names = {i.get("name") for i in fld["items"]}
        item_currencies = [i for i in fld["items"] if i.get("type") == "currency"]
        sub: set = set()
        for item in fld["items"]:
            _check_field(item, f"{where}.{name}[]", sub, errs,
                         record_currencies + item_currencies,
                         (visible or set()) | item_names)


def _check_identifier(name: str, what: str, errs: list) -> None:
    if len(name) > PG_MAX_IDENTIFIER:
        errs.append(f"{what}: generated SQL identifier {name!r} is "
                    f"{len(name)} characters; Postgres truncates at "
                    f"{PG_MAX_IDENTIFIER} and two truncated names collide "
                    f"silently. Shorten the catalog's table or field name")


# Fields the GENERATOR supplies for every event, so an event payload may name
# them even though they are not control-record fields: they are the columns of
# the generated <table>_shariah_finding table plus the envelope timestamp.
GENERATED_ENVELOPE_FIELDS = {"ruleId", "errorCode", "onViolation", "detectedAt",
                             "detail", "occurredAt"}


def validate_domain(sd: dict, area: str, known_patterns: set,
                    known_areas: set) -> tuple[list[str], list[str]]:
    """Return (errors, warnings).

    An ERROR means the generated code would be wrong or unbuildable, so the
    generator refuses to stamp the domain.  A WARNING means the catalog entry is
    incomplete in a way the generated artefacts can state honestly — it is
    printed, written into the repo's docs/RULES-GAPS.md, and made fatal by
    --strict.
    """
    errs: list[str] = []
    warns: list[str] = []
    name = sd.get("name")
    if not name:
        return ["a service domain has no name"], []
    where = name

    for key in ("functionalPattern", "assetType", "controlRecord",
                "rules", "events", "shariah"):
        if key not in sd:
            errs.append(f"{where}: missing {key!r} — catalog schema v2 requires "
                        f"it. A three-field entry can only produce a scaffold, "
                        f"which is what this phase exists to end")
    if errs:
        return errs, warns

    if sd["functionalPattern"] not in known_patterns:
        errs.append(f"{where}: functional pattern "
                    f"{sd['functionalPattern']!r} is not in the catalog's "
                    f"functionalPatterns or the generator's PATTERN_NOUN table")
    if area not in known_areas:
        errs.append(f"{where}: business area {area!r} has no namespace in the "
                    f"generator's AREA_NAMESPACE table")

    cr = sd["controlRecord"]
    for key in ("name", "table", "primaryKey", "fields"):
        if not cr.get(key):
            errs.append(f"{where}.controlRecord: missing {key!r}")
    if errs:
        return errs, warns

    table = cr["table"]
    if not TABLE_RE.match(table):
        errs.append(f"{where}: controlRecord.table {table!r} is not a valid "
                    f"snake_case SQL identifier")
    _check_identifier(table, f"{where}.controlRecord.table", errs)

    currencies = [f for f in cr["fields"] if f.get("type") == "currency"]
    cr_names = {f.get("name") for f in cr["fields"]}
    seen: set = set()
    for fld in cr["fields"]:
        _check_field(fld, f"{where}.controlRecord", seen, errs, currencies,
                     cr_names)
    if cr["primaryKey"] not in seen:
        errs.append(f"{where}: primaryKey {cr['primaryKey']!r} is not a field")
    else:
        pk = next(f for f in cr["fields"] if f["name"] == cr["primaryKey"])
        if pk.get("type") != "id":
            errs.append(f"{where}: primaryKey {pk['name']!r} is of type "
                        f"{pk.get('type')!r}, not 'id'")
        if not pk.get("required"):
            errs.append(f"{where}: primaryKey {pk['name']!r} must be required")

    # Constraint and index names are shortened deterministically by
    # render.sql_ident(), so only names the CATALOG controls are checked here.

    bq_paths, bq_tables = set(), set()
    for bq in sd.get("behaviourQualifiers", []):
        bwhere = f"{where}.bq[{bq.get('name')}]"
        if bq.get("noSchema") or not bq.get("fields"):
            warns.append(f"{bwhere}: named but given no field list, so it gets "
                         f"no table and no endpoint")
            continue
        for key in ("name", "path", "table", "cardinality", "actions"):
            if not bq.get(key):
                errs.append(f"{bwhere}: missing {key!r}")
        if bq.get("path") in bq_paths:
            errs.append(f"{bwhere}: duplicate path {bq['path']!r} — two "
                        f"behaviour qualifiers would serve the same URL")
        bq_paths.add(bq.get("path"))
        if bq.get("table") in bq_tables:
            errs.append(f"{bwhere}: duplicate table {bq['table']!r}")
        bq_tables.add(bq.get("table"))
        if bq.get("table") and not TABLE_RE.match(bq["table"]):
            errs.append(f"{bwhere}: table {bq['table']!r} is not snake_case")
        bq_currencies = [f for f in bq["fields"] if f.get("type") == "currency"] \
            or currencies
        bq_visible = cr_names | {f.get("name") for f in bq["fields"]}
        bseen: set = set()
        for fld in bq["fields"]:
            _check_field(fld, bwhere, bseen, errs, bq_currencies, bq_visible)

    rule_ids: set = set()
    field_names = set(seen)
    for bq in sd.get("behaviourQualifiers", []):
        for fld in bq.get("fields", []):
            field_names.add(fld.get("name"))
    for rule in sd["rules"]:
        rid = rule.get("id", "")
        if not RULE_ID_RE.match(rid):
            errs.append(f"{where}: rule id {rid!r} must be upper-case "
                        f"[A-Z0-9-]+ — it becomes a Java method and test name")
        if rid in rule_ids:
            errs.append(f"{where}: duplicate rule id {rid!r}")
        rule_ids.add(rid)
        if not rule.get("assert"):
            errs.append(f"{where}.rule {rid}: no `assert`")
        if rule.get("onViolation") not in ON_VIOLATION:
            errs.append(f"{where}.rule {rid}: onViolation "
                        f"{rule.get('onViolation')!r} is not one of "
                        f"{sorted(ON_VIOLATION)}")
        # A generator-lint rule asserting absent(X) is a lint on THIS catalog
        # entry: the forbidden field must not exist.  This is how
        # "no interestRate on an investment account" is enforced at all.
        if rule.get("enforcedAt") == "generator-lint":
            for forbidden in re.findall(r"absent\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
                                        rule["assert"]):
                if forbidden in field_names:
                    errs.append(
                        f"{where}.rule {rid}: forbids the field {forbidden!r} and "
                        f"the catalog defines it. {rule.get('errorCode', '')} "
                        f"{(rule.get('citation') or [''])[0] if rule.get('citation') else ''}")

    topic_prefix = "isb."
    ev_names: set = set()
    for ev in sd["events"]:
        evn = ev.get("name", "")
        if not EVENT_NAME_RE.match(evn):
            errs.append(f"{where}.event {evn!r}: name must match "
                        f"{EVENT_NAME_RE.pattern}")
        if evn in ev_names:
            errs.append(f"{where}: duplicate event name {evn!r}")
        ev_names.add(evn)
        if not str(ev.get("topic", "")).startswith(topic_prefix):
            errs.append(f"{where}.event {evn}: topic {ev.get('topic')!r} must "
                        f"start with {topic_prefix!r}")
        payload = ev.get("payload") or []
        if not payload:
            errs.append(f"{where}.event {evn}: empty payload")
        for p in payload:
            if p not in field_names and p not in GENERATED_ENVELOPE_FIELDS:
                warns.append(f"{where}.event {evn}: payload names {p!r}, which is "
                             f"neither a control-record field, a "
                             f"behaviour-qualifier field, nor one the generator "
                             f"supplies. The AsyncAPI document declares it as an "
                             f"unsourced string; nothing fills it")

    sh = sd["shariah"]
    if sh.get("reviewed") is not False:
        errs.append(f"{where}.shariah.reviewed must be false. No Shariah "
                    f"supervisory board has reviewed anything in this estate, "
                    f"and there is no flag that overrides this")
    if "contractType" not in sh:
        errs.append(f"{where}.shariah: no contractType")
    if "capitalAtRisk" not in sh:
        errs.append(f"{where}.shariah: no capitalAtRisk — it decides whether a "
                    f"funds confirmation against this product must refuse "
                    f"(DESIGN.md §7)")
    return errs, warns


def validate_catalog(catalog: dict, known_patterns: set, known_areas: set,
                     schema_path: Path | None = None
                     ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Validate every domain. Returns ({domain: errors}, {domain: warnings})."""
    bad: dict[str, list[str]] = {}
    warn: dict[str, list[str]] = {}
    version = str(catalog.get("version", "0"))
    if int(version.split(".")[0] or 0) < 2:
        bad["<catalog>"] = [
            f"catalog version {version} is pre-v2: service domains carry only "
            f"{{name, functionalPattern, assetType}}, which can only produce a "
            f"scaffold. Run catalog/merge_fragments.py."]
        return bad, warn
    if catalog.get("shariahReview", {}).get("reviewed") is not False:
        bad.setdefault("<catalog>", []).append(
            "shariahReview.reviewed must be false")

    for area in catalog.get("businessAreas", []):
        for bdom in area.get("businessDomains", []):
            for sd in bdom.get("serviceDomains", []):
                errs, warns = validate_domain(sd, area.get("name", ""),
                                              known_patterns, known_areas)
                if errs:
                    bad[sd.get("name", "<unnamed>")] = errs
                if warns:
                    warn[sd.get("name", "<unnamed>")] = warns

    # Optional belt-and-braces pass against the documented JSON Schema.
    if schema_path and schema_path.exists():
        try:
            import jsonschema                      # noqa: PLC0415 - optional
        except ImportError:
            pass
        else:
            schema = json.loads(schema_path.read_text())
            for err in jsonschema.Draft202012Validator(schema).iter_errors(catalog):
                path = "/".join(str(x) for x in err.absolute_path)
                bad.setdefault("<json-schema>", []).append(f"{path}: {err.message}")
    return bad, warn
