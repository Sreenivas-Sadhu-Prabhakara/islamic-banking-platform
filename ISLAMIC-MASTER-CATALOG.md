# 🕌 Islamic Banking Platform — Master Catalog

**Every Shariah-compliant service domain, explained.** 48 independent microservice repositories — modelled in the BIAN service-domain style but **Shariah-native**: profit-sharing (Mudarabah/Musharakah), cost-plus sale (Murabaha), leasing (Ijara), and fee-based (Ujrah/Wakala) structures — **no interest-bearing constructs anywhere**.

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

## 📚 Contents

- **Shariah Governance and Compliance** (8 domains)
  - [Shariah Governance](#shariah-governance) (8)
- **Deposits and Investment Accounts** (9 domains)
  - [Islamic Deposits](#islamic-deposits) (5)
  - [Profit Management](#profit-management) (4)
- **Islamic Financing** (12 domains)
  - [Sale Based Financing](#sale-based-financing) (5)
  - [Lease And Partnership Financing](#lease-and-partnership-financing) (7)
- **Treasury Markets and Sukuk** (7 domains)
  - [Sukuk](#sukuk) (3)
  - [Islamic Treasury](#islamic-treasury) (4)
- **Takaful and Shared Operations** (12 domains)
  - [Takaful](#takaful) (3)
  - [Islamic Cards and Payments](#islamic-cards-and-payments) (3)
  - [Shared Operations](#shared-operations) (6)

---


## Shariah Governance and Compliance


### Shariah Governance

*Shariah governance (mandatory layer across every Islamic banking line).*

#### [Shariah Supervisory Board Directory](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-shariah-supervisory-board-directory)

`isb-shariah-supervisory-board-directory` · namespace `isb-governance` · gateway path `/isb-shariah-supervisory-board-directory`

Shariah-compliant **Catalog** service domain on the **SSB Member Mandate Directory Entry** control record — the system of record for *SSB Member Mandate* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain SSB Member Mandate records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Fatwa And Ruling Repository](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-fatwa-and-ruling-repository)

`isb-fatwa-and-ruling-repository` · namespace `isb-governance` · gateway path `/isb-fatwa-and-ruling-repository`

Shariah-compliant **Catalog** service domain on the **Shariah Ruling Directory Entry** control record — the system of record for *Shariah Ruling* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Shariah Ruling records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Shariah Compliance Review](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-shariah-compliance-review)

`isb-shariah-compliance-review` · namespace `isb-governance` · gateway path `/isb-shariah-compliance-review`

Shariah-compliant **Assess** service domain on the **Shariah Compliance Case Assessment** control record — the system of record for *Shariah Compliance Case* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Shariah Compliance Case records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Shariah Audit](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-shariah-audit)

`isb-shariah-audit` · namespace `isb-governance` · gateway path `/isb-shariah-audit`

Shariah-compliant **Assess** service domain on the **Shariah Audit Engagement Assessment** control record — the system of record for *Shariah Audit Engagement* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Shariah Audit Engagement records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Income Purification](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-income-purification)

`isb-income-purification` · namespace `isb-governance` · gateway path `/isb-income-purification`

Shariah-compliant **Process** service domain on the **Purification Entry Procedure** control record — the system of record for *Purification Entry* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Purification Entry records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Zakat Calculation](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-zakat-calculation)

`isb-zakat-calculation` · namespace `isb-governance` · gateway path `/isb-zakat-calculation`

Shariah-compliant **Process** service domain on the **Zakat Assessment Procedure** control record — the system of record for *Zakat Assessment* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Compute zakat on eligible balances at nisab thresholds for consenting customers
  2. Calculate the bank's own corporate zakat per AAOIFI methodology
  3. Generate certificates customers can use for personal religious compliance
  4. Feed Zakat Distribution with assessed amounts by category of recipient
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Zakat Distribution](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-zakat-distribution)

`isb-zakat-distribution` · namespace `isb-governance` · gateway path `/isb-zakat-distribution`

Shariah-compliant **Distribute** service domain on the **Zakat Disbursement Distribution** control record — the system of record for *Zakat Disbursement* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Zakat Disbursement records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)

#### [Sadaqah And Charity Management](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-sadaqah-and-charity-management)

`isb-sadaqah-and-charity-management` · namespace `isb-governance` · gateway path `/isb-sadaqah-and-charity-management`

Shariah-compliant **Manage** service domain on the **Charity Pool Management Plan** control record — the system of record for *Charity Pool* within Shariah Governance.

- **Banking type:** Shariah governance (mandatory layer across every Islamic banking line)
- **Typical use cases:**
  1. Maintain Charity Pool records as the authoritative Shariah-governance source
  2. Evidence Shariah compliance for products, contracts, and campaigns before launch
  3. Drive periodic Shariah audit cycles and remediation tracking
  4. Compute/route obligatory religious dues with full auditability
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Shariah & accounting standards, IFSB prudential standards
  - Screening data: Refinitiv/LSEG Islamic indices, IdealRatings
  - SSB workflow & fatwa management tooling; zakat authorities (e.g. national boards)


## Deposits and Investment Accounts


### Islamic Deposits

*Islamic retail banking (deposits — non-interest-bearing by construction).*

#### [Wadiah Safekeeping Account](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-wadiah-safekeeping-account)

`isb-wadiah-safekeeping-account` · namespace `isb-deposits` · gateway path `/isb-wadiah-safekeeping-account`

Shariah-compliant **Fulfill** service domain on the **Wadiah Custody Account Fulfillment Arrangement** control record — the system of record for *Wadiah Custody Account* within Islamic Deposits.

- **Banking type:** Islamic retail banking (deposits — non-interest-bearing by construction)
- **Typical use cases:**
  1. Open and service Wadiah Custody Account records under the correct contract (Wadiah/Qard/Mudarabah/Wakala)
  2. Gate activation on KYC + Shariah screening outcomes
  3. Attribute investment-account balances to profit-sharing pools (no interest accrual, ever)
  4. Stream postings to financial-crime monitoring
- **Integrates with (typical backend providers):**
  - Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic
  - Profit-distribution engines; AAOIFI-aligned GL
  - Channels: any conventional digital-banking front-end (the contract is the boundary)

#### [Qard Hassan Account](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-qard-hassan-account)

`isb-qard-hassan-account` · namespace `isb-deposits` · gateway path `/isb-qard-hassan-account`

Shariah-compliant **Fulfill** service domain on the **Qard Hassan Account Fulfillment Arrangement** control record — the system of record for *Qard Hassan Account* within Islamic Deposits.

- **Banking type:** Islamic retail banking (deposits — non-interest-bearing by construction)
- **Typical use cases:**
  1. Open and service Qard Hassan Account records under the correct contract (Wadiah/Qard/Mudarabah/Wakala)
  2. Gate activation on KYC + Shariah screening outcomes
  3. Attribute investment-account balances to profit-sharing pools (no interest accrual, ever)
  4. Stream postings to financial-crime monitoring
- **Integrates with (typical backend providers):**
  - Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic
  - Profit-distribution engines; AAOIFI-aligned GL
  - Channels: any conventional digital-banking front-end (the contract is the boundary)

#### [Mudarabah Savings Account](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-mudarabah-savings-account)

`isb-mudarabah-savings-account` · namespace `isb-deposits` · gateway path `/isb-mudarabah-savings-account`

Shariah-compliant **Fulfill** service domain on the **Mudarabah Savings Account Fulfillment Arrangement** control record — the system of record for *Mudarabah Savings Account* within Islamic Deposits.

- **Banking type:** Islamic retail banking (deposits — non-interest-bearing by construction)
- **Typical use cases:**
  1. Offer savings where returns come from actual pool profits, not promised interest
  2. Attribute each account's balance-days to the Mudarabah pool for profit distribution
  3. Disclose the bank's Mudarib share and historical profit rates transparently
  4. Bear pool losses by capital (account holders) unless operator negligence — as Shariah requires
- **Integrates with (typical backend providers):**
  - Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic
  - Profit-distribution engines; AAOIFI-aligned GL
  - Channels: any conventional digital-banking front-end (the contract is the boundary)

#### [Mudarabah Term Investment Account](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-mudarabah-term-investment-account)

`isb-mudarabah-term-investment-account` · namespace `isb-deposits` · gateway path `/isb-mudarabah-term-investment-account`

Shariah-compliant **Fulfill** service domain on the **Mudarabah Investment Account Fulfillment Arrangement** control record — the system of record for *Mudarabah Investment Account* within Islamic Deposits.

- **Banking type:** Islamic retail banking (deposits — non-interest-bearing by construction)
- **Typical use cases:**
  1. Open and service Mudarabah Investment Account records under the correct contract (Wadiah/Qard/Mudarabah/Wakala)
  2. Gate activation on KYC + Shariah screening outcomes
  3. Attribute investment-account balances to profit-sharing pools (no interest accrual, ever)
  4. Stream postings to financial-crime monitoring
- **Integrates with (typical backend providers):**
  - Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic
  - Profit-distribution engines; AAOIFI-aligned GL
  - Channels: any conventional digital-banking front-end (the contract is the boundary)

#### [Wakala Investment Account](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-wakala-investment-account)

`isb-wakala-investment-account` · namespace `isb-deposits` · gateway path `/isb-wakala-investment-account`

Shariah-compliant **Fulfill** service domain on the **Wakala Investment Account Fulfillment Arrangement** control record — the system of record for *Wakala Investment Account* within Islamic Deposits.

- **Banking type:** Islamic retail banking (deposits — non-interest-bearing by construction)
- **Typical use cases:**
  1. Open and service Wakala Investment Account records under the correct contract (Wadiah/Qard/Mudarabah/Wakala)
  2. Gate activation on KYC + Shariah screening outcomes
  3. Attribute investment-account balances to profit-sharing pools (no interest accrual, ever)
  4. Stream postings to financial-crime monitoring
- **Integrates with (typical backend providers):**
  - Islamic cores: Azentio iMAL, Oracle FLEXCUBE Islamic, Temenos Islamic Banking, ICS BANKS Islamic
  - Profit-distribution engines; AAOIFI-aligned GL
  - Channels: any conventional digital-banking front-end (the contract is the boundary)


### Profit Management

*Islamic retail & treasury (the profit-sharing engine that replaces interest).*

#### [Profit Calculation And Distribution](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-profit-calculation-and-distribution)

`isb-profit-calculation-and-distribution` · namespace `isb-deposits` · gateway path `/isb-profit-calculation-and-distribution`

Shariah-compliant **Process** service domain on the **Profit Distribution Run Procedure** control record — the system of record for *Profit Distribution Run* within Profit Management.

- **Banking type:** Islamic retail & treasury (the profit-sharing engine that replaces interest)
- **Typical use cases:**
  1. Run month-end distribution: pool income → weighted balances → Mudarib share → holder credits
  2. Apply Profit Equalization Reserve smoothing with AAOIFI-compliant disclosure
  3. Publish calculation lineage for SSB review and customer queries
  4. Re-run hypothetical scenarios before changing weightings or fees
- **Integrates with (typical backend providers):**
  - Islamic core profit engines (iMAL, FLEXCUBE Islamic)
  - AAOIFI FAS-aligned accounting; actuarial/reserve tooling

#### [Profit Equalization Reserve](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-profit-equalization-reserve)

`isb-profit-equalization-reserve` · namespace `isb-deposits` · gateway path `/isb-profit-equalization-reserve`

Shariah-compliant **Manage** service domain on the **Profit Equalization Reserve Management Plan** control record — the system of record for *Profit Equalization Reserve* within Profit Management.

- **Banking type:** Islamic retail & treasury (the profit-sharing engine that replaces interest)
- **Typical use cases:**
  1. Run periodic Profit Equalization Reserve cycles: pool income → weightings → Mudarib share → account holders
  2. Smooth returns across periods via reserves (PER/IRR) with full disclosure
  3. Publish profit rates to channels and regulators with calculation lineage
- **Integrates with (typical backend providers):**
  - Islamic core profit engines (iMAL, FLEXCUBE Islamic)
  - AAOIFI FAS-aligned accounting; actuarial/reserve tooling

#### [Investment Risk Reserve](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-investment-risk-reserve)

`isb-investment-risk-reserve` · namespace `isb-deposits` · gateway path `/isb-investment-risk-reserve`

Shariah-compliant **Manage** service domain on the **Investment Risk Reserve Management Plan** control record — the system of record for *Investment Risk Reserve* within Profit Management.

- **Banking type:** Islamic retail & treasury (the profit-sharing engine that replaces interest)
- **Typical use cases:**
  1. Run periodic Investment Risk Reserve cycles: pool income → weightings → Mudarib share → account holders
  2. Smooth returns across periods via reserves (PER/IRR) with full disclosure
  3. Publish profit rates to channels and regulators with calculation lineage
- **Integrates with (typical backend providers):**
  - Islamic core profit engines (iMAL, FLEXCUBE Islamic)
  - AAOIFI FAS-aligned accounting; actuarial/reserve tooling

#### [Hibah Discretionary Gift](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-hibah-discretionary-gift)

`isb-hibah-discretionary-gift` · namespace `isb-deposits` · gateway path `/isb-hibah-discretionary-gift`

Shariah-compliant **Process** service domain on the **Hibah Award Procedure** control record — the system of record for *Hibah Award* within Profit Management.

- **Banking type:** Islamic retail & treasury (the profit-sharing engine that replaces interest)
- **Typical use cases:**
  1. Run periodic Hibah Award cycles: pool income → weightings → Mudarib share → account holders
  2. Smooth returns across periods via reserves (PER/IRR) with full disclosure
  3. Publish profit rates to channels and regulators with calculation lineage
- **Integrates with (typical backend providers):**
  - Islamic core profit engines (iMAL, FLEXCUBE Islamic)
  - AAOIFI FAS-aligned accounting; actuarial/reserve tooling


## Islamic Financing


### Sale Based Financing

*Islamic retail & corporate financing (sale/cost-plus structures).*

#### [Murabaha Financing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-murabaha-financing)

`isb-murabaha-financing` · namespace `isb-financing` · gateway path `/isb-murabaha-financing`

Shariah-compliant **Fulfill** service domain on the **Murabaha Facility Fulfillment Arrangement** control record — the system of record for *Murabaha Facility* within Sale Based Financing.

- **Banking type:** Islamic retail & corporate financing (sale/cost-plus structures)
- **Typical use cases:**
  1. Finance vehicles/equipment/homes: bank buys the asset, sells to the customer at disclosed cost-plus markup
  2. Fix the total deferred price at contract signing — installments never recalculate like interest
  3. Evidence the bank's ownership moment (constructive possession) for Shariah audit
  4. Route any late-payment charges to the charity pool, never to income
- **Integrates with (typical backend providers):**
  - Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)
  - Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)
  - Asset registries, valuers, and supplier networks (the bank actually buys the asset)

#### [Commodity Murabaha Tawarruq](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-commodity-murabaha-tawarruq)

`isb-commodity-murabaha-tawarruq` · namespace `isb-financing` · gateway path `/isb-commodity-murabaha-tawarruq`

Shariah-compliant **Process** service domain on the **Tawarruq Transaction Procedure** control record — the system of record for *Tawarruq Transaction* within Sale Based Financing.

- **Banking type:** Islamic retail & corporate financing (sale/cost-plus structures)
- **Typical use cases:**
  1. Originate Tawarruq Transaction deals: asset purchase → markup disclosure → deferred-sale to customer
  2. Execute commodity legs with brokers and evidence constructive possession
  3. Service installment schedules where the markup is fixed at contract (never recalculated as interest)
  4. Route late-payment amounts to charity, not income (Shariah requirement)
- **Integrates with (typical backend providers):**
  - Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)
  - Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)
  - Asset registries, valuers, and supplier networks (the bank actually buys the asset)

