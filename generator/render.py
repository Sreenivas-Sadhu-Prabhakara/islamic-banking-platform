#!/usr/bin/env python3
"""Render the per-domain artefacts of a generated Islamic banking service.

templates/service/ holds the files that are the SAME for every domain (Helm,
CI, Dockerfile, .gitignore, the contract test).  This module holds the files
whose CONTENT comes from the catalog entry, which is the whole point of catalog
schema v2:

    api/openapi.yaml                    real schemas, additionalProperties:false
    api/events.yaml                     AsyncAPI 2.6 from events[]
    src/main/resources/db/migration/    Flyway DDL; money is BIGINT minor units
    .../model/                          NOT written here — openapi-generator
                                        derives the models from api/openapi.yaml,
                                        which is what makes drift a compile error
    .../repo/ControlRecordRepository    JdbcTemplate over the generated table
    .../rules/ShariahRules              rules[] translated by rules_lang
    .../api/ServiceDomainController     implements the GENERATED interfaces
    .../config/SecurityConfig           scopes from the contract's security:
    src/test/java/.../                  rule tests + authorization deny-tests
    docs/RULES-GAPS.md                  every rule that could NOT be translated
    docs/SHARIAH-GAPS.md                every `uncertain` note, verbatim

Stdlib only.  Deterministic: same catalog entry in, byte-identical files out.
"""

from __future__ import annotations

import json
import re

import rules_lang

# ISO 4217 minor-unit exponents that are not 2.  DESIGN.md §6: a hardcoded ×100
# is a bug, and the Islamic markets' 3-decimal currencies are the first ones to
# break it.  This table is emitted into every service as the single authority.
ISO4217_EXPONENTS = {
    "BHD": 3, "IQD": 3, "JOD": 3, "KWD": 3, "LYD": 3, "OMR": 3, "TND": 3,
    "BIF": 0, "CLP": 0, "DJF": 0, "GNF": 0, "ISK": 0, "JPY": 0, "KMF": 0,
    "KRW": 0, "PYG": 0, "RWF": 0, "UGX": 0, "UYI": 0, "VND": 0, "VUV": 0,
    "XAF": 0, "XOF": 0, "XPF": 0,
    "CLF": 4, "UYW": 4,
}

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "record", "var", "yield",
}

SQL_TYPE = {
    "id": "VARCHAR(64)", "ref": "VARCHAR(64)", "string": "TEXT",
    "enum": "TEXT", "bool": "BOOLEAN", "int32": "INTEGER", "int64": "BIGINT",
    "money": "BIGINT", "currency": "CHAR(3)", "countryCode": "CHAR(2)",
    "date": "DATE", "timestamp": "TIMESTAMP WITH TIME ZONE", "array": "TEXT",
}

JAVA_TYPE = {
    "id": "String", "ref": "String", "string": "String", "enum": "String",
    "currency": "String", "countryCode": "String", "bool": "Boolean",
    "int32": "Integer", "int64": "Long", "money": "Long",
    "date": "java.time.LocalDate", "timestamp": "java.time.OffsetDateTime",
}


