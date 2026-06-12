#!/usr/bin/env python3
"""Generate ISLAMIC-MASTER-CATALOG.md — every Shariah-compliant service domain
explained: link, purpose, 3+ use cases, banking classification, and the
Islamic-finance backends it typically integrates with.

    python3 scripts/generate-master-catalog.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = json.loads((HERE / "../../islamic-banking-services/registry.json").read_text())
OUT = HERE / "../ISLAMIC-MASTER-CATALOG.md"
GH = "https://github.com/Sreenivas-Sadhu-Prabhakara"

DOMAIN_META = {
    "Shariah Governance": dict(
        kind="Shariah governance (mandatory layer across every Islamic banking line)",
        providers=["Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards",
                   "Screening data: Refinitiv/LSEG Islamic indices, IdealRatings",
                   "SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)"],
        cases=["Maintain {asset} records as the authoritative Shariah-governance source",
               "Evidence Shariah compliance for products, contracts, and campaigns before launch",
               "Drive periodic Shariah audit cycles and remediation tracking",
               "Compute/route obligatory religious dues with full auditability"]),
    "Islamic Deposits": dict(
        kind="Islamic retail banking (deposits — non-interest-bearing by construction)",
        providers=["Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic",
                   "Profit-distribution engines; AAOIFI-aligned GL",
                   "Channels: any conventional digital-banking front-end (the contract is the boundary)"],
        cases=["Open and service {asset} records under the correct contract (Wadiah/Qard/Mudarabah/Wakala)",
               "Gate activation on KYC + Shariah screening outcomes",
               "Attribute investment-account balances to profit-sharing pools (no interest accrual, ever)",
               "Stream postings to financial-crime monitoring"]),
    "Profit Management": dict(
        kind="Islamic retail & treasury (the profit-sharing engine that replaces interest)",
        providers=["Islamic core profit engines (iMAL, FLEXCUBE Islamic)",
                   "AAOIFI FAS-aligned accounting; actuarial/reserve tooling"],
        cases=["Run periodic {asset} cycles: pool income → weightings → Mudarib share → account holders",
               "Smooth returns across periods via reserves (PER/IRR) with full disclosure",
               "Publish profit rates to channels and regulators with calculation lineage"]),
    "Sale Based Financing": dict(
        kind="Islamic retail & corporate financing (sale/cost-plus structures)",
        providers=["Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)",
                   "Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)",
                   "Asset registries, valuers, and supplier networks (the bank actually buys the asset)"],
        cases=["Originate {asset} deals: asset purchase → markup disclosure → deferred-sale to customer",
               "Execute commodity legs with brokers and evidence constructive possession",
               "Service installment schedules where the markup is fixed at contract (never recalculated as interest)",
               "Route late-payment amounts to charity, not income (Shariah requirement)"]),
    "Lease And Partnership Financing": dict(
        kind="Islamic retail & corporate financing (lease/equity structures)",
        providers=["Islamic cores + leasing modules; land/vehicle registries",
                   "Takaful providers (asset coverage is typically mandatory)",
                   "Property valuers; co-ownership accounting"],
        cases=["Operate {asset} arrangements with bank ownership reflected for the lease/partnership term",
               "Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules",
               "Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)",
               "Handle maintenance/takaful obligations that follow ownership, not the customer"]),
    "Sukuk": dict(
        kind="Islamic capital markets & treasury",
        providers=["Standards: AAOIFI Sukuk standards, IIFM documentation",
                   "CSDs/ICSDs: Euroclear/Clearstream, national CSDs; paying agents",
                   "Listing venues (Nasdaq Dubai, Bursa Malaysia); Bloomberg/IdealRatings Sukuk data"],
        cases=["Structure and issue {asset} programs with underlying-asset linkage evidenced",
               "Maintain holdings, periodic distributions, and dissolution events",
               "Manage portfolios for HQLA/liquidity purposes under IFSB rules"]),
    "Islamic Treasury": dict(
        kind="Islamic treasury & markets (interest-free liquidity and hedging)",
        providers=["Interbank: commodity Murabaha counterparties via Bursa Suq Al-Sila'/DDCAP",
                   "IIFM/ISDA Tahawwut master agreements (Wa'd-based hedging)",
                   "Central-bank Islamic facilities; Murex/Calypso Islamic configurations"],
        cases=["Place/accept interbank liquidity via {asset} structures instead of interest-bearing deposits",
               "Hedge FX exposure with unilateral promise (Wa'd) constructs documented per IIFM",
               "Screen instruments/equities for Shariah eligibility before treasury investment"]),
    "Takaful": dict(
        kind="Takaful (Islamic cooperative insurance)",
        providers=["Takaful cores: Azentio, Beyontec; retakaful: Hannover ReTakaful, Malaysian Re",
                   "AAOIFI FAS for Takaful accounting; actuarial platforms"],
        cases=["Administer {asset} records under Wakala/Mudarabah operator models",
               "Process claims from the participants' risk pool with surplus-sharing rules",
               "Arrange retakaful capacity treaty-by-treaty"]),
    "Islamic Cards and Payments": dict(
        kind="Islamic retail payments & cards (fee-based, riba-free)",
        providers=["Networks: Visa/Mastercard (Ujrah/fee-based card programs), local schemes",
                   "Rails (halal-neutral): SWIFT, SEPA, UPI/NPCI, instant-payment systems",
                   "Processors with Islamic product configs (M2P, Marqeta)"],
        cases=["Issue and service {asset} products on fee (Ujrah) structures — no revolving interest",
               "Validate, route, and execute payment instructions with debit/credit atomicity",
               "Charge late amounts to charity pools per Shariah board rulings"]),
    "Shared Operations": dict(
        kind="Universal Islamic banking operations & compliance",
        providers=["AML/screening: NICE Actimize, World-Check (plus Shariah screening data)",
                   "Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle",
                   "Regulators: IFSB-aligned returns; national central banks"],
        cases=["Maintain {asset} records consistently across the Islamic estate",
               "Combine conventional KYC/AML with Shariah-specific screening at onboarding",
               "Produce AAOIFI-basis financials and IFSB regulatory returns",
               "Operate branch/digital channels with products labeled by underlying contract"]),
}

CURATED = {
    "isb-murabaha-financing": [
        "Finance vehicles/equipment/homes: bank buys the asset, sells to the customer at disclosed cost-plus markup",
        "Fix the total deferred price at contract signing — installments never recalculate like interest",
        "Evidence the bank's ownership moment (constructive possession) for Shariah audit",
        "Route any late-payment charges to the charity pool, never to income"],
    "isb-mudarabah-savings-account": [
        "Offer savings where returns come from actual pool profits, not promised interest",
        "Attribute each account's balance-days to the Mudarabah pool for profit distribution",
        "Disclose the bank's Mudarib share and historical profit rates transparently",
        "Bear pool losses by capital (account holders) unless operator negligence — as Shariah requires"],
    "isb-profit-calculation-and-distribution": [
        "Run month-end distribution: pool income → weighted balances → Mudarib share → holder credits",
        "Apply Profit Equalization Reserve smoothing with AAOIFI-compliant disclosure",
        "Publish calculation lineage for SSB review and customer queries",
        "Re-run hypothetical scenarios before changing weightings or fees"],
    "isb-zakat-calculation": [
        "Compute zakat on eligible balances at nisab thresholds for consenting customers",
        "Calculate the bank's own corporate zakat per AAOIFI methodology",
        "Generate certificates customers can use for personal religious compliance",
        "Feed Zakat Distribution with assessed amounts by category of recipient"],
    "isb-sukuk-issuance": [
        "Structure asset-backed/asset-based programs (Ijara, Murabaha, Wakala sukuk) with SSB sign-off evidence",
        "Manage bookbuilding, allocation, and settlement with paying agents and CSDs",
        "Track underlying-asset performance that drives periodic distributions",
        "Handle dissolution and redemption at maturity or trigger events"],
    "isb-takaful-claims-processing": [
        "Process claims as payouts from the participants' mutual pool, not the operator's P&L",
        "Apply Wakala-fee/surplus rules between operator and pool on every settlement",
        "Coordinate retakaful recoveries on large claims",
        "Distribute pool surplus back to participants per the certificate terms"],
}


def slugify(t):
    return t.lower().replace(" ", "-").replace("&", "and")


def entry(svc):
    name, repo = svc["serviceDomain"], svc["repo"]
    meta = DOMAIN_META[svc["businessDomain"]]
    what = (f"Shariah-compliant **{svc['functionalPattern']}** service domain on the "
            f"**{svc['controlRecord']}** control record — the system of record for "
            f"*{svc['assetType']}* within {svc['businessDomain']}.")
    cases = CURATED.get(repo) or [c.format(sd=name, asset=svc["assetType"]) for c in meta["cases"]]
    lines = [f"#### [{name}]({GH}/{repo})",
             "",
             f"`{repo}` · namespace `{svc['namespace']}` · gateway path `/{repo}`",
             "",
             what,
             "",
             f"- **Banking type:** {meta['kind']}",
             "- **Typical use cases:**"]
    lines += [f"  {i + 1}. {c}" for i, c in enumerate(cases)]
    lines += ["- **Integrates with (typical backend providers):**"]
    lines += [f"  - {p}" for p in meta["providers"]]
    lines.append("")
    return "\n".join(lines)


def main():
    svcs = REGISTRY["services"]
    by_area = {}
    for s in svcs:
        by_area.setdefault(s["businessArea"], {}).setdefault(s["businessDomain"], []).append(s)

    out = [f"""# 🕌 Islamic Banking Platform — Master Catalog