#### [Istisna Construction Financing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-istisna-construction-financing)

`isb-istisna-construction-financing` · namespace `isb-financing` · gateway path `/isb-istisna-construction-financing`

Shariah-compliant **Fulfill** service domain on the **Istisna Facility Fulfillment Arrangement** control record — the system of record for *Istisna Facility* within Sale Based Financing.

- **Banking type:** Islamic retail & corporate financing (sale/cost-plus structures)
- **Typical use cases:**
  1. Originate Istisna Facility deals: asset purchase → markup disclosure → deferred-sale to customer
  2. Execute commodity legs with brokers and evidence constructive possession
  3. Service installment schedules where the markup is fixed at contract (never recalculated as interest)
  4. Route late-payment amounts to charity, not income (Shariah requirement)
- **Integrates with (typical backend providers):**
  - Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)
  - Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)
  - Asset registries, valuers, and supplier networks (the bank actually buys the asset)

#### [Salam Commodity Forward](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-salam-commodity-forward)

`isb-salam-commodity-forward` · namespace `isb-financing` · gateway path `/isb-salam-commodity-forward`

Shariah-compliant **Fulfill** service domain on the **Salam Contract Fulfillment Arrangement** control record — the system of record for *Salam Contract* within Sale Based Financing.

- **Banking type:** Islamic retail & corporate financing (sale/cost-plus structures)
- **Typical use cases:**
  1. Originate Salam Contract deals: asset purchase → markup disclosure → deferred-sale to customer
  2. Execute commodity legs with brokers and evidence constructive possession
  3. Service installment schedules where the markup is fixed at contract (never recalculated as interest)
  4. Route late-payment amounts to charity, not income (Shariah requirement)