def camel(text: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", text)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def lower_camel(text: str) -> str:
    c = camel(text)
    return c[:1].lower() + c[1:]


def yq(text) -> str:
    """Quote a scalar for YAML, conservatively."""
    s = str(text)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def jstr(text) -> str:
    s = str(text)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def sql_ident(*parts: str) -> str:
    """A deterministic SQL identifier that fits Postgres' 63-character limit.

    Two long names truncated to 63 characters collide silently, which is a
    corrupt migration rather than a build error, so an over-long name is
    shortened with a stable hash of the full name instead of being cut.
    """
    name = "_".join(p for p in parts if p)
    if len(name) <= 63:
        return name
    import hashlib
    digest = hashlib.sha256(name.encode()).hexdigest()[:8]
    return name[:54].rstrip("_") + "_" + digest


def sql_str(text) -> str:
    return "'" + str(text).replace("'", "''") + "'"


# ---------------------------------------------------------------- OpenAPI

def _openapi_property(fld: dict, schema_prefix: str) -> list[str]:
    """Return the YAML lines of one property body, indented by the caller."""
    t = fld["type"]
    note = fld.get("note") or fld.get("description")
    out: list[str] = []
    if t == "ratio":
        out.append('$ref: "#/components/schemas/Ratio"')
        return out
    if t == "period":
        out.append('$ref: "#/components/schemas/Period"')
        return out
    if t == "array":
        out.append("type: array")
        items = fld.get("items")
        if isinstance(items, list):
            out.append(f'items: {{ $ref: "#/components/schemas/'
                       f'{schema_prefix}{camel(fld["name"])}Item" }}')
        else:
            out.append("items: { type: string }")
        return out
    if t == "bool":
        out.append("type: boolean")
        if "const" in fld:
            # Deliberately NOT `enum: [true]`: a single-valued boolean enum makes
            # the code generator emit an enum type for a boolean. The constraint
            # is enforced by the SQL CHECK and stated here.
            out.append("description: >-")
            out.append(f"  Catalog const: this field may only be "
                       f"{str(fld['const']).lower()}. Enforced by a CHECK "
                       f"constraint in db/migration, not a product option.")
        return out
    if t in ("int32", "int64", "money"):
        out.append("type: integer")
        out.append("format: " + ("int32" if t == "int32" else "int64"))
        if t == "money":
            cur = fld.get("currencyField", "currency")
            out.append(f"description: >-")
            out.append(f"  SIGNED int64 MINOR units. The ISO 4217 exponent comes from "
                       f"`{cur}` via the shared Iso4217 table (BHD/KWD/OMR/TND are 3, "
                       f"JPY is 0): a hardcoded x100 is a bug. Never a float.")
            if fld.get("nonNegative"):
                out.append("minimum: 0")
        else:
            if "min" in fld:
                out.append(f"minimum: {fld['min']}")
            if "max" in fld:
                out.append(f"maximum: {fld['max']}")
        return out
    if t == "enum":
        # A NAMED component schema, not an inline enum: a named enum generates a
        # top-level Java enum with a predictable class name, where an inline one
        # generates an inner class whose name the generator chooses.
        out.append(f'$ref: "#/components/schemas/{schema_prefix}{camel(fld["name"])}"')
        return out
    # string-shaped
    out.append("type: string")
    if t == "currency":
        out.append('pattern: "^[A-Z]{3}$"')
    elif t == "countryCode":
        out.append('pattern: "^[A-Z]{2}$"')
    elif t == "date":
        out.append("format: date")
    elif t == "timestamp":
        out.append("format: date-time")
    elif t == "id":
        out.append("maxLength: 64")
    elif t == "ref":
        out.append("maxLength: 64")
    elif "maxLength" in fld:
        out.append(f"maxLength: {fld['maxLength']}")
    if t == "ref" and fld.get("refDomain"):
        out.append(f"description: >-")
        out.append(f"  Reference to a record owned by the {fld['refDomain']!r} service "
                   f"domain. NOT a foreign key: each service domain owns its own "
                   f"schema and referential integrity is the caller's.")
    elif note and t != "enum":
        out.append("description: " + yq(note))
    return out


def _schema_block(name: str, fields: list[dict], title: str,
                  schema_prefix: str, indent: str = "    ") -> list[str]:
    req = [f["name"] for f in fields if f.get("required")]
    L = [f"{indent}{name}:",
         f"{indent}  title: {yq(title)}",
         f"{indent}  type: object",
         f"{indent}  additionalProperties: false"]
    if req:
        L.append(f"{indent}  required: [" + ", ".join(req) + "]")
    L.append(f"{indent}  properties:")
    for fld in fields:
        L.append(f"{indent}    {fld['name']}:")
        for line in _openapi_property(fld, schema_prefix):
            L.append(f"{indent}      {line}")
    return L


def _enum_schemas(fields: list[dict], prefix: str,
                  indent: str = "    ") -> list[str]:
    """One named schema per enum field, so its generated Java type is a
    top-level enum with a name this generator chose rather than guessed."""
    out: list[str] = []
    for fld in fields:
        if fld["type"] != "enum":
            continue
        vals = [fld["const"]] if "const" in fld else fld.get("values", [])
        out.append(f"{indent}{prefix}{camel(fld['name'])}:")
        out.append(f"{indent}  title: {yq(prefix + ' ' + fld['name'])}")
        out.append(f"{indent}  type: string")
        out.append(f"{indent}  enum: [" + ", ".join(yq(v) for v in vals) + "]")
        if "const" in fld:
            out.append(f"{indent}  description: >-")
            out.append(f"{indent}    Catalog const — one permitted value. Not a "
                       f"configurable product option.")
        elif fld.get("note"):
            out.append(f"{indent}  description: {yq(fld['note'])}")
        if fld["type"] == "array":
            continue
    for fld in fields:
        if fld["type"] == "array" and isinstance(fld.get("items"), list):
            out += _enum_schemas(fld["items"], f"{prefix}{camel(fld['name'])}Item",
                                 indent)
    return out


def _inline_item_schemas(fields: list[dict], prefix: str,
                         indent: str = "    ") -> list[str]:
    """Named schemas for array-of-object fields, so the generated Java class
    name is predictable instead of an `…Inner` the generator invents."""
    out: list[str] = []
    for fld in fields:
        if fld["type"] == "array" and isinstance(fld.get("items"), list):
            out += _schema_block(f"{prefix}{camel(fld['name'])}Item",
                                 fld["items"],
                                 f"{fld['name']} element", prefix, indent)
    return out


def operations(sd: dict, ctx: dict) -> list[dict]:
    """The generated operation set. ONE place defines it, so the contract, the
    controller, the security config and the deny-tests cannot disagree."""
    cr_slug = ctx["__CR_SLUG__"]
    sd_slug = ctx["__SD_SLUG__"]
    read, write = f"isb:{sd_slug}:read", f"isb:{sd_slug}:write"
    ops = [
        {"id": "getServiceDomain", "method": "get", "path": "/v1/service-domain",
         "tag": "service-domain", "summary": "Service domain metadata",
         "scope": None, "returns": "ServiceDomainInfo", "statuses": ["200"]},
        {"id": "initiate", "method": "post", "path": f"/v1/{cr_slug}/initiate",
         "tag": "control-record", "summary": "BIAN action term: Initiate",
         "scope": write, "body": "ControlRecord", "returns": "ControlRecord",
         "success": "201", "statuses": ["201", "400", "401", "403", "422"]},
        {"id": "retrieveAll", "method": "get", "path": f"/v1/{cr_slug}",
         "tag": "control-record", "summary": "BIAN action term: Retrieve (collection)",
         "scope": read, "returns": "ControlRecord", "array": True,
         "statuses": ["200", "401", "403"]},
        {"id": "retrieve", "method": "get", "path": f"/v1/{cr_slug}/{{crId}}/retrieve",
         "tag": "control-record", "summary": "BIAN action term: Retrieve",
         "scope": read, "returns": "ControlRecord", "crid": True,
         "statuses": ["200", "401", "403", "404"]},
        {"id": "update", "method": "put", "path": f"/v1/{cr_slug}/{{crId}}/update",
         "tag": "control-record", "summary": "BIAN action term: Update",
         "scope": write, "body": "ControlRecord", "returns": "ControlRecord",
         "crid": True, "statuses": ["200", "400", "401", "403", "404", "422"]},
        {"id": "control", "method": "put", "path": f"/v1/{cr_slug}/{{crId}}/control",
         "tag": "control-record", "summary": "BIAN action term: Control",
         "scope": write, "body": "ControlAction", "returns": "ControlRecord",
         "crid": True, "statuses": ["200", "400", "401", "403", "404"]},
    ]
    for bq in sd.get("behaviourQualifiers", []):
        if bq.get("noSchema") or not bq.get("fields"):
            continue
        ops.append({
            "id": "retrieve" + camel(bq["name"]),
            "method": "get",
            "path": f"/v1/{cr_slug}/{{crId}}/{bq['path']}",
            "tag": "control-record",
            "summary": f"Behaviour qualifier: {bq['name']} ({bq['cardinality']})",
            "scope": read, "returns": camel(bq["name"]) + "Item",
            "array": True, "crid": True,
            "statuses": ["200", "401", "403", "404"],
        })
    return ops


STATUS_TEXT = {
    "200": "OK", "201": "Created",
    "400": "Malformed request", "401": "No or invalid access token",
    "403": "Access token lacks the required scope",
    "404": "Unknown control record id",
    "422": "A Shariah or arithmetic rule rejected the write",
}


def render_openapi(ctx: dict, sd: dict) -> str:
    cr = sd["controlRecord"]
    prefix = "ControlRecord"
    L = [
        "# GENERATED from catalog/islamic-service-landscape.json by",
        "# islamic-banking-platform/generator — DO NOT EDIT.  Change the catalog",
        "# entry and re-run the generator; a hand edit here is reverted by the",
        "# next --force stamp and is caught by the drift check.",
        "#",
        "# This file is COMPILED AGAINST: openapi-generator derives the model and",
        "# API interfaces from it at generate-sources, and the controller declares",
        "# `implements ControlRecordApi`.  A path, parameter, status code or",
        "# response type that stops matching this contract stops compiling.",
        "#",
        "# NOT A SHARIAH ARTEFACT.  Every Shariah-bearing field below was modelled",
        "# by an engineer from a research record and reviewed by NO Shariah",
        f"#   supervisory board.  shariah.reviewed = false.  See docs/SHARIAH-GAPS.md.",
        "openapi: 3.0.3",
        "info:",
        f"  title: {yq(sd['name'] + ' — BIAN-styled Islamic Semantic API')}",
        "  description: >-",
        f"    Islamic banking service domain {sd['name']!r} (functional pattern "
        f"{sd['functionalPattern']}, business area {sd.get('businessArea', '')}) "
        f"operating on the {cr['name']!r} control record.",
        "",
        f"    EXTENSION BEYOND THE UK OPEN BANKING STANDARD. This surface is not "
        f"part of UK OBL v4.0.1 and no conformance or certification claim attaches "
        f"to it (DESIGN.md §7 RULE 3, §9).",
        "",
        f"    UNREVIEWED — requires named Shariah board sign-off.",
        "  version: 0.2.0",
        "  x-shariah-reviewed: false",
        f"  x-contract-type: {yq(sd['shariah'].get('contractType'))}",
        f"  x-capital-at-risk: {yq(sd['shariah'].get('capitalAtRisk'))}",
        "servers:",
        "  - url: /",
        "    description: direct (in-cluster)",
        f"  - url: /{ctx['__ARTIFACT_ID__']}",
        "    description: through the platform gateway (prefix is rewritten away)",
        "tags:",
        "  - name: service-domain",
        "  - name: control-record",
        "",
        "paths:",
    ]
    for op in operations(sd, ctx):
        L.append(f"  {op['path']}:")
        L.append(f"    {op['method']}:")
        L.append(f"      tags: [{op['tag']}]")
        L.append(f"      operationId: {op['id']}")
        L.append(f"      summary: {yq(op['summary'])}")
        if op["scope"]:
            L.append(f"      security:")
            L.append(f"        - bearerAuth: [{yq(op['scope'])}]")
        else:
            L.append("      security: []   # public service-domain metadata")
        if op.get("crid"):
            L.append('      parameters:')
            L.append('        - $ref: "#/components/parameters/CrId"')
        if op.get("body"):
            L.append("      requestBody:")
            L.append("        required: true")
            L.append("        content:")
            L.append("          application/json:")
            L.append("            schema:")
            L.append(f'              $ref: "#/components/schemas/{op["body"]}"')
        L.append("      responses:")
        for st in op["statuses"]:
            L.append(f'        "{st}":')
            L.append(f"          description: {yq(STATUS_TEXT[st])}")
            if st == op.get("success", "200"):
                L.append("          content:")
                L.append("            application/json:")
                L.append("              schema:")
                if op.get("array"):
                    L.append("                type: array")
                    L.append(f'                items: {{ $ref: "#/components/schemas/{op["returns"]}" }}')
                else:
                    L.append(f'                $ref: "#/components/schemas/{op["returns"]}"')
            elif st in ("400", "404", "422"):
                L.append("          content:")
                L.append("            application/json:")
                L.append("              schema:")
                L.append('                $ref: "#/components/schemas/Problem"')
    L += [
        "",
        "components:",
        "  securitySchemes:",
        "    bearerAuth:",
        "      type: http",
        "      scheme: bearer",
        "      bearerFormat: JWT",
        "      description: >-",
        "        FAPI 2.0 access token issued by the platform authorization server.",
        "        The scope required per operation is declared on that operation and",
        f"        is enforced by the generated SecurityConfig. Read scope",
        f"        `isb:{ctx['__SD_SLUG__']}:read`, write scope `isb:{ctx['__SD_SLUG__']}:write`.",
        "  parameters:",
        "    CrId:",
        "      name: crId",
        "      in: path",
        "      required: true",
        "      schema: { type: string, maxLength: 64 }",
        f"      description: {yq(cr['name'] + ' identifier')}",
        "  schemas:",
        "    ServiceDomainInfo:",
        "      title: Service domain identity",
        "      type: object",
        "      additionalProperties: false",
        "      required: [serviceDomain, businessArea, functionalPattern, assetType, controlRecord, shariahReviewed]",
        "      properties:",
        "        serviceDomain: { type: string }",
        "        businessArea: { type: string }",
        "        businessDomain: { type: string }",
        "        functionalPattern: { type: string }",
        "        assetType: { type: string }",
        "        controlRecord: { type: string }",
        "        version: { type: string }",
        "        shariahReviewed:",
        "          type: boolean",
        "          description: >-",
        "            Always false. No Shariah supervisory board has reviewed this",
        "            service. There is no catalog value and no generator flag that",
        "            can make it true.",
        "    Ratio:",
        "      title: Exact ratio",
        "      description: >-",
        "        An EXACT ratio of two int64 integers. ProfitSharingRatio and every",
        "        weightage use this type. Never a float, never a decimal string:",
        "        comparison is by cross-multiplication in int64, which is why every",
        "        ratio field carries a maxDenominator.",
        "      type: object",
        "      additionalProperties: false",
        "      required: [numerator, denominator]",
        "      properties:",
        "        numerator: { type: integer, format: int64 }",
        "        denominator: { type: integer, format: int64, minimum: 1 }",
        "    Period:",
        "      title: Closed date period",
        "      type: object",
        "      additionalProperties: false",
        "      required: [from, to]",
        "      properties:",
        "        from: { type: string, format: date }",
        "        to: { type: string, format: date }",
        "    ControlAction:",
        "      title: BIAN Control action",
        "      type: object",
        "      additionalProperties: false",
        "      required: [action]",
        "      properties:",
        "        action: { type: string, enum: [suspend, resume, terminate] }",
        "    Problem:",
        "      title: RFC 9457 problem detail",
        "      type: object",
        "      additionalProperties: false",
        "      required: [type, title, status]",
        "      properties:",
        "        type: { type: string }",
        "        title: { type: string }",
        "        status: { type: integer, format: int32 }",
        "        detail: { type: string }",
        "        code:",
        "          type: string",
        "          description: The violated rule's errorCode from the catalog.",
        "        ruleId:",
        "          type: string",
        "          description: The violated rule's catalog id, e.g. ISB-MUDS-02.",
    ]
    L += _schema_block("ControlRecord", cr["fields"], cr["name"], prefix)
    L += _enum_schemas(cr["fields"], prefix)
    L += _inline_item_schemas(cr["fields"], prefix)
    for bq in sd.get("behaviourQualifiers", []):
        if bq.get("noSchema") or not bq.get("fields"):
            continue
        nm = camel(bq["name"]) + "Item"
        L += _schema_block(nm, bq["fields"],
                           f"{bq['name']} behaviour qualifier", nm)
        L += _enum_schemas(bq["fields"], nm)
        L += _inline_item_schemas(bq["fields"], nm)
    return "\n".join(L) + "\n"


# ------------------------------------------------------------- AsyncAPI

def render_events(ctx: dict, sd: dict) -> str:
    cr = sd["controlRecord"]
    known = {f["name"]: f for f in cr["fields"]}
    for bq in sd.get("behaviourQualifiers", []):
        for f in bq.get("fields", []):
            known.setdefault(f["name"], f)
    L = [
        "# GENERATED from the catalog's events[] — DO NOT EDIT.",
        "asyncapi: 2.6.0",
        "info:",
        f"  title: {yq(sd['name'] + ' — events')}",
        "  version: 0.2.0",
        "  description: >-",
        "    Event surface of this service domain. Every payload field below is a",
        "    control-record or behaviour-qualifier field of this domain; the",
        "    generator rejects a payload that names anything else.",
        "defaultContentType: application/json",
        f"service: {ctx['__ARTIFACT_ID__']}",
        "channels:",
    ]
    for ev in sd["events"]:
        L.append(f"  {ev['topic']}:")
        L.append(f"    description: {yq(ev.get('trigger') or ev.get('note') or ev['name'])}")
        L.append("    publish:")
        L.append(f"      operationId: {lower_camel(ev['name'].replace('.', ' '))}")
        L.append(f"      summary: {yq(ev['name'])}")
        L.append("      message:")
        L.append(f"        name: {yq(ev['name'])}")
        L.append("        payload:")
        L.append("          type: object")
        L.append("          additionalProperties: false")
        L.append("          required: [" + ", ".join(ev["payload"]) + "]")
        L.append("          properties:")
        for name in ev["payload"]:
            fld = known.get(name)
            L.append(f"            {name}:")
            if fld is None:
                L.append("              type: string")
            else:
                for line in _openapi_property(fld, ""):
                    L.append(f"              {line}")
    # The ApiContractTest's event assertions want the flat publishes/consumes
    # lists too; keep them so the existing test keeps working.
    L.append("publishes:")
    for ev in sd["events"]:
        L.append(f"  - topic: {ev['topic']}")
        L.append(f"    events: [{yq(ev['name'])}]")
    L.append("consumes: []")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- Flyway

def _columns(fld: dict) -> list[tuple[str, str]]:
    """One catalog field -> one or more (column, sql type) pairs."""
    col, t = fld["column"], fld["type"]
    if t == "ratio":
        return [(f"{col}_numerator", "BIGINT"), (f"{col}_denominator", "BIGINT")]
    if t == "period":
        return [(f"{col}_from", "DATE"), (f"{col}_to", "DATE")]
    return [(col, SQL_TYPE[t])]


def _field_checks(fld: dict, table: str) -> list[str]:
    out = []
    col, t = fld["column"], fld["type"]
    if t == "enum":
        vals = [fld["const"]] if "const" in fld else fld.get("values", [])
        if vals:
            out.append(f"CONSTRAINT {sql_ident('ck', table, col, 'values')} "
                       f"CHECK ({col} IN ({', '.join(sql_str(v) for v in vals)}))")
    elif t == "bool" and "const" in fld:
        out.append(f"CONSTRAINT {sql_ident('ck', table, col, 'const')} "
                   f"CHECK ({col} = {str(fld['const']).upper()})")
    elif t == "money" and fld.get("nonNegative"):
        out.append(f"CONSTRAINT {sql_ident('ck', table, col, 'nonneg')} "
                   f"CHECK ({col} >= 0)")
    elif t == "ratio":
        md = fld["maxDenominator"]
        out.append(f"CONSTRAINT {sql_ident('ck', table, col, 'exact')} "
                   f"CHECK ({col}_denominator > 0 "
                   f"AND {col}_denominator <= {md} AND {col}_numerator >= 0)")
    elif t == "currency":
        # Portable across Postgres and H2: no `~` regex operator, which H2's
        # PostgreSQL mode does not implement.
        out.append(f"CONSTRAINT {sql_ident('ck', table, col, 'iso4217')} "
                   f"CHECK (LENGTH({col}) = 3 AND {col} = UPPER({col}))")
    return out


def _table_ddl(table: str, fields: list[dict], pk: str | None,
               parent: tuple[str, str] | None, checks: list[str]) -> list[str]:
    lines = [f"CREATE TABLE {table} ("]
    body: list[str] = []
    if parent:
        body.append(f"  {parent[1]} VARCHAR(64) NOT NULL "
                    f"REFERENCES {parent[0]}({parent[1]}) ON DELETE CASCADE")
    for fld in fields:
        # The comment goes on its OWN line: an inline `--` after a column would
        # swallow the separating comma when the body is joined.
        if fld["type"] == "money":
            body.append("  -- signed int64 MINOR units\n"
                        f"  {fld['column']} {SQL_TYPE['money']}"
                        f"{' NOT NULL' if fld.get('required') else ''}")
            continue
        if fld["type"] == "ref":
            body.append(f"  -- ref -> {fld.get('refDomain')}; NO foreign key "
                        f"across service domains (decentralised data)\n"
                        f"  {fld['column']} {SQL_TYPE['ref']}"
                        f"{' NOT NULL' if fld.get('required') else ''}")
            continue
        for col, sqlt in _columns(fld):
            nn = " NOT NULL" if fld.get("required") else ""
            body.append(f"  {col} {sqlt}{nn}")
    if pk:
        body.append(f"  PRIMARY KEY ({pk})")
    for ck in checks:
        body.append("  " + ck)
    lines.append(",\n".join(body))
    lines.append(");")
    return lines


def render_migration(ctx: dict, sd: dict,
                     translations: list[rules_lang.Translation]) -> str:
    cr = sd["controlRecord"]
    table = cr["table"]
    pk_field = next((f for f in cr["fields"] if f["name"] == cr["primaryKey"]), None)
    L = [
        f"-- GENERATED from catalog/islamic-service-landscape.json — DO NOT EDIT.",
        f"-- Service domain : {sd['name']}",
        f"-- Control record : {cr['name']}",
        f"--",
        f"-- MONEY IS BIGINT MINOR UNITS, SIGNED.  There is no NUMERIC, no DECIMAL",
        f"-- and no DOUBLE column anywhere in this file, by construction: the",
        f"-- catalog has no decimal type.  The ISO 4217 exponent comes from the",
        f"-- generated Iso4217 table, never from a hardcoded x100.",
        f"--",
        f"-- A RATIO IS TWO BIGINT COLUMNS (<name>_numerator, <name>_denominator)",
        f"-- with a CHECK bounding the denominator, so cross-multiplying two",
        f"-- ratios cannot overflow int64.",
        f"--",
        f"-- NULL SEMANTICS: a CHECK whose expression is UNKNOWN passes.  Required",
        f"-- fields are NOT NULL so their checks always bite; for an optional field",
        f"-- the check bites only when a value is present.  The generated",
        f"-- ShariahRules returns NOT_APPLICABLE in exactly that case, so the two",
        f"-- enforcement points agree.",
        "",
    ]
    checks = []
    for fld in cr["fields"]:
        checks += _field_checks(fld, table)
    rule_checks = []
    for tr in translations:
        if tr.translated:
            rule_checks.append((tr.rule_id, tr.sql))
    for rid, sql in rule_checks:
        checks.append(f"CONSTRAINT "
                      f"{sql_ident('ck', table, rid.lower().replace('-', '_'))} "
                      f"CHECK ({sql})")
    L += _table_ddl(table, cr["fields"],
                    pk_field["column"] if pk_field else None, None, checks)
    L.append("")
    if rule_checks:
        L.append("-- Catalog rules enforced above as CHECK constraints:")
        for rid, _ in rule_checks:
            rule = next(r for r in sd["rules"] if r["id"] == rid)
            L.append(f"--   {rid}: {rule['assert'][:160]}")
            if rule.get("errorCode"):
                L.append(f"--       errorCode {rule['errorCode']}")
            for c in rule.get("citation", [])[:2]:
                txt = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                L.append(f"--       cite {txt[:150]}")
        L.append("")
    for fld in cr["fields"]:
        if fld["type"] == "ref":
            L.append(f"CREATE INDEX {sql_ident('ix', table, fld['column'])} "
                     f"ON {table}({fld['column']});")
    L.append("")
    for bq in sd.get("behaviourQualifiers", []):
        if bq.get("noSchema") or not bq.get("fields"):
            L.append(f"-- behaviour qualifier {bq['name']!r} has no field list in the "
                     f"catalog, so it gets NO table and NO endpoint. See docs/RULES-GAPS.md.")
            continue
        bq_table = sql_ident(table, bq["table"])
        bq_checks: list[str] = []
        for fld in bq["fields"]:
            bq_checks += _field_checks(fld, bq_table)
        bq_pk = next((f["name"] for f in bq["fields"] if f["type"] == "id"), None)
        bq_pk_col = next((f["column"] for f in bq["fields"]
                          if f["name"] == bq_pk), None)
        L.append(f"-- behaviour qualifier: {bq['name']} ({bq['cardinality']}) "
                 f"-> GET /v1/{ctx['__CR_SLUG__']}/{{crId}}/{bq['path']}")
        L += _table_ddl(bq_table, bq["fields"], bq_pk_col,
                        (table, pk_field["column"] if pk_field else "id"), bq_checks)
        L.append(f"CREATE INDEX {sql_ident('ix', bq_table, 'parent')} "
                 f"ON {bq_table}({pk_field['column'] if pk_field else 'id'});")
        L.append("")
    L += [
        "-- Append-only Shariah findings (DESIGN.md §5.8: a DELETE that destroys a",
        "-- non-compliance record is a correctness bug, not untidiness).",
        f"CREATE TABLE {sql_ident(table, 'shariah_finding')} (",
        "  finding_id    BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,",
        f"  {pk_field['column'] if pk_field else 'record_id'} VARCHAR(64) NOT NULL,",
        "  rule_id       VARCHAR(64) NOT NULL,",
        "  error_code    VARCHAR(128),",
        "  on_violation  TEXT NOT NULL,",
        "  detected_at   TIMESTAMP WITH TIME ZONE NOT NULL,",
        "  detail        TEXT",
        ");",
        f"CREATE INDEX {sql_ident('ix', table, 'finding_rule')} "
        f"ON {sql_ident(table, 'shariah_finding')}(rule_id);",
    ]
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------- Java

def render_iso4217(ctx: dict) -> str:
    rows = ",\n".join(f'            java.util.Map.entry("{c}", {e})'
                      for c, e in sorted(ISO4217_EXPONENTS.items()))
    return f"""package {ctx['__PACKAGE__']}.money;

import java.util.Map;

/**
 * The ONE ISO 4217 minor-unit exponent table in this service.
 *
 * DESIGN.md §6: money crosses this estate as a signed int64 count of MINOR
 * units, and a hardcoded x100 is a bug. BHD, IQD, JOD, KWD, LYD, OMR and TND
 * are 3-decimal — the Islamic markets' currencies are the first ones to break
 * a 2-decimal assumption — and JPY, KRW and the CFA francs are 0-decimal.
 *
 * GENERATED — do not edit.
 */
public final class Iso4217 {{

    private static final Map<String, Integer> EXPONENTS = Map.ofEntries(
{rows}
    );

    private Iso4217() {{ }}

    /** @return the ISO 4217 minor-unit exponent; 2 for every currency not listed. */
    public static int exponent(String currency) {{
        if (currency == null) {{
            throw new IllegalArgumentException("currency is required to scale minor units");
        }}
        return EXPONENTS.getOrDefault(currency, 2);
    }}

    /** Smallest positive amount in the currency, in minor units. Always 1. */
    public static long minorUnit() {{
        return 1L;
    }}
}}
"""


def _getter(fld: dict) -> str:
    return "get" + camel(fld["name"])


def render_rules(ctx: dict, sd: dict,
                 translations: list[rules_lang.Translation]) -> str:
    pkg = ctx["__PACKAGE__"]
    cr = sd["controlRecord"]
    by_name = {f["name"]: f for f in cr["fields"]}
    tr_by_id = {t.rule_id: t for t in translations}

    registry, methods, dispatch = [], [], []
    for rule in sd["rules"]:
        tr = tr_by_id[rule["id"]]
        mname = "check" + camel(rule["id"])
        cites = [c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                 for c in rule.get("citation", [])]
        enforcement = ("TRANSLATED" if tr.translated else "UNIMPLEMENTED")
        registry.append(
            f"            new Rule({jstr(rule['id'])}, {jstr(rule['assert'])}, "
            f"{jstr(rule['onViolation'])}, {jstr(rule.get('errorCode', ''))}, "
            f"{jstr(rule.get('enforcedAt', ''))}, Enforcement.{enforcement}, "
            f"{jstr(' | '.join(cites))}, {jstr(tr.reason)})")
        if not tr.translated:
            continue
        dispatch.append(f"        add(out, {jstr(rule['id'])}, {mname}(cr));")
        decls = []
        for fname in tr.fields:
            fld = by_name[fname]
            if fld["type"] == "enum":
                # the generated model types an enum field as a Java enum, so the
                # rule's string comparison runs against its wire value
                decls.append(f"        {ctx['__MODEL_PKG__']}."
                             f"{'ControlRecord' + camel(fname)} b_{fname} = "
                             f"cr.{_getter(fld)}();")
                decls.append(f"        String v_{fname} = b_{fname} == null "
                             f"? null : b_{fname}.getValue();")
                continue
            jt = JAVA_TYPE[fld["type"]]
            decls.append(f"        {jt} b_{fname} = cr.{_getter(fld)}();")
            if fld["type"] in ("money", "int32", "int64"):
                decls.append(f"        long v_{fname} = b_{fname} == null ? 0L "
                             f": b_{fname}.longValue();")
            else:
                decls.append(f"        {jt} v_{fname} = b_{fname};")
        for fname in tr.presence_fields:
            decls.append(f"        boolean v_{fname}_present = "
                         f"cr.{_getter(by_name[fname])}() != null;")
        # A presence test is meaningful on a null field, so a field used ONLY
        # inside present()/absent() must not trip the null guard.
        guard_fields = [f for f in tr.fields if f not in tr.presence_fields]
        guard = " || ".join(f"b_{f} == null" for f in guard_fields)
        cite_doc = "\n     * ".join(("cite: " + c) for c in cites[:4]) or "no citation — an arithmetic or engineering invariant, not a Shariah claim"
        test_doc = rule.get("test") or ""
        methods.append(f"""
    /**
     * {rule['id']} — {rule['assert'].replace('*/', '* /')}
     *
     * onViolation {rule['onViolation']}; errorCode {rule.get('errorCode', '(none)')}
     * {cite_doc}
     *
     * UNREVIEWED — requires named Shariah board sign-off.
     * {('designer test vector: ' + test_doc.replace('*/', '* /')) if test_doc else ''}
     */
    public static Outcome {mname}({ctx['__MODEL_PKG__']}.ControlRecord cr) {{
{chr(10).join(decls)}
        if ({guard if guard else 'false'}) {{
            return Outcome.NOT_APPLICABLE;
        }}
        return ({tr.java}) ? Outcome.PASS : Outcome.FAIL;
    }}""")

    translated = sum(1 for t in translations if t.translated)
    return f"""package {pkg}.rules;

import java.util.ArrayList;
import java.util.List;

/**
 * GENERATED Shariah and arithmetic rule component for the {sd['name']!r} service
 * domain — do not edit.  Derived from the catalog entry's rules[].
 *
 * {len(sd['rules'])} rules in the catalog.  {translated} are translated into executable
 * checks here (and into SQL CHECK constraints in the Flyway migration);
 * {len(sd['rules']) - translated} are registered as UNIMPLEMENTED because their assertion
 * uses cross-row aggregation, a behaviour-qualifier path, an exact-ratio
 * comparison or a field this control record does not own.  An UNIMPLEMENTED
 * rule is REPORTED, never silently dropped and never silently claimed — see
 * docs/RULES-GAPS.md and the registry below.
 *
 * NOT A COMPLIANCE ARTEFACT.  No Shariah supervisory board has reviewed any
 * rule, citation or field here.  Citations name a body and a standard number
 * from this estate's research record; no clause was read from a primary text.
 */
public final class ShariahRules {{

    public enum Outcome {{ PASS, FAIL, NOT_APPLICABLE }}

    /** Whether this rule has an executable check in this class. */
    public enum Enforcement {{ TRANSLATED, UNIMPLEMENTED }}

    public record Rule(String id, String assertion, String onViolation,
                       String errorCode, String catalogEnforcedAt,
                       Enforcement enforcement, String citation,
                       String untranslatableReason) {{ }}

    public record Violation(String ruleId, String errorCode, String onViolation,
                            String assertion) {{ }}

    private static final List<Rule> RULES = List.of(
{",".join(chr(10) + r for r in registry) if registry else ""}
    );

    private ShariahRules() {{ }}

    /** Every catalog rule, translated or not. */
    public static List<Rule> rules() {{
        return RULES;
    }}

    public static Rule rule(String id) {{
        return RULES.stream().filter(r -> r.id().equals(id)).findFirst()
                .orElseThrow(() -> new IllegalArgumentException("no such rule: " + id));
    }}

    /**
     * Evaluate every translated rule against a control record.
     *
     * @return the violations, in catalog order.  A rule whose fields are null
     *         is NOT_APPLICABLE and yields no violation, which is the same
     *         answer the SQL CHECK gives for a NULL column.
     */
    public static List<Violation> check({ctx['__MODEL_PKG__']}.ControlRecord cr) {{
        List<Violation> out = new ArrayList<>();
{chr(10).join(dispatch) if dispatch else "        // no rule in this domain is translatable; see docs/RULES-GAPS.md"}
        return out;
    }}

    private static void add(List<Violation> out, String id, Outcome outcome) {{
        if (outcome == Outcome.FAIL) {{
            Rule r = rule(id);
            out.add(new Violation(r.id(), r.errorCode(), r.onViolation(), r.assertion()));
        }}
    }}
{"".join(methods)}
}}
"""


def render_rules_test(ctx: dict, sd: dict,
                      translations: list[rules_lang.Translation]) -> str:
    pkg = ctx["__PACKAGE__"]
    tr_by_id = {t.rule_id: t for t in translations}
    translated = [r for r in sd["rules"] if tr_by_id[r["id"]].translated]
    unimpl = [r for r in sd["rules"] if not tr_by_id[r["id"]].translated]
    L = []
    for rule in translated:
        tr = tr_by_id[rule["id"]]
        L.append(f"""
    @Test
    void {lower_camel('rule ' + rule['id'])}IsTranslatedAndEnforcedInBothPlaces() throws Exception {{
        ShariahRules.Rule r = ShariahRules.rule({jstr(rule['id'])});
        assertThat(r.enforcement()).isEqualTo(ShariahRules.Enforcement.TRANSLATED);
        assertThat(r.assertion()).isEqualTo({jstr(rule['assert'])});
        assertThat(r.onViolation()).isEqualTo({jstr(rule['onViolation'])});
        // the same rule must also be a CHECK constraint in the migration
        assertThat(MIGRATION).contains({jstr(sql_ident('ck', sd['controlRecord']['table'], rule['id'].lower().replace('-', '_')))});
        // and an executable check method must exist and be reachable
        assertThat(ShariahRules.class.getMethod({jstr('check' + camel(rule['id']))},
                {ctx['__MODEL_PKG__']}.ControlRecord.class)).isNotNull();
        // an all-null record is NOT_APPLICABLE, never a false PASS
        assertThat(ShariahRules.{'check' + camel(rule['id'])}(
                new {ctx['__MODEL_PKG__']}.ControlRecord()))
                .isEqualTo(ShariahRules.Outcome.NOT_APPLICABLE);
    }}""")
    for rule in unimpl:
        tr = tr_by_id[rule["id"]]
        L.append(f"""
    @Test
    void {lower_camel('rule ' + rule['id'])}IsReportedAsUnimplemented() {{
        // {tr.reason.replace(chr(10), ' ')}
        ShariahRules.Rule r = ShariahRules.rule({jstr(rule['id'])});
        assertThat(r.enforcement()).isEqualTo(ShariahRules.Enforcement.UNIMPLEMENTED);
        assertThat(r.untranslatableReason()).isNotBlank();
        assertThat(GAPS).contains({jstr(rule['id'])});
    }}""")
    return f"""package {pkg}.rules;

import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * GENERATED — one test per catalog rule, {len(translated)} translated and
 * {len(unimpl)} reported as unimplemented.  Do not edit.
 *
 * What these tests actually assert, stated plainly so nobody reads more into
 * them than is there:
 *   - a translated rule is registered, is spelled exactly as the catalog spells
 *     it, has a CHECK constraint of the same name in the migration, has a
 *     reachable check method, and answers NOT_APPLICABLE (never PASS) for an
 *     empty record;
 *   - an unimplemented rule is registered as UNIMPLEMENTED with a reason and
 *     appears in docs/RULES-GAPS.md.
 * They do NOT assert that a rule is Shariah-correct.  Nothing here can.
 */
class ShariahRulesTest {{

    private static final String MIGRATION = read(
            "src/main/resources/db/migration/{ctx['__MIGRATION_FILE__']}");
    private static final String GAPS = read("docs/RULES-GAPS.md");

    private static String read(String path) {{
        try {{
            return Files.readString(Path.of(path));
        }} catch (Exception e) {{
            throw new IllegalStateException("generated file missing: " + path, e);
        }}
    }}

    @Test
    void everyCatalogRuleIsRegistered() {{
        assertThat(ShariahRules.rules()).hasSize({len(sd['rules'])});
        assertThat(ShariahRules.rules()).allSatisfy(r -> {{
            assertThat(r.id()).isNotBlank();
            assertThat(r.assertion()).isNotBlank();
        }});
    }}
{"".join(L)}
}}
"""


def render_deny_test(ctx: dict, sd: dict) -> str:
    """Authorization deny-tests derived from each operation's security: block."""
    pkg = ctx["__PACKAGE__"]
    cases = []
    for op in operations(sd, ctx):
        if not op["scope"]:
            continue
        path = op["path"].replace("{crId}", "CR-does-not-exist")
        verb = op["method"].upper()
        body = '"{}"' if op.get("body") else "null"
        cases.append(f"""
    @Test
    void {lower_camel(op['id'])}IsDeniedWithoutAToken() throws Exception {{
        mvc.perform(request("{verb}", "{path}", {body}))
                .andExpect(status().isUnauthorized());
    }}

    @Test
    void {lower_camel(op['id'])}IsDeniedWithTheWrongScope() throws Exception {{
        mvc.perform(request("{verb}", "{path}", {body})
                        .with(jwt().jwt(j -> j.claim("scope", "isb:some-other-domain:read"))))
                .andExpect(status().isForbidden());
    }}""")
    return f"""package {pkg}.api;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * GENERATED authorization deny-tests — one pair per operation that declares a
 * `security:` block in api/openapi.yaml.  Do not edit.
 *
 * Each secured operation must answer 401 with no token and 403 with a token
 * that carries a scope for a different service domain.  The public
 * /v1/service-domain metadata operation declares `security: []` and is
 * deliberately NOT tested here.
 *
 * These are negative tests only.  A 401/403 proves the gate is shut; nothing
 * here proves the happy path is correct.
 */
@SpringBootTest
@AutoConfigureMockMvc
class AuthorizationDenyTest {{

    @Autowired
    MockMvc mvc;

    private static MockHttpServletRequestBuilder request(String verb, String path,
                                                         String body) {{
        MockHttpServletRequestBuilder b = switch (verb) {{
            case "POST" -> MockMvcRequestBuilders.post(path);
            case "PUT" -> MockMvcRequestBuilders.put(path);
            default -> MockMvcRequestBuilders.get(path);
        }};
        if (body != null) {{
            b = b.contentType(MediaType.APPLICATION_JSON).content(body);
        }}
        return b;
    }}
{"".join(cases)}
}}
"""


def render_security_config(ctx: dict, sd: dict) -> str:
    pkg = ctx["__PACKAGE__"]
    sd_slug = ctx["__SD_SLUG__"]
    cr_slug = ctx["__CR_SLUG__"]
    return f"""package {pkg}.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.server.resource.authentication.JwtGrantedAuthoritiesConverter;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.web.SecurityFilterChain;

/**
 * GENERATED from the `security:` blocks of api/openapi.yaml — do not edit.
 *
 * Read operations require scope {{@code isb:{sd_slug}:read}}, writes require
 * {{@code isb:{sd_slug}:write}}, and /v1/service-domain is public because the
 * contract declares {{@code security: []}} on it.  The generated
 * AuthorizationDenyTest asserts every one of those decisions.
 *
 * This service VALIDATES tokens; it does not issue them.  PAR, PKCE, client
 * authentication, DPoP and JWKS rotation belong to the platform authorization
 * server (DESIGN.md §3) and nothing here reimplements them.
 */
@Configuration
public class SecurityConfig {{

    static final String READ_SCOPE = "SCOPE_isb:{sd_slug}:read";
    static final String WRITE_SCOPE = "SCOPE_isb:{sd_slug}:write";

    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {{
        http
            .csrf(csrf -> csrf.disable())           // stateless bearer-token API
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(a -> a
                .requestMatchers("/v1/service-domain").permitAll()
                .requestMatchers("/actuator/health/**", "/actuator/info",
                                 "/v3/api-docs/**", "/swagger-ui/**",
                                 "/swagger-ui.html").permitAll()
                .requestMatchers(HttpMethod.GET, "/v1/{cr_slug}/**").hasAuthority(READ_SCOPE)
                .requestMatchers(HttpMethod.GET, "/v1/{cr_slug}").hasAuthority(READ_SCOPE)
                .requestMatchers(HttpMethod.POST, "/v1/{cr_slug}/**").hasAuthority(WRITE_SCOPE)
                .requestMatchers(HttpMethod.PUT, "/v1/{cr_slug}/**").hasAuthority(WRITE_SCOPE)
                .anyRequest().denyAll())
            .oauth2ResourceServer(o -> o.jwt(j -> j.jwtAuthenticationConverter(converter())));
        return http.build();
    }}

    private static JwtAuthenticationConverter converter() {{
        JwtGrantedAuthoritiesConverter scopes = new JwtGrantedAuthoritiesConverter();
        scopes.setAuthorityPrefix("SCOPE_");
        scopes.setAuthoritiesClaimName("scope");
        JwtAuthenticationConverter c = new JwtAuthenticationConverter();
        c.setJwtGrantedAuthoritiesConverter(scopes);
        return c;
    }}
}}
"""


def render_repository(ctx: dict, sd: dict) -> str:
    pkg = ctx["__PACKAGE__"]
    model = ctx["__MODEL_PKG__"]
    cr = sd["controlRecord"]
    table = cr["table"]
    pk_field = next(f for f in cr["fields"] if f["name"] == cr["primaryKey"])

    cols, params, mappers, setters = [], [], [], []
    for fld in cr["fields"]:
        g = _getter(fld)
        t = fld["type"]
        if t == "ratio":
            cols += [f"{fld['column']}_numerator", f"{fld['column']}_denominator"]
            params += [f"cr.{g}() == null ? null : cr.{g}().getNumerator()",
                       f"cr.{g}() == null ? null : cr.{g}().getDenominator()"]
            mappers.append(f"""        if (rs.getObject("{fld['column']}_numerator") != null) {{
            {model}.Ratio r = new {model}.Ratio();
            r.setNumerator(rs.getLong("{fld['column']}_numerator"));
            r.setDenominator(rs.getLong("{fld['column']}_denominator"));
            cr.set{camel(fld['name'])}(r);
        }}""")
        elif t == "period":
            cols += [f"{fld['column']}_from", f"{fld['column']}_to"]
            params += [f"cr.{g}() == null ? null : java.sql.Date.valueOf(cr.{g}().getFrom())",
                       f"cr.{g}() == null ? null : java.sql.Date.valueOf(cr.{g}().getTo())"]
            mappers.append(f"""        if (rs.getDate("{fld['column']}_from") != null) {{
            {model}.Period p = new {model}.Period();
            p.setFrom(rs.getDate("{fld['column']}_from").toLocalDate());
            p.setTo(rs.getDate("{fld['column']}_to").toLocalDate());
            cr.set{camel(fld['name'])}(p);
        }}""")
        elif t == "array":
            cols.append(fld["column"])
            params.append(f"writeJson(cr.{g}())")
            mappers.append(f'        cr.set{camel(fld["name"])}(readJson('
                           f'rs.getString("{fld["column"]}"), new '
                           f'com.fasterxml.jackson.core.type.TypeReference<>() {{ }}));')
        elif t == "money" or t == "int64":
            cols.append(fld["column"])
            params.append(f"cr.{g}()")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getObject("{fld["column"]}") == null ? null '
                           f': rs.getLong("{fld["column"]}"));')
        elif t == "int32":
            cols.append(fld["column"])
            params.append(f"cr.{g}()")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getObject("{fld["column"]}") == null ? null '
                           f': rs.getInt("{fld["column"]}"));')
        elif t == "bool":
            cols.append(fld["column"])
            params.append(f"cr.{g}()")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getObject("{fld["column"]}") == null ? null '
                           f': rs.getBoolean("{fld["column"]}"));')
        elif t == "date":
            cols.append(fld["column"])
            params.append(f"cr.{g}() == null ? null : java.sql.Date.valueOf(cr.{g}())")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getDate("{fld["column"]}") == null ? null '
                           f': rs.getDate("{fld["column"]}").toLocalDate());')
        elif t == "timestamp":
            cols.append(fld["column"])
            params.append(f"cr.{g}() == null ? null : java.sql.Timestamp.from(cr.{g}().toInstant())")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getTimestamp("{fld["column"]}") == null ? null '
                           f': rs.getTimestamp("{fld["column"]}").toInstant()'
                           f'.atOffset(java.time.ZoneOffset.UTC));')
        elif t == "enum":
            ec = f'{model}.ControlRecord{camel(fld["name"])}'
            cols.append(fld["column"])
            params.append(f"cr.{g}() == null ? null : cr.{g}().getValue()")
            mappers.append(f'        cr.set{camel(fld["name"])}('
                           f'rs.getString("{fld["column"]}") == null ? null : '
                           f'{ec}.fromValue(rs.getString("{fld["column"]}")));')
        else:
            cols.append(fld["column"])
            params.append(f"cr.{g}()")
            mappers.append(f'        cr.set{camel(fld["name"])}(rs.getString("{fld["column"]}"));')

    placeholders = ", ".join("?" for _ in cols)
    set_clause = ", ".join(f"{c} = ?" for c in cols)
    bq_methods = []
    for bq in sd.get("behaviourQualifiers", []):
        if bq.get("noSchema") or not bq.get("fields"):
            continue
        item = camel(bq["name"]) + "Item"
        bq_table = sql_ident(table, bq["table"])
        bq_map = []
        for fld in bq["fields"]:
            if fld["type"] in ("money", "int64"):
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getObject("{fld["column"]}") == null ? null : rs.getLong("{fld["column"]}"));')
            elif fld["type"] == "int32":
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getObject("{fld["column"]}") == null ? null : rs.getInt("{fld["column"]}"));')
            elif fld["type"] == "bool":
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getObject("{fld["column"]}") == null ? null : rs.getBoolean("{fld["column"]}"));')
            elif fld["type"] == "date":
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getDate("{fld["column"]}") == null ? null : rs.getDate("{fld["column"]}").toLocalDate());')
            elif fld["type"] == "timestamp":
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getTimestamp("{fld["column"]}") == null ? null : '
                              f'rs.getTimestamp("{fld["column"]}").toInstant().atOffset(java.time.ZoneOffset.UTC));')
            elif fld["type"] == "ratio":
                bq_map.append(f"""            if (rs.getObject("{fld['column']}_numerator") != null) {{
                {model}.Ratio r = new {model}.Ratio();
                r.setNumerator(rs.getLong("{fld['column']}_numerator"));
                r.setDenominator(rs.getLong("{fld['column']}_denominator"));
                it.set{camel(fld['name'])}(r);
            }}""")
            elif fld["type"] == "period":
                bq_map.append(f"""            if (rs.getDate("{fld['column']}_from") != null) {{
                {model}.Period p = new {model}.Period();
                p.setFrom(rs.getDate("{fld['column']}_from").toLocalDate());
                p.setTo(rs.getDate("{fld['column']}_to").toLocalDate());
                it.set{camel(fld['name'])}(p);
            }}""")
            elif fld["type"] == "array":
                bq_map.append(f'            it.set{camel(fld["name"])}(readJson('
                              f'rs.getString("{fld["column"]}"), new '
                              f'com.fasterxml.jackson.core.type.TypeReference<>() {{ }}));')
            elif fld["type"] == "enum":
                ec = f'{model}.{item}{camel(fld["name"])}'
                bq_map.append(f'            it.set{camel(fld["name"])}('
                              f'rs.getString("{fld["column"]}") == null ? null : '
                              f'{ec}.fromValue(rs.getString("{fld["column"]}")));')
            else:
                bq_map.append(f'            it.set{camel(fld["name"])}(rs.getString("{fld["column"]}"));')
        bq_methods.append(f"""
    /** Behaviour qualifier {bq['name']!r} ({bq['cardinality']}) of one control record. */
    public List<{model}.{item}> {lower_camel('find ' + bq['name'])}(String id) {{
        return jdbc.query("SELECT * FROM {bq_table} WHERE {pk_field['column']} = ?",
                (rs, n) -> {{
            {model}.{item} it = new {model}.{item}();
{chr(10).join(bq_map)}
            return it;
        }}, id);
    }}""")

    return f"""package {pkg}.repo;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

/**
 * GENERATED repository for the {cr['name']!r} control record — do not edit.
 *
 * This replaces the Phase-1 {{@code ConcurrentHashMap}} store.  Every column
 * below comes from the catalog entry, every statement is parameterised with
 * {{@code ?}} placeholders (DESIGN.md §5.2), and every money column is a signed
 * {{@code BIGINT}} of MINOR units read and written as {{@code Long}} — there is no
 * float, double or BigDecimal anywhere in this file.
 *
 * Single-tenant: there is no {{@code tenant_id}} column in this estate.  Stated
 * rather than faked (DESIGN.md §5.3).
 */
@Repository
public class {camel(sd['name'])}Repository {{

    private static final String TABLE = "{table}";
    private static final String COLUMNS = "{', '.join(cols)}";
    private static final ObjectMapper JSON = new ObjectMapper()
            .findAndRegisterModules();

    private final JdbcTemplate jdbc;

    public {camel(sd['name'])}Repository(JdbcTemplate jdbc) {{
        this.jdbc = jdbc;
    }}

    private final RowMapper<{model}.ControlRecord> mapper = this::map;

    private {model}.ControlRecord map(ResultSet rs, int rowNum) throws SQLException {{
        {model}.ControlRecord cr = new {model}.ControlRecord();
{chr(10).join(mappers)}
        return cr;
    }}

    public {model}.ControlRecord insert({model}.ControlRecord cr) {{
        jdbc.update("INSERT INTO " + TABLE + " (" + COLUMNS + ") VALUES ({placeholders})",
                {", ".join(params)});
        return cr;
    }}

    public List<{model}.ControlRecord> findAll() {{
        return jdbc.query("SELECT * FROM " + TABLE, mapper);
    }}

    public Optional<{model}.ControlRecord> findById(String id) {{
        return jdbc.query("SELECT * FROM " + TABLE + " WHERE {pk_field['column']} = ?",
                mapper, id).stream().findFirst();
    }}

    public int update({model}.ControlRecord cr) {{
        return jdbc.update("UPDATE " + TABLE + " SET {set_clause} WHERE {pk_field['column']} = ?",
                {", ".join(params)}, cr.{_getter(pk_field)}());
    }}

    /** Append-only: a Shariah finding is never updated and never deleted (§5.8). */
    public void appendFinding(String id, String ruleId, String errorCode,
                              String onViolation, String detail) {{
        jdbc.update("INSERT INTO {table}_shariah_finding "
                        + "({pk_field['column']}, rule_id, error_code, on_violation, detected_at, detail) "
                        + "VALUES (?, ?, ?, ?, ?, ?)",
                id, ruleId, errorCode, onViolation,
                java.sql.Timestamp.from(java.time.Instant.now()), detail);
    }}
{"".join(bq_methods)}

    private static String writeJson(Object value) {{
        if (value == null) {{
            return null;
        }}
        try {{
            return JSON.writeValueAsString(value);
        }} catch (Exception e) {{
            throw new IllegalArgumentException("cannot serialise array field", e);
        }}
    }}

    private static <T> T readJson(String json, TypeReference<T> type) {{
        if (json == null) {{
            return null;
        }}
        try {{
            return JSON.readValue(json, type);
        }} catch (Exception e) {{
            throw new IllegalStateException("cannot read array column", e);
        }}
    }}
}}
"""


