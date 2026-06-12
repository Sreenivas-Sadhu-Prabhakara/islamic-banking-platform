# islamic-banking-platform

A **Shariah-compliant core-banking microservice landscape** — 48 service domains modelled in the BIAN service-domain style but **Shariah-native**: Mudarabah profit-sharing instead of interest, Murabaha cost-plus sale, Ijara leasing, Sukuk, Takaful, Zakat, and a full Shariah-governance layer.

> 📒 **[ISLAMIC MASTER CATALOG](ISLAMIC-MASTER-CATALOG.md)** — every domain explained: link, purpose, 3+ use cases, banking type, and the Islamic-finance backends it integrates with (AAOIFI, IFSB, Bursa Suq Al-Sila', iMAL, FLEXCUBE Islamic, …).

## ⚠️ Total isolation by design

This landscape shares **nothing** with the conventional [bian-platform](https://github.com/Sreenivas-Sadhu-Prabhakara/bian-platform):

| | Conventional | Islamic (this) |
|---|---|---|
| Repos | `sd-*` | **`isb-*`** |
| Packages | `com.bank.bian` | **`com.bank.islamic`** |
| Event topics | `bian.*` | **`isb.*`** |
| K8s namespaces | `bian-*` | **`isb-*`** |
| Mesh identity | `part-of: bian-platform` | **`part-of: islamic-platform`** |
| Catalog/template/generator | own copies | **own copies** |

No shared libraries, no cross-references, no mixed deployments.

## What's here

| Path | What |
|---|---|
| `catalog/islamic-service-landscape.json` | **Source of truth** — 5 business areas → 10 business domains → 48 service domains |
| `generator/` | Stamps one git repo per domain from the Islamic golden template |
| `platform-infra/` | Namespaces per Islamic business area |
| `scripts/` | Master-catalog generator · GitHub publishing |
| [`ISLAMIC-MASTER-CATALOG.md`](ISLAMIC-MASTER-CATALOG.md) | The full explained catalog |

Generated landscape: **`../islamic-banking-services/`** — 48 sibling git repos (`isb-murabaha-financing`, `isb-sukuk-issuance`, …) + registry.

## Quick start

```bash
# any domain standalone:
git clone https://github.com/Sreenivas-Sadhu-Prabhakara/isb-murabaha-financing
mvn -f isb-murabaha-financing spring-boot:run     # → :8080/swagger-ui.html

# regenerate the landscape from the catalog:
python3 generator/generate.py        # --force to re-stamp

# Kubernetes:
kubectl apply -f platform-infra/namespaces.yaml
helm install isb-murabaha-financing ../islamic-banking-services/isb-murabaha-financing/helm -n isb-financing
```

**Every repo ships:** BIAN-style semantic API over its control record · per-repo OpenAPI + event contracts (`api/`) · a **contract-test suite** failing the build on code↔contract drift · Dockerfile · Helm chart · CI.

## Phase roadmap

Phase 1 (this): full landscape, shallow but runnable + contracts + tests. Phase 2: deepen flagship domains — Murabaha origination math (cost+markup schedules), Mudarabah profit-distribution engine (pool weighting, PER/IRR), Zakat calculation (nisab thresholds), late-payment-to-charity flows — following the conventional platform's graduation model.

---

*Educational reference implementation. Actual Shariah compliance of any deployment requires certification by a qualified Shariah Supervisory Board.*