- **Integrates with (typical backend providers):**
  - Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)
  - Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)
  - Asset registries, valuers, and supplier networks (the bank actually buys the asset)

#### [Asset Acquisition Agency](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-asset-acquisition-agency)

`isb-asset-acquisition-agency` · namespace `isb-financing` · gateway path `/isb-asset-acquisition-agency`

Shariah-compliant **Process** service domain on the **Wakala Purchase Mandate Procedure** control record — the system of record for *Wakala Purchase Mandate* within Sale Based Financing.

- **Banking type:** Islamic retail & corporate financing (sale/cost-plus structures)
- **Typical use cases:**
  1. Originate Wakala Purchase Mandate deals: asset purchase → markup disclosure → deferred-sale to customer
  2. Execute commodity legs with brokers and evidence constructive possession
  3. Service installment schedules where the markup is fixed at contract (never recalculated as interest)
  4. Route late-payment amounts to charity, not income (Shariah requirement)
- **Integrates with (typical backend providers):**
  - Commodity platforms: Bursa Suq Al-Sila', DDCAP ETHOS (for Tawarruq)
  - Islamic LOS modules (iMAL, FLEXCUBE Islamic, Temenos)
  - Asset registries, valuers, and supplier networks (the bank actually buys the asset)


### Lease And Partnership Financing