# ------------------------------------------------------- controller & tests

def render_controller(ctx: dict, sd: dict) -> str:
    pkg = ctx["__PACKAGE__"]
    model = ctx["__MODEL_PKG__"]
    api = ctx["__API_PKG__"]
    cr = sd["controlRecord"]
    repo_cls = camel(sd["name"]) + "Repository"
    repo_var = lower_camel(sd["name"]) + "Repository"
    pk_field = next(f for f in cr["fields"] if f["name"] == cr["primaryKey"])
    status_field = next((f for f in cr["fields"]
                         if f["name"] == "status" and f["type"] == "enum"), None)
    status_enum = (ctx["__MODEL_PKG__"] + "." + camel("ControlRecord " + status_field["name"])
                   if status_field else None)

    bq_impls = []
    for bq in sd.get("behaviourQualifiers", []):
        if bq.get("noSchema") or not bq.get("fields"):
            continue
        item = camel(bq["name"]) + "Item"
        bq_impls.append(f"""
    @Override
    public ResponseEntity<List<{model}.{item}>> retrieve{camel(bq['name'])}(String crId) {{
        if ({repo_var}.findById(crId).isEmpty()) {{
            return ResponseEntity.notFound().build();
        }}
        return ResponseEntity.ok({repo_var}.{lower_camel('find ' + bq['name'])}(crId));
    }}""")

    control_body = ""
    if status_field:
        control_body = f"""
        String action = body.getAction() == null ? "" : body.getAction().getValue();
        {status_enum} next = switch (action) {{
            case "suspend" -> {status_enum}.fromValue("SUSPENDED");
            case "resume" -> {status_enum}.fromValue("ACTIVE");
            case "terminate" -> {status_enum}.fromValue("TERMINATED");
            default -> null;
        }};
        if (next == null) {{
            return ResponseEntity.badRequest().build();
        }}
        existing.get().set{camel(status_field['name'])}(next);
        {repo_var}.update(existing.get());
        return ResponseEntity.ok(existing.get());"""
    else:
        control_body = """
        // This control record has no `status` enum in the catalog, so there is
        // no state machine to drive. Reported rather than invented.
        return ResponseEntity.status(org.springframework.http.HttpStatus.NOT_IMPLEMENTED).build();"""

    return f"""package {pkg}.api;

import {pkg}.repo.{repo_cls};
import {pkg}.rules.ShariahRules;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Optional;

/**
 * GENERATED BIAN-styled semantic API for {sd['name']!r} — do not edit.
 *
 * THIS IS WHY DRIFT IS A COMPILE ERROR: the two interfaces below are generated
 * from api/openapi.yaml by openapi-generator at generate-sources, and this
 * class declares that it implements them.  Change a path, a parameter, a status
 * code or a response type in the contract and this file stops compiling.
 *
 * Writes are gated by the generated {{@link ShariahRules}}: a rule whose
 * onViolation is `reject` returns 422 with the rule id; a rule whose
 * onViolation is `flag` appends an audit finding and lets the write through.
 */
@RestController
public class {camel(sd['name'])}Controller
        implements {api}.ControlRecordApi, {api}.ServiceDomainApi {{

    private final {repo_cls} {repo_var};

    public {camel(sd['name'])}Controller({repo_cls} {repo_var}) {{
        this.{repo_var} = {repo_var};
    }}

    @Override
    public ResponseEntity<{model}.ServiceDomainInfo> getServiceDomain() {{
        {model}.ServiceDomainInfo info = new {model}.ServiceDomainInfo();
        info.setServiceDomain({jstr(sd['name'])});
        info.setBusinessArea({jstr(sd.get('businessArea', ''))});
        info.setBusinessDomain({jstr(sd.get('businessDomain', ''))});
        info.setFunctionalPattern({jstr(sd['functionalPattern'])});
        info.setAssetType({jstr(sd['assetType'])});
        info.setControlRecord({jstr(cr['name'])});
        info.setVersion("0.2.0");
        info.setShariahReviewed(false);   // always. No SSB has reviewed this.
        return ResponseEntity.ok(info);
    }}

    @Override
    public ResponseEntity<{model}.ControlRecord> initiate({model}.ControlRecord cr) {{
        List<ShariahRules.Violation> rejects = reject(cr);
        if (!rejects.isEmpty()) {{
            return ResponseEntity.unprocessableEntity().build();
        }}
        {repo_var}.insert(cr);
        flag(cr);
        return ResponseEntity.status(HttpStatus.CREATED).body(cr);
    }}

    @Override
    public ResponseEntity<List<{model}.ControlRecord>> retrieveAll() {{
        return ResponseEntity.ok({repo_var}.findAll());
    }}

    @Override
    public ResponseEntity<{model}.ControlRecord> retrieve(String crId) {{
        return {repo_var}.findById(crId)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }}

    @Override
    public ResponseEntity<{model}.ControlRecord> update(String crId,
                                                        {model}.ControlRecord cr) {{
        if ({repo_var}.findById(crId).isEmpty()) {{
            return ResponseEntity.notFound().build();
        }}
        cr.set{camel(pk_field['name'])}(crId);
        if (!reject(cr).isEmpty()) {{
            return ResponseEntity.unprocessableEntity().build();
        }}
        {repo_var}.update(cr);
        flag(cr);
        return ResponseEntity.ok(cr);
    }}

    @Override
    public ResponseEntity<{model}.ControlRecord> control(String crId,
                                                         {model}.ControlAction body) {{
        Optional<{model}.ControlRecord> existing = {repo_var}.findById(crId);
        if (existing.isEmpty()) {{
            return ResponseEntity.notFound().build();
        }}{control_body}
    }}
{"".join(bq_impls)}

    private List<ShariahRules.Violation> reject({model}.ControlRecord cr) {{
        return ShariahRules.check(cr).stream()
                .filter(v -> "reject".equals(v.onViolation())).toList();
    }}

    /** onViolation=flag: the write stands, the finding is appended (§5.8). */
    private void flag({model}.ControlRecord cr) {{
        String id = cr.{_getter(pk_field)}();
        ShariahRules.check(cr).stream()
                .filter(v -> !"reject".equals(v.onViolation()))
                .forEach(v -> {repo_var}.appendFinding(id, v.ruleId(), v.errorCode(),
                        v.onViolation(), v.assertion()));
    }}
}}
"""


