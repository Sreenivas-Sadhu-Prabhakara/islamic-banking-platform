# control-record-engine

Serves any BIAN-style control record described by **catalog schema v2**.

A service domain is data, not code. One catalog entry in — a validated,
persisted, tenant-scoped API out, with the BIAN action terms
(`initiate` / `retrieve` / `update` / `control`) and one read path per
behaviour qualifier.

## Why it exists

The estate had 210 service repos. **203 of them were the same six Java files**
— 428 lines that knew nothing about their own domain, stored records in a
`ConcurrentHashMap`, accepted `Map<String, Object> properties` with
`additionalProperties: true`, and answered `"phase": "1-shallow"`. The
remaining 7 carry `.bian-graduated` and own their code.

Meanwhile the generator had grown a second way to produce that Java:
`render.py` emits controllers, repositories and an ISO 4217 table from Python
f-strings — Java that cannot be compiled, read or tested until a repo is
stamped.

This module is the third option: read the catalog at **runtime**.

| Engine | Replaces |
|---|---|
| `spec/FieldType` | `SQL_TYPE` + `JAVA_TYPE` + `_columns`, three tables for one vocabulary |
| `validate/RecordValidator` | `additionalProperties: true` — the escape hatch schema v2 exists to close |
| `store/JdbcControlRecordStore` | `render_repository`, 247 f-string lines per domain |
| `api/ControlRecordHandler` | `render_controller`, 161 f-string lines per domain |
| `money/Iso4217`, `money/Ratio` | `render_iso4217`, one copy compiled into every service |

## The rules it keeps

- **Every statement filters `tenant_id`.** There is no tenant-free overload, so
  a tenantless query cannot be written by accident. `TenantResolver` fails
  closed: no default tenant, ever.
- **Every value is a bind parameter.** Table and column names cannot be bound,
  so they pass `Identifiers.SAFE` when the spec loads and a spec that could
  inject never serves traffic.
- **No in-memory store on the main source path.** `FakeStore` lives in
  `src/test`. An in-memory fallback in a banking service is a data-loss bug
  that passes its own tests.
- **No decimal anywhere.** Money is signed `int64` minor units scaled by the
  one ISO 4217 table; a ratio is an exact `int64` pair compared by
  cross-multiplication under `Math.multiplyExact`, so an overflow throws
  instead of returning a wrong profit share.

## Verified

`mvn test` — **57 tests, 0 failures**. `CatalogReaderTest` reads the real
`catalog/islamic-service-landscape.json`: every service domain loads, every
field maps onto the closed vocabulary, every ratio carries its denominator
bound. Three guarantees were mutation-checked — drop the tenant filter, make a
ratio one column, stop rejecting undeclared fields — and each one killed its
named test.

## Not done

- Nothing consumes this yet. The 203 repos still hold their scaffold; wiring
  one service to the engine, and only then deleting `render.py`'s Java
  emitters, is the next step.
- Catalog **rules** (607 of them) are not interpreted here yet — `ShariahRules`
  is still generated.
- No integration test against real Postgres: the SQL is asserted as text, which
  catches a wrong statement but not a wrong schema.
- The BIAN estate cannot use this until `bian-platform/catalog` is upgraded from
  v1 (three fields per entry) to schema v2.