*Islamic retail & corporate financing (lease/equity structures).*

#### [Ijara Leasing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-ijara-leasing)

`isb-ijara-leasing` · namespace `isb-financing` · gateway path `/isb-ijara-leasing`

Shariah-compliant **Fulfill** service domain on the **Ijara Lease Fulfillment Arrangement** control record — the system of record for *Ijara Lease* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Ijara Lease arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Ijara Muntahia Bittamleek](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-ijara-muntahia-bittamleek)

`isb-ijara-muntahia-bittamleek` · namespace `isb-financing` · gateway path `/isb-ijara-muntahia-bittamleek`

Shariah-compliant **Fulfill** service domain on the **Lease To Own Arrangement Fulfillment Arrangement** control record — the system of record for *Lease To Own Arrangement* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Lease To Own Arrangement arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Diminishing Musharakah Home Finance](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-diminishing-musharakah-home-finance)

`isb-diminishing-musharakah-home-finance` · namespace `isb-financing` · gateway path `/isb-diminishing-musharakah-home-finance`

Shariah-compliant **Fulfill** service domain on the **Diminishing Musharakah Facility Fulfillment Arrangement** control record — the system of record for *Diminishing Musharakah Facility* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Diminishing Musharakah Facility arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Musharakah Partnership Financing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-musharakah-partnership-financing)

