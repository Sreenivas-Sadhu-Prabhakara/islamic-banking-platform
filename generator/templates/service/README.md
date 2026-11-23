# __SD_NAME__

BIAN Service Domain microservice — part of the [islamic-platform](../../islamic-platform/) landscape.

| | |
|---|---|
| **Business Area** | __BUSINESS_AREA__ |
| **Business Domain** | __BUSINESS_DOMAIN__ |
| **Functional Pattern** | __FUNCTIONAL_PATTERN__ |
| **Asset Type** | __ASSET_TYPE__ |
| **Control Record** | __CONTROL_RECORD__ |
| **K8s Namespace** | `__NAMESPACE__` |
| **Stack** | Java 21 · Spring Boot 3 · Resilience4j · Cilium mesh |

> ⚠️ **GENERATED. Do not hand-edit.** Every file here was stamped from
> `islamic-banking-platform/generator` out of this service domain's entry in
> `catalog/islamic-service-landscape.json`. Change the catalog entry and
> re-run the generator; a hand edit is reverted by the next `--force` stamp.
>
> **UNREVIEWED — requires named Shariah board sign-off.** Every Shariah-bearing
> field, rule and standard reference was modelled by an engineer from a research
> record and reviewed by no Shariah supervisory board. See
> [`docs/SHARIAH-GAPS.md`](docs/SHARIAH-GAPS.md).
>
> **An extension beyond the UK Open Banking Standard**, not part of it: no
> conformance or certification claim attaches to this surface.
>
> **Single-tenant** — there is no `tenant_id` column in this estate — and
> `replicaCount: 1` is load-bearing for money correctness until DB-level
> locking lands in the debit path. Stated rather than faked.
>
> **Money is a signed `int64` count of ISO 4217 MINOR units** everywhere: no
> float, no double, no decimal column. The exponent comes from the generated
> `money/Iso4217` table — BHD/KWD/OMR/TND are 3-decimal and JPY is 0-decimal,
> so a hardcoded ×100 is a bug. A profit-sharing ratio is an exact
> numerator/denominator pair of `int64`s, never a float.
>
> **Rule coverage is partial and listed**: see
> [`docs/RULES-GAPS.md`](docs/RULES-GAPS.md) for every catalog rule this
> service does *not* enforce, and why.

## BIAN Semantic API

| Method | Path | BIAN action term |
|---|---|---|
| GET | `/v1/service-domain` | — (SD metadata) |
| POST | `/v1/__CR_SLUG__/initiate` | Initiate |
| GET | `/v1/__CR_SLUG__` | Retrieve (list) |
| GET | `/v1/__CR_SLUG__/{crId}/retrieve` | Retrieve |
| PUT | `/v1/__CR_SLUG__/{crId}/update` | Update |
| PUT | `/v1/__CR_SLUG__/{crId}/control` | Control — body `{"action": "suspend"\|"resume"\|"terminate"}` |

OpenAPI UI: `/swagger-ui.html` · Health: `/actuator/health` · Metrics: `/actuator/prometheus`

**API contract:** [`api/openapi.yaml`](api/openapi.yaml) — owned by **this repo** (contract-per-repo; no central contracts repo). The runtime spec at `/v3/api-docs` must stay compatible with it; Phase 2 adds contract tests that enforce this.

## Run locally

```bash
mvn spring-boot:run
curl localhost:8080/v1/service-domain

# lifecycle smoke test
curl -X POST localhost:8080/v1/__CR_SLUG__/initiate -H 'content-type: application/json' -d '{"note":"hello"}'
```

## Build & containerize

```bash
mvn -B verify
docker build -t isb/__ARTIFACT_ID__:0.1.0 .
```

## Deploy (Helm → K8s with Cilium mesh)

```bash
helm upgrade --install __ARTIFACT_ID__ ./helm -n __NAMESPACE__
```

Exposed through the platform Gateway at path prefix `/__ARTIFACT_ID__` (Cilium Gateway API). Mesh policy (`CiliumNetworkPolicy`) allows: gateway ingress, same-area peers, Prometheus — everything else denied.
