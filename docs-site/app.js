/* Islamic Banking Platform docs — interactivity. Vanilla JS; data from data.js. */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const ghRepo = (r) => `https://github.com/${GH_OWNER}/${r}`;
  const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");

  /* ── 01 principles ──────────────────────────────────────────── */
  const PRIN = {
    riba: `<b>Where it lives in the code:</b> there is no interest field anywhere in this landscape.
      Savings return real pool profit via <a href="${ghRepo("isb-profit-calculation-and-distribution")}" target="_blank" rel="noopener">isb-profit-calculation-and-distribution</a>;
      financing earns a <em>fixed, disclosed markup</em> on a genuine sale (<a href="${ghRepo("isb-murabaha-financing")}" target="_blank" rel="noopener">isb-murabaha-financing</a>) or rental on an owned asset (Ijara).
      Late payments route to <a href="${ghRepo("isb-late-payment-charity-handling")}" target="_blank" rel="noopener">charity</a> — penalising delay may not enrich the bank.`,
    gharar: `<b>Where it lives in the code:</b> every financing contract names its asset. Murabaha records the bank's
      purchase before the onward sale (<a href="${ghRepo("isb-asset-acquisition-agency")}" target="_blank" rel="noopener">isb-asset-acquisition-agency</a> evidences possession);
      Salam and Istisna (<a href="${ghRepo("isb-salam-commodity-forward")}" target="_blank" rel="noopener">forward</a> / <a href="${ghRepo("isb-istisna-construction-financing")}" target="_blank" rel="noopener">construction</a>) fix specification, price, and delivery up front — the permitted exceptions, precisely because they are fully specified.`,
    risk: `<b>Where it lives in the code:</b> Mudarabah account holders share pool profit by weighted balances and bear losses by capital
      (<a href="${ghRepo("isb-mudarabah-savings-account")}" target="_blank" rel="noopener">isb-mudarabah-savings-account</a>); reserves smooth returns transparently
      (<a href="${ghRepo("isb-profit-equalization-reserve")}" target="_blank" rel="noopener">PER</a> / <a href="${ghRepo("isb-investment-risk-reserve")}" target="_blank" rel="noopener">IRR</a>).
      Musharakah splits outcomes by agreed ratios (<a href="${ghRepo("isb-musharakah-partnership-financing")}" target="_blank" rel="noopener">isb-musharakah-partnership-financing</a>). Takaful pools risk mutually
      (<a href="${ghRepo("isb-takaful-policy-administration")}" target="_blank" rel="noopener">isb-takaful-policy-administration</a>).`,
    halal: `<b>Where it lives in the code:</b> a whole governance area: the Shariah board directory, fatwa repository,
      <a href="${ghRepo("isb-shariah-compliance-review")}" target="_blank" rel="noopener">compliance review</a> and <a href="${ghRepo("isb-shariah-audit")}" target="_blank" rel="noopener">audit</a>,
      <a href="${ghRepo("isb-halal-equity-screening")}" target="_blank" rel="noopener">equity screening</a>,
      <a href="${ghRepo("isb-income-purification")}" target="_blank" rel="noopener">income purification</a>, and
      <a href="${ghRepo("isb-zakat-calculation")}" target="_blank" rel="noopener">Zakat</a> calculation/distribution.`,
  };
  const prinDetail = $("#prin-detail");
  document.querySelectorAll(".prin").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".prin").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      prinDetail.innerHTML = PRIN[b.dataset.p];
    });
  });
  document.querySelector('.prin[data-p="riba"]').click();

  /* ── 02 conventional → islamic mapper ───────────────────────── */
  const MAP = [
    { from: "Personal loan", to: "Tawarruq (commodity Murabaha)", repo: "isb-commodity-murabaha-tawarruq",
      how: "The bank buys a commodity, sells it to you at deferred cost-plus, you sell it spot for cash.",
      diff: ["Cash raised through real trades with real commodities (e.g. via Bursa Suq Al-Sila')",
             "Your obligation is a fixed sale price — it can never compound",
             "Late payment charges go to charity, not bank income"] },
    { from: "Home loan / mortgage", to: "Diminishing Musharakah", repo: "isb-diminishing-musharakah-home-finance",
      how: "Bank and customer co-own the home; you buy the bank's share unit-by-unit while paying rent on the part you don't yet own.",
      diff: ["Co-ownership, not creditor/debtor: the bank actually owns its share",
             "Your monthly payment = rent (on bank's share) + unit purchase — rent falls as ownership grows",
             "Ownership costs (structural takaful etc.) follow the owners proportionally"] },
    { from: "Car / equipment loan", to: "Murabaha (cost-plus sale)", repo: "isb-murabaha-financing",
      how: "The bank purchases the asset, then sells it to you at disclosed cost + markup, payable in installments.",
      diff: ["The bank must genuinely own the asset before selling it (possession evidenced)",
             "Markup is disclosed and FIXED at contract — never recalculated like interest",
             "Default cannot inflate the debt; recovery is of the agreed price only"] },
    { from: "Savings account (interest)", to: "Mudarabah savings", repo: "isb-mudarabah-savings-account",
      how: "Your deposits join an investment pool the bank manages as Mudarib; you receive a share of actual profit.",
      diff: ["Returns vary with real pool performance — nothing is promised in advance",
             "The bank earns only its pre-agreed Mudarib share of profit",
             "Losses (absent negligence) are borne by capital — that's the deal that makes profit lawful"] },
    { from: "Fixed deposit", to: "Mudarabah term investment", repo: "isb-mudarabah-term-investment-account",
      how: "A term-bound investment in the profit pool, with higher weighting for longer commitments.",
      diff: ["'Expected profit rate' is indicative, settled by actual results",
             "Weightings (not promised rates) reward tenor",
             "Profit Equalization Reserve smooths volatility — with disclosure"] },
    { from: "Credit card", to: "Ujrah (fee-based) card", repo: "isb-ujrah-card-services",
      how: "Card services priced as fixed fees for defined services — never revolving interest on balances.",
      diff: ["No APR: fees are flat, service-linked, and known in advance",
             "Late amounts go to the charity pool",
             "Cash-advance-style features are structured as separate Tawarruq if offered at all"] },
    { from: "Insurance", to: "Takaful (mutual protection)", repo: "isb-takaful-policy-administration",
      how: "Participants contribute to a mutual pool; claims are paid from the pool; the operator earns a Wakala fee.",
      diff: ["Risk is shared among participants, not transferred to a profit-taking insurer",
             "Underwriting surplus belongs to the pool and can return to participants",
             "Pool investments are themselves Shariah-screened"] },
    { from: "Bond", to: "Sukuk (certificates over assets)", repo: "isb-sukuk-issuance",
      how: "Certificates conferring beneficial ownership in income-generating assets or ventures — returns from the assets, not interest.",
      diff: ["Holders own a share of something real; returns track its performance",
             "Tradability rules depend on the underlying (receivables vs assets)",
             "Structures (Ijara/Wakala/Murabaha sukuk) carry SSB sign-off"] },
    { from: "Interbank lending", to: "Interbank commodity Murabaha", repo: "isb-interbank-commodity-murabaha-desk",
      how: "Banks place liquidity with each other through short-tenor commodity cost-plus trades.",
      diff: ["Every placement is a real trade with settlement of a commodity leg",
             "Return is a sale markup, fixed at trade time",
             "Documented under IIFM master agreements"] },
  ];
  const mb = $("#mapper-buttons"), mo = $("#mapper-out");
  MAP.forEach((m, i) => {
    const b = document.createElement("button");
    b.className = "mapbtn"; b.textContent = m.from;
    b.addEventListener("click", () => {
      mb.querySelectorAll(".mapbtn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      mo.innerHTML = `
        <p class="map-arrow"><span class="from">${m.from}</span> &nbsp;⇢&nbsp; <span class="to">${m.to}</span></p>
        <h4>How it works</h4><p>${m.how}</p>
        <h4>What's actually different</h4>
        <ul>${m.diff.map((d) => `<li>${d}</li>`).join("")}</ul>
        <p class="map-repo">implemented by <a href="${ghRepo(m.repo)}" target="_blank" rel="noopener">${m.repo} ↗</a></p>`;
    });
    mb.appendChild(b);
  });
  mb.firstChild.click();

  /* ── 03 explorer ────────────────────────────────────────────── */
  const exBody = $("#ex-body"), exCount = $("#ex-count");
  const exSearch = $("#ex-search"), exArea = $("#ex-area");
  [...new Set(REGISTRY.map((s) => s.businessArea))].forEach((a) =>
    exArea.insertAdjacentHTML("beforeend", `<option>${a}</option>`));
  function renderExplorer() {
    const q = exSearch.value.trim().toLowerCase();
    const rows = REGISTRY.filter((s) =>
      (!q || (s.serviceDomain + s.repo + s.controlRecord + s.businessDomain).toLowerCase().includes(q)) &&
      (!exArea.value || s.businessArea === exArea.value));
    exCount.textContent = `${rows.length} of ${REGISTRY.length} service domains`;
    exBody.innerHTML = rows.map((s) => `
      <tr>
        <td><span class="sd-name">${s.serviceDomain}</span></td>
        <td class="dim">${s.businessArea}<br/>${s.businessDomain}</td>
        <td class="dim">${s.functionalPattern}</td>
        <td class="dim">${s.controlRecord}</td>
        <td><a class="repo-link" href="${ghRepo(s.repo)}" target="_blank" rel="noopener">${s.repo} ↗</a></td>
      </tr>`).join("");
  }
  exSearch.addEventListener("input", renderExplorer);
  exArea.addEventListener("change", renderExplorer);
  renderExplorer();

  /* ── 04 calculators ─────────────────────────────────────────── */
  function num(id) { return Math.max(0, Number($(id).value) || 0); }

  // Mudarabah
  function mudarabah() {
    const profit = num("#md-profit"), pool = num("#md-pool"),
          bal = num("#md-bal"), share = Math.min(100, num("#md-share"));
    const distributable = profit * (1 - share / 100);
    const yours = pool > 0 ? distributable * (bal / pool) : 0;
    const annualized = bal > 0 ? (yours * 12 / bal) * 100 : 0;
    $("#md-out").innerHTML =
      `<span>your profit share this month</span><span class="big">${inr(yours)}</span>` +
      `<div class="row"><span>pool profit</span><b>${inr(profit)}</b></div>` +
      `<div class="row"><span>Mudarib (bank) share ${share}%</span><b>− ${inr(profit * share / 100)}</b></div>` +
      `<div class="row"><span>distributed to account holders</span><b>${inr(distributable)}</b></div>` +
      `<div class="row"><span>your weight in pool</span><b>${pool > 0 ? ((bal / pool) * 100).toFixed(4) : 0}%</b></div>` +
      `<div class="row"><span>indicative annualized</span><b>${annualized.toFixed(2)}%</b></div>` +
      `<p class="note">If the pool earned nothing, you earn nothing — and losses fall on capital. That risk-sharing is what makes the profit lawful.</p>`;
  }
  ["#md-profit", "#md-pool", "#md-bal", "#md-share"].forEach((id) =>
    $(id).addEventListener("input", mudarabah));
  mudarabah();

  // Murabaha
  function murabaha() {
    const cost = num("#mu-cost"), markup = num("#mu-markup"), months = Math.max(1, num("#mu-months"));
    const total = cost * (1 + markup / 100);
    $("#mu-out").innerHTML =
      `<span>monthly installment</span><span class="big">${inr(total / months)}</span>` +
      `<div class="row"><span>asset cost (bank pays seller)</span><b>${inr(cost)}</b></div>` +
      `<div class="row"><span>disclosed markup ${markup}%</span><b>${inr(total - cost)}</b></div>` +
      `<div class="row"><span>total sale price — fixed at contract</span><b>${inr(total)}</b></div>` +
      `<div class="row"><span>tenor</span><b>${months} months</b></div>` +
      `<p class="note">The price never changes after signing: early settlement may earn a discretionary rebate; late payment adds nothing to the bank — it goes to charity.</p>`;
  }
  ["#mu-cost", "#mu-markup", "#mu-months"].forEach((id) =>
    $(id).addEventListener("input", murabaha));
  murabaha();

  // Zakat
  function zakat() {
    const assets = num("#zk-assets"), liab = num("#zk-liab"), gold = num("#zk-gold");
    const net = Math.max(0, assets - liab);
    const nisab = 85 * gold;
    const due = net >= nisab ? net * 0.025 : 0;
    $("#zk-out").innerHTML =
      `<span>zakat due</span><span class="big">${inr(due)}</span>` +
      `<div class="row"><span>zakatable net wealth</span><b>${inr(net)}</b></div>` +
      `<div class="row"><span>nisab (85g gold)</span><b>${inr(nisab)}</b></div>` +
      `<div class="row"><span>above nisab?</span><b>${net >= nisab ? "yes — 2.5% applies" : "no — nothing due"}</b></div>` +
      `<p class="note">Computed by isb-zakat-calculation; isb-zakat-distribution routes it to eligible recipient categories.</p>`;
  }
  ["#zk-assets", "#zk-liab", "#zk-gold"].forEach((id) =>
    $(id).addEventListener("input", zakat));
  zakat();

  /* copy buttons */
  document.querySelectorAll("pre[data-copy]").forEach((pre) => {
    const b = document.createElement("button");
    b.className = "copy-btn"; b.textContent = "copy";
    b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(pre.querySelector("code").innerText); } catch (e) {}
      b.textContent = "copied"; setTimeout(() => (b.textContent = "copy"), 1200);
    });
    pre.appendChild(b);
  });
})();