`isb-musharakah-partnership-financing` · namespace `isb-financing` · gateway path `/isb-musharakah-partnership-financing`

Shariah-compliant **Fulfill** service domain on the **Musharakah Facility Fulfillment Arrangement** control record — the system of record for *Musharakah Facility* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Musharakah Facility arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Mudarabah Venture Financing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-mudarabah-venture-financing)

`isb-mudarabah-venture-financing` · namespace `isb-financing` · gateway path `/isb-mudarabah-venture-financing`

Shariah-compliant **Fulfill** service domain on the **Mudarabah Facility Fulfillment Arrangement** control record — the system of record for *Mudarabah Facility* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Mudarabah Facility arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Qard Hassan Benevolent Loan](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-qard-hassan-benevolent-loan)

`isb-qard-hassan-benevolent-loan` · namespace `isb-financing` · gateway path `/isb-qard-hassan-benevolent-loan`

Shariah-compliant **Fulfill** service domain on the **Qard Hassan Facility Fulfillment Arrangement** control record — the system of record for *Qard Hassan Facility* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Qard Hassan Facility arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting

#### [Late Payment Charity Handling](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-late-payment-charity-handling)

`isb-late-payment-charity-handling` · namespace `isb-financing` · gateway path `/isb-late-payment-charity-handling`

Shariah-compliant **Process** service domain on the **Late Payment Charity Entry Procedure** control record — the system of record for *Late Payment Charity Entry* within Lease And Partnership Financing.

- **Banking type:** Islamic retail & corporate financing (lease/equity structures)
- **Typical use cases:**
  1. Operate Late Payment Charity Entry arrangements with bank ownership reflected for the lease/partnership term
  2. Adjust rentals/units as ownership diminishes (Diminishing Musharakah) with transparent schedules
  3. Share venture outcomes by pre-agreed ratios — losses borne by capital, not penalized (Mudarabah/Musharakah)
  4. Handle maintenance/takaful obligations that follow ownership, not the customer
- **Integrates with (typical backend providers):**
  - Islamic cores + leasing modules; land/vehicle registries
  - Takaful providers (asset coverage is typically mandatory)
  - Property valuers; co-ownership accounting


## Treasury Markets and Sukuk


### Sukuk

*Islamic capital markets & treasury.*

#### [Sukuk Issuance](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-sukuk-issuance)

`isb-sukuk-issuance` · namespace `isb-treasury` · gateway path `/isb-sukuk-issuance`

Shariah-compliant **Process** service domain on the **Sukuk Issuance Program Procedure** control record — the system of record for *Sukuk Issuance Program* within Sukuk.

- **Banking type:** Islamic capital markets & treasury
- **Typical use cases:**
  1. Structure asset-backed/asset-based programs (Ijara, Murabaha, Wakala sukuk) with SSB sign-off evidence
  2. Manage bookbuilding, allocation, and settlement with paying agents and CSDs
  3. Track underlying-asset performance that drives periodic distributions
  4. Handle dissolution and redemption at maturity or trigger events
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Sukuk standards, IIFM documentation
  - CSDs/ICSDs: Euroclear/Clearstream, national CSDs; paying agents
  - Listing venues (Nasdaq Dubai, Bursa Malaysia); Bloomberg/IdealRatings Sukuk data

#### [Sukuk Registry And Custody](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-sukuk-registry-and-custody)

`isb-sukuk-registry-and-custody` · namespace `isb-treasury` · gateway path `/isb-sukuk-registry-and-custody`

Shariah-compliant **Administer** service domain on the **Sukuk Holding Administrative Plan** control record — the system of record for *Sukuk Holding* within Sukuk.