def render_app_test(ctx: dict, sd: dict) -> str:
    pkg = ctx["__PACKAGE__"]
    return f"""package {pkg};

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * GENERATED smoke test — do not edit.
 *
 * /v1/service-domain is the one public operation (its contract declares
 * `security: []`), so it is the one thing this test can assert without a token.
 * Everything else is covered by AuthorizationDenyTest and ShariahRulesTest.
 */
@SpringBootTest
@AutoConfigureMockMvc
class ApplicationTests {{

    @Autowired
    MockMvc mvc;

    @Test
    void serviceDomainMetadataIsServedAndSaysItIsUnreviewed() throws Exception {{
        mvc.perform(get("/v1/service-domain"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.serviceDomain").value({jstr(sd['name'])}))
                .andExpect(jsonPath("$.functionalPattern").value({jstr(sd['functionalPattern'])}))
                .andExpect(jsonPath("$.shariahReviewed").value(false));
    }}
}}
"""


# ------------------------------------------------------------------- docs

def render_rules_gaps(ctx: dict, sd: dict,
                      translations: list[rules_lang.Translation],
                      catalog_warnings: list[str] | None = None) -> str:
    tr_by_id = {t.rule_id: t for t in translations}
    done = [r for r in sd["rules"] if tr_by_id[r["id"]].translated]
    # A generator-lint rule is enforced, just not at runtime: catalog_validate
    # checks it when the repo is stamped, and a violation REFUSES the stamp.
    lint = [r for r in sd["rules"]
            if not tr_by_id[r["id"]].translated
            and r.get("enforcedAt") == "generator-lint"]
    gaps = [r for r in sd["rules"] if not tr_by_id[r["id"]].translated
            and r not in lint]
    L = [
        f"# Rule coverage — {sd['name']}",
        "",
        "GENERATED from the catalog entry. Do not edit.",
        "",
        f"The catalog declares **{len(sd['rules'])} rules** for this service domain. "
        f"**{len(done)}** are translated into an executable check (a Java method in "
        f"`ShariahRules` *and* a `CHECK` constraint in the Flyway migration), "
        f"**{len(lint)}** are enforced by the generator against the catalog, and "
        f"**{len(gaps)}** are **not enforced at all** and are listed below with "
        f"the reason.",
        "",
        "An untranslated rule is **not enforced by this service**. It is recorded "
        "here, registered as `UNIMPLEMENTED` in `ShariahRules.rules()`, and "
        "asserted by a generated test — so it cannot be quietly forgotten and "
        "cannot be quietly claimed.",
        "",
        "## Enforced",
        "",
        "| Rule | onViolation | errorCode | assertion |",
        "|---|---|---|---|",
    ]
    for r in done:
        L.append(f"| `{r['id']}` | {r['onViolation']} | `{r.get('errorCode', '—')}` | "
                 f"`{r['assert'][:110].replace('|', '\\|')}` |")
    if lint:
        L += ["", "## Enforced at generation time (`generator-lint`)", "",
              "These rules assert that a field is ABSENT. They cannot be a "
              "runtime check — there is no column to check — so the generator "
              "enforces them against the catalog entry itself and REFUSES to "
              "stamp the repo if a forbidden field ever appears.", "",
              "| Rule | errorCode | assertion |", "|---|---|---|"]
        for r in lint:
            L.append(f"| `{r['id']}` | `{r.get('errorCode', '—')}` | "
                     f"`{r['assert'][:110].replace('|', chr(92) + '|')}` |")
    L += ["", "## Not enforced — reported gaps", "",
          "| Rule | why it is outside the translated grammar | assertion |",
          "|---|---|---|"]
    for r in gaps:
        L.append(f"| `{r['id']}` | {tr_by_id[r['id']].reason} | "
                 f"`{r['assert'][:110].replace('|', '\\|')}` |")
    empty_bqs = [b for b in sd.get("behaviourQualifiers", [])
                 if b.get("noSchema") or not b.get("fields")]
    if empty_bqs:
        L += ["", "## Behaviour qualifiers with no schema", "",
              "The catalog names these behaviour qualifiers but gives them no "
              "field list, so the generator emits no table and no endpoint for "
              "them. A documented intent is not a sub-resource.", ""]
        for b in empty_bqs:
            L.append(f"- **{b['name']}** ({b['cardinality']})"
                     + (f" — {b.get('note', '')}" if b.get("note") else ""))
    if catalog_warnings:
        L += ["", "## Catalog warnings for this domain", "",
              "The generator stamped this service with these known gaps in its "
              "catalog entry. They do not make the generated code wrong, but "
              "something a reader might expect to be filled is not. "
              "`generate.py --strict` makes them fatal.", ""]
        for w in catalog_warnings:
            L.append(f"- {w}")
    L += ["",
          "## What this file is not",
          "",
          "It is not a compliance assessment. The translated rules are "
          "arithmetic and structural invariants that happen to encode Shariah "
          "requirements as the designing agent understood them. No Shariah "
          "supervisory board has reviewed any of it.", ""]
    return "\n".join(L)