**Every Shariah-compliant service domain, explained.** {len(svcs)} independent microservice repositories — modelled in the BIAN service-domain style but **Shariah-native**: profit-sharing (Mudarabah/Musharakah), cost-plus sale (Murabaha), leasing (Ijara), and fee-based (Ujrah/Wakala) structures — **no interest-bearing constructs anywhere**.

> ⚠️ **Total isolation:** this landscape shares **no code, no repos, no namespaces** with the conventional [bian-platform](https://github.com/Sreenivas-Sadhu-Prabhakara/bian-platform). Own catalog, own template, own `isb-*` repositories, own `com.bank.islamic` packages, own `isb.*` event topics.

---

## 🚀 Run anything in 5 commands

```bash
# 0. prerequisites (macOS):  brew install docker kind helm kubectl maven
git clone https://github.com/Sreenivas-Sadhu-Prabhakara/islamic-banking-platform

# 1. run any domain standalone in 10 seconds…
git clone https://github.com/Sreenivas-Sadhu-Prabhakara/isb-murabaha-financing
mvn -f isb-murabaha-financing spring-boot:run   # → http://localhost:8080/swagger-ui.html

# 2. …or generate/refresh the whole landscape from the catalog
python3 islamic-banking-platform/generator/generate.py

# 3. deploy onto Kubernetes (namespaces per Islamic business area)
kubectl apply -f islamic-banking-platform/platform-infra/namespaces.yaml
helm install isb-murabaha-financing isb-murabaha-financing/helm -n isb-financing
```

**Quality bar in every repo:** OpenAPI + event contracts owned per repo (`api/`), a contract-test suite that fails the build if code and contract drift, Helm chart, CI on every push.

---
"""]
    out.append("## 📚 Contents\n")
    for area, domains in by_area.items():
        n = sum(len(v) for v in domains.values())
        out.append(f"- **{area}** ({n} domains)")
        for d in domains:
            out.append(f"  - [{d}](#{slugify(d)}) ({len(domains[d])})")
    out.append("\n---\n")

    for area, domains in by_area.items():
        out.append(f"\n## {area}\n")
        for dname, ss in domains.items():
            meta = DOMAIN_META[dname]
            out.append(f"\n### {dname}\n")
            out.append(f"*{meta['kind']}.*\n")
            for s in ss:
                out.append(entry(s))

    out.append("""
---

*Generated from `islamic-banking-services/registry.json` by `scripts/generate-master-catalog.py`. Educational reference implementation — actual Shariah compliance of any deployment requires certification by a qualified Shariah Supervisory Board.*
""")
    OUT.write_text("\n".join(out))
    print(f"ISLAMIC-MASTER-CATALOG.md written: {len(svcs)} entries, {len(OUT.read_text().splitlines())} lines")

    # ── structured data for the interactive catalog (docs-site/catalog.html) ──
    records = []
    for s in svcs:
        meta = DOMAIN_META[s["businessDomain"]]
        cases = CURATED.get(s["repo"]) or \
            [c.format(sd=s["serviceDomain"], asset=s["assetType"]) for c in meta["cases"]]
        records.append(dict(
            name=s["serviceDomain"], repo=s["repo"], deep=bool(CURATED.get(s["repo"])),
            area=s["businessArea"], domain=s["businessDomain"],
            pattern=s["functionalPattern"], asset=s["assetType"],
            cr=s["controlRecord"], ns=s["namespace"],
            kind=meta["kind"], cases=cases, providers=meta["providers"]))
    js = ("// Generated by scripts/generate-master-catalog.py — do not hand-edit.\n"
          "const GH_OWNER = 'Sreenivas-Sadhu-Prabhakara';\n"
          "const CATALOG = " + json.dumps(records, indent=1) + ";\n")
    (HERE / "../docs-site/catalog-data.js").write_text(js)
    print(f"docs-site/catalog-data.js written: {len(records)} records")


if __name__ == "__main__":
    main()