- **Banking type:** Islamic capital markets & treasury
- **Typical use cases:**
  1. Structure and issue Sukuk Holding programs with underlying-asset linkage evidenced
  2. Maintain holdings, periodic distributions, and dissolution events
  3. Manage portfolios for HQLA/liquidity purposes under IFSB rules
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Sukuk standards, IIFM documentation
  - CSDs/ICSDs: Euroclear/Clearstream, national CSDs; paying agents
  - Listing venues (Nasdaq Dubai, Bursa Malaysia); Bloomberg/IdealRatings Sukuk data

#### [Sukuk Portfolio Management](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-sukuk-portfolio-management)

`isb-sukuk-portfolio-management` · namespace `isb-treasury` · gateway path `/isb-sukuk-portfolio-management`

Shariah-compliant **Manage** service domain on the **Sukuk Portfolio Management Plan** control record — the system of record for *Sukuk Portfolio* within Sukuk.

- **Banking type:** Islamic capital markets & treasury
- **Typical use cases:**
  1. Structure and issue Sukuk Portfolio programs with underlying-asset linkage evidenced
  2. Maintain holdings, periodic distributions, and dissolution events
  3. Manage portfolios for HQLA/liquidity purposes under IFSB rules
- **Integrates with (typical backend providers):**
  - Standards: AAOIFI Sukuk standards, IIFM documentation
  - CSDs/ICSDs: Euroclear/Clearstream, national CSDs; paying agents
  - Listing venues (Nasdaq Dubai, Bursa Malaysia); Bloomberg/IdealRatings Sukuk data


### Islamic Treasury

*Islamic treasury & markets (interest-free liquidity and hedging).*

#### [Interbank Commodity Murabaha Desk](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-interbank-commodity-murabaha-desk)

`isb-interbank-commodity-murabaha-desk` · namespace `isb-treasury` · gateway path `/isb-interbank-commodity-murabaha-desk`

Shariah-compliant **Operate** service domain on the **Interbank Murabaha Deal Operating Session** control record — the system of record for *Interbank Murabaha Deal* within Islamic Treasury.