def render_shariah_gaps(ctx: dict, sd: dict) -> str:
    sh = sd["shariah"]
    L = [
        f"# Shariah status and open questions — {sd['name']}",
        "",
        "GENERATED from the catalog entry. Do not edit.",
        "",
        "## Review status",
        "",
        "**UNREVIEWED — requires named Shariah board sign-off.**",
        "",
        "Every Shariah-bearing field, rule, enum value and standard reference in "
        "this repository was modelled by an engineer from a research record. "
        "None has been reviewed by a Shariah supervisory board. A profit-sharing "
        "field modelled by a developer is a compliance claim this code cannot "
        "back, and this file is where that is said plainly rather than buried.",
        "",
        f"- contract type: `{sh.get('contractType')}`",
        f"- capital at risk: `{sh.get('capitalAtRisk')}`",
        f"- `shariah.reviewed`: `false` — there is no catalog value and no "
        f"generator flag that can change this.",
        "",
        "## Standards cited",
        "",
        "Cited by **body and number only**. No clause below was read from a "
        "primary standard text by anyone who built this; the citations come from "
        "this estate's research record and are marked `clauseVerified: false`.",
        "",
    ]
    for std in sh.get("standards", []):
        if isinstance(std, str):
            L.append(f"- {std}")
        else:
            bits = [std.get("body", ""), std.get("code", ""),
                    std.get("clause", ""), std.get("title", "")]
            L.append("- " + " ".join(b for b in bits if b)
                     + (f" — {std['note']}" if std.get("note") else ""))
    if sd.get("uncertain"):
        L += ["", "## What the designer could not model", "",
              "Verbatim from the catalog. Honesty over completeness: a domain "
              "that could not be modelled well is a reported gap, not invented "
              "detail.", ""]
        for u in sd["uncertain"]:
            L.append(f"- {u}")
    if sd.get("openBankingMapping"):
        L += ["", "## Open Banking surface", "",
              "This domain's Islamic fields surface on the `openbank-islamic` "
              "sibling resource server, never on an OBIE path: DESIGN.md §7 "
              "RULE 1 forbids extending OBIE's own schemas, and an extra field "
              "in `OBAccount` is a conformance failure.", "",
              "```json",
              json.dumps(sd["openBankingMapping"], indent=2, ensure_ascii=False),
              "```"]
    L.append("")
    return "\n".join(L)