- **Banking type:** Islamic treasury & markets (interest-free liquidity and hedging)
- **Typical use cases:**
  1. Place/accept interbank liquidity via Interbank Murabaha Deal structures instead of interest-bearing deposits
  2. Hedge FX exposure with unilateral promise (Wa'd) constructs documented per IIFM
  3. Screen instruments/equities for Shariah eligibility before treasury investment
- **Integrates with (typical backend providers):**
  - Interbank: commodity Murabaha counterparties via Bursa Suq Al-Sila'/DDCAP
  - IIFM/ISDA Tahawwut master agreements (Wa'd-based hedging)
  - Central-bank Islamic facilities; Murex/Calypso Islamic configurations

#### [Islamic FX Wad Arrangements](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-islamic-fx-wad-arrangements)

`isb-islamic-fx-wad-arrangements` · namespace `isb-treasury` · gateway path `/isb-islamic-fx-wad-arrangements`

Shariah-compliant **Process** service domain on the **Wad FX Arrangement Procedure** control record — the system of record for *Wad FX Arrangement* within Islamic Treasury.

- **Banking type:** Islamic treasury & markets (interest-free liquidity and hedging)
- **Typical use cases:**
  1. Place/accept interbank liquidity via Wad FX Arrangement structures instead of interest-bearing deposits
  2. Hedge FX exposure with unilateral promise (Wa'd) constructs documented per IIFM
  3. Screen instruments/equities for Shariah eligibility before treasury investment
- **Integrates with (typical backend providers):**
  - Interbank: commodity Murabaha counterparties via Bursa Suq Al-Sila'/DDCAP
  - IIFM/ISDA Tahawwut master agreements (Wa'd-based hedging)
  - Central-bank Islamic facilities; Murex/Calypso Islamic configurations

#### [Shariah Compliant Liquidity Management](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-shariah-compliant-liquidity-management)

`isb-shariah-compliant-liquidity-management` · namespace `isb-treasury` · gateway path `/isb-shariah-compliant-liquidity-management`

Shariah-compliant **Manage** service domain on the **Liquidity Position Management Plan** control record — the system of record for *Liquidity Position* within Islamic Treasury.

- **Banking type:** Islamic treasury & markets (interest-free liquidity and hedging)
- **Typical use cases:**
  1. Place/accept interbank liquidity via Liquidity Position structures instead of interest-bearing deposits
  2. Hedge FX exposure with unilateral promise (Wa'd) constructs documented per IIFM
  3. Screen instruments/equities for Shariah eligibility before treasury investment
- **Integrates with (typical backend providers):**
  - Interbank: commodity Murabaha counterparties via Bursa Suq Al-Sila'/DDCAP
  - IIFM/ISDA Tahawwut master agreements (Wa'd-based hedging)
  - Central-bank Islamic facilities; Murex/Calypso Islamic configurations

#### [Halal Equity Screening](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-halal-equity-screening)

`isb-halal-equity-screening` · namespace `isb-treasury` · gateway path `/isb-halal-equity-screening`

Shariah-compliant **Assess** service domain on the **Equity Screening Result Assessment** control record — the system of record for *Equity Screening Result* within Islamic Treasury.

- **Banking type:** Islamic treasury & markets (interest-free liquidity and hedging)
- **Typical use cases:**
  1. Place/accept interbank liquidity via Equity Screening Result structures instead of interest-bearing deposits
  2. Hedge FX exposure with unilateral promise (Wa'd) constructs documented per IIFM
  3. Screen instruments/equities for Shariah eligibility before treasury investment
- **Integrates with (typical backend providers):**
  - Interbank: commodity Murabaha counterparties via Bursa Suq Al-Sila'/DDCAP
  - IIFM/ISDA Tahawwut master agreements (Wa'd-based hedging)
  - Central-bank Islamic facilities; Murex/Calypso Islamic configurations


## Takaful and Shared Operations


### Takaful

*Takaful (Islamic cooperative insurance).*

#### [Takaful Policy Administration](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-takaful-policy-administration)

`isb-takaful-policy-administration` · namespace `isb-operations` · gateway path `/isb-takaful-policy-administration`

Shariah-compliant **Administer** service domain on the **Takaful Certificate Administrative Plan** control record — the system of record for *Takaful Certificate* within Takaful.

- **Banking type:** Takaful (Islamic cooperative insurance)
- **Typical use cases:**
  1. Administer Takaful Certificate records under Wakala/Mudarabah operator models
  2. Process claims from the participants' risk pool with surplus-sharing rules
  3. Arrange retakaful capacity treaty-by-treaty
- **Integrates with (typical backend providers):**
  - Takaful cores: Azentio, Beyontec; retakaful: Hannover ReTakaful, Malaysian Re
  - AAOIFI FAS for Takaful accounting; actuarial platforms

#### [Takaful Claims Processing](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-takaful-claims-processing)

`isb-takaful-claims-processing` · namespace `isb-operations` · gateway path `/isb-takaful-claims-processing`

Shariah-compliant **Process** service domain on the **Takaful Claim Procedure** control record — the system of record for *Takaful Claim* within Takaful.

- **Banking type:** Takaful (Islamic cooperative insurance)
- **Typical use cases:**
  1. Process claims as payouts from the participants' mutual pool, not the operator's P&L
  2. Apply Wakala-fee/surplus rules between operator and pool on every settlement
  3. Coordinate retakaful recoveries on large claims
  4. Distribute pool surplus back to participants per the certificate terms
- **Integrates with (typical backend providers):**
  - Takaful cores: Azentio, Beyontec; retakaful: Hannover ReTakaful, Malaysian Re
  - AAOIFI FAS for Takaful accounting; actuarial platforms

#### [Retakaful Arrangement](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-retakaful-arrangement)

`isb-retakaful-arrangement` · namespace `isb-operations` · gateway path `/isb-retakaful-arrangement`

Shariah-compliant **Manage** service domain on the **Retakaful Treaty Management Plan** control record — the system of record for *Retakaful Treaty* within Takaful.

- **Banking type:** Takaful (Islamic cooperative insurance)
- **Typical use cases:**
  1. Administer Retakaful Treaty records under Wakala/Mudarabah operator models
  2. Process claims from the participants' risk pool with surplus-sharing rules
  3. Arrange retakaful capacity treaty-by-treaty
- **Integrates with (typical backend providers):**
  - Takaful cores: Azentio, Beyontec; retakaful: Hannover ReTakaful, Malaysian Re
  - AAOIFI FAS for Takaful accounting; actuarial platforms


### Islamic Cards and Payments

*Islamic retail payments & cards (fee-based, riba-free).*

#### [Ujrah Card Services](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-ujrah-card-services)

`isb-ujrah-card-services` · namespace `isb-operations` · gateway path `/isb-ujrah-card-services`

Shariah-compliant **Fulfill** service domain on the **Ujrah Card Facility Fulfillment Arrangement** control record — the system of record for *Ujrah Card Facility* within Islamic Cards and Payments.

- **Banking type:** Islamic retail payments & cards (fee-based, riba-free)
- **Typical use cases:**
  1. Issue and service Ujrah Card Facility products on fee (Ujrah) structures — no revolving interest
  2. Validate, route, and execute payment instructions with debit/credit atomicity
  3. Charge late amounts to charity pools per Shariah board rulings
- **Integrates with (typical backend providers):**
  - Networks: Visa/Mastercard (Ujrah/fee-based card programs), local schemes
  - Rails (halal-neutral): SWIFT, SEPA, UPI/NPCI, instant-payment systems
  - Processors with Islamic product configs (M2P, Marqeta)

#### [Payment Order](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-payment-order)

`isb-payment-order` · namespace `isb-operations` · gateway path `/isb-payment-order`

Shariah-compliant **Process** service domain on the **Payment Order Procedure** control record — the system of record for *Payment Order* within Islamic Cards and Payments.

- **Banking type:** Islamic retail payments & cards (fee-based, riba-free)
- **Typical use cases:**
  1. Issue and service Payment Order products on fee (Ujrah) structures — no revolving interest
  2. Validate, route, and execute payment instructions with debit/credit atomicity
  3. Charge late amounts to charity pools per Shariah board rulings
- **Integrates with (typical backend providers):**
  - Networks: Visa/Mastercard (Ujrah/fee-based card programs), local schemes
  - Rails (halal-neutral): SWIFT, SEPA, UPI/NPCI, instant-payment systems
  - Processors with Islamic product configs (M2P, Marqeta)

#### [Payment Execution](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-payment-execution)

`isb-payment-execution` · namespace `isb-operations` · gateway path `/isb-payment-execution`

Shariah-compliant **Process** service domain on the **Payment Transaction Procedure** control record — the system of record for *Payment Transaction* within Islamic Cards and Payments.

- **Banking type:** Islamic retail payments & cards (fee-based, riba-free)
- **Typical use cases:**
  1. Issue and service Payment Transaction products on fee (Ujrah) structures — no revolving interest
  2. Validate, route, and execute payment instructions with debit/credit atomicity
  3. Charge late amounts to charity pools per Shariah board rulings
- **Integrates with (typical backend providers):**
  - Networks: Visa/Mastercard (Ujrah/fee-based card programs), local schemes
  - Rails (halal-neutral): SWIFT, SEPA, UPI/NPCI, instant-payment systems
  - Processors with Islamic product configs (M2P, Marqeta)


### Shared Operations

*Universal Islamic banking operations & compliance.*

#### [Customer Reference Data](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-customer-reference-data)

`isb-customer-reference-data` · namespace `isb-operations` · gateway path `/isb-customer-reference-data`

Shariah-compliant **Maintain** service domain on the **Customer Reference Data Maintenance Agreement** control record — the system of record for *Customer Reference Data* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain Customer Reference Data records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks

#### [KYC And Shariah Screening](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-kyc-and-shariah-screening)

`isb-kyc-and-shariah-screening` · namespace `isb-operations` · gateway path `/isb-kyc-and-shariah-screening`

Shariah-compliant **Process** service domain on the **KYC Shariah Assessment Procedure** control record — the system of record for *KYC Shariah Assessment* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain KYC Shariah Assessment records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks

#### [Financial Crime Monitoring](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-financial-crime-monitoring)

`isb-financial-crime-monitoring` · namespace `isb-operations` · gateway path `/isb-financial-crime-monitoring`

Shariah-compliant **Monitor** service domain on the **Financial Crime Alert Monitoring State** control record — the system of record for *Financial Crime Alert* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain Financial Crime Alert records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks

#### [AAOIFI Financial Accounting](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-aaoifi-financial-accounting)

`isb-aaoifi-financial-accounting` · namespace `isb-operations` · gateway path `/isb-aaoifi-financial-accounting`

Shariah-compliant **Process** service domain on the **AAOIFI Ledger Posting Procedure** control record — the system of record for *AAOIFI Ledger Posting* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain AAOIFI Ledger Posting records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks

#### [IFSB Regulatory Reporting](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-ifsb-regulatory-reporting)

`isb-ifsb-regulatory-reporting` · namespace `isb-operations` · gateway path `/isb-ifsb-regulatory-reporting`

Shariah-compliant **Process** service domain on the **IFSB Regulatory Report Procedure** control record — the system of record for *IFSB Regulatory Report* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain IFSB Regulatory Report records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks

#### [Branch And Digital Channel Operation](https://github.com/Sreenivas-Sadhu-Prabhakara/isb-branch-and-digital-channel-operation)

`isb-branch-and-digital-channel-operation` · namespace `isb-operations` · gateway path `/isb-branch-and-digital-channel-operation`

Shariah-compliant **Operate** service domain on the **Channel Session Operating Session** control record — the system of record for *Channel Session* within Shared Operations.

- **Banking type:** Universal Islamic banking operations & compliance
- **Typical use cases:**
  1. Maintain Channel Session records consistently across the Islamic estate
  2. Combine conventional KYC/AML with Shariah-specific screening at onboarding
  3. Produce AAOIFI-basis financials and IFSB regulatory returns
  4. Operate branch/digital channels with products labeled by underlying contract
- **Integrates with (typical backend providers):**
  - AML/screening: NICE Actimize, World-Check (plus Shariah screening data)
  - Accounting: AAOIFI FAS-aligned GL mappings on SAP/Oracle
  - Regulators: IFSB-aligned returns; national central banks


---

*Generated from `islamic-banking-services/registry.json` by `scripts/generate-master-catalog.py`. Educational reference implementation — actual Shariah compliance of any deployment requires certification by a qualified Shariah Supervisory Board.*
