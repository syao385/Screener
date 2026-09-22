# Institutional Earnings Intelligence Engine (EIE) Architecture

**Document Version**: `4.0.0` (Living Institutional Document)  
**Last Updated**: `2026-09-13`  
**Classification**: Wall Street Quant & Fundamental Research Infrastructure

---

## 1. Executive Summary & Version Changelog

| Version | Date | Key Architectural Additions | Author |
|---|---|---|---|
| **v1.0.0** | 2026-08-26 | Initial research & critique of `ai-berkshire` single/multi-agent skills. Identified retail bias and execution latency gaps. | Senior Quant PM |
| **v2.0.0** | 2026-08-26 | Complete institutional deployment: DuckDB local OLAP lake (`data/earnings_lake.duckdb`), Dual-Speed Engine (T+0 Flash SUE + T+1 4-Master Team), Multi-Session Playbooks (AH, BMO, Day 1-5 PEAD), Thesis Divergence handlers, and 5th dedicated HTML Dashboard view. | Senior Quant PM |
| **v3.0.0** | 2026-09-02 | **Universal 4-Horizon Consensus & Forward Guidance Architecture**: Permanent resolution of consensus estimates across Upcoming ($t>0$), Day 0 Flash ($t=0$), Recent PEAD Window ($t\in[1,45\text{d}]$, e.g. DELL, NVDA), and Historical ($t>45\text{d}$). Eliminated rolled-forward aggregator contamination, decoupled QoQ growth from consensus beats, and unified 5-column modal UI. | Senior Quant PM |
| **v3.1.0** | 2026-09-04 | **Phase 4 Attribution Lake Decoupling & Skill 08 Integration**: Separated analytical DuckDB lake (`data/attribution_lake.duckdb`) from earnings storage (`data/earnings_lake.duckdb`) to allow lock-free concurrent execution. Ingested PEAD surprise factors into parameter auto-tuning engine. | Senior Quant PM |
| **v3.2.0** | 2026-09-10 | **Active Release Staleness Invalidation & Multi-Session Parity (AVAV, Yesterday AMC)**: Expanded dynamic auto-enrichment and cache invalidation in `html_generator.py` to include `yesterday_amc` alongside `today_bmo`/`today_amc`. Injected explicit ISO `date` propagation in `earnings_calendar.py`, prioritized active calendar release date over stale prior quarter filings in `earnings_intelligence.py`, and eliminated restrictive ticker whitelists in `defeatbeta_client.py` for sub-5d releases. | Senior Quant PM |
| **v4.0.0** | 2026-09-13 | **Phase 7 Deep Research & Zero-Redundancy Forensic Caching**: Deployed Step 10 Institutional Company Deep Research Dossier & Forensics (`/deep-research`). Integrated Reverse DCF bisection valuation, Joseph Piotroski 9-point F-Score, Messod Beneish 8-variable $M$-Score manipulation filter ($M \le -1.78$), 15% random sample SEC EDGAR audit gate, and client-side on-the-fly live generation button (`⚡ Populate Deep Research Live`). Enforced zero-redundancy caching protocol to prevent remote network scraping during routine 60-second loops. | Senior Quant PM |
| **v5.0.0** | 2026-09-22 | **Phase 9-11 Institutional v2.0 Release**: Fully synthesized the Buffett 6-Gate Pre-Purchase Verification Audit and 4-Master Consensus Desk. Corrected Beneish M-Score formula (AQI non-current asset standard, SGI hyper-growth cap) and Sloan Accrual 4-quarter rolling window. Instituted multi-signal confluence requirement for fatal hard vetoes ($0.0\times$) vs gray-zone warnings ($0.5\times$). Replaced synthetic fallback balance sheets with clean `⚪ PENDING AUDIT (NO DATA)` status. Integrated hands-off background daemon (`run_hands_off_earnings_daemon.py`). | Senior Quant PM |


---

## 2. High-Level System Topology

```
                                  UNIFIED SYSTEM TOPOLOGY
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION & OLAP STORAGE                                                      │
│    • DefeatBeta API (DuckDB via HuggingFace Parquet) -> 0 Rate Limit, Sub-5ms Query    │
│    • Direct SEC EDGAR 8-K/10-Q Feeds -> Sub-15s Breaking Press Release Extraction     │
│    • Local Persistent DuckDB Store: data/earnings_lake.duckdb                          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. DUAL-SPEED ANALYTICS ENGINE (sources/earnings_intelligence.py)                     │
│    ┌─────────────────────────────────────────┬───────────────────────────────────────┐ │
│    │ OPTION A: Fast Flash Engine (< 5s)      │ OPTION B: Deep 4-Master Team          │ │
│    │ • SUE (Standardized Unexpected Earnings)│ • Duan Yongping: Moat & Pricing Power │ │
│    │ • Sloan Accrual Anomaly (< 6.0% clean)  │ • Buffett/Sloan: Forensic Cash Audit  │ │
│    │ • Guidance vs Consensus Revision Delta  │ • Munger: Competitive Inversion       │ │
│    │ • FCF Conversion Efficiency (> 100%)    │ • Li Lu: Tone NLP & Deception Hunter  │ │
│    │ • Immediate Active Playbook Generator   │ • Lead Quant PM: 0-100 Quality Score  │ │
│    └─────────────────────────────────────────┴───────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. MULTI-SESSION EXECUTION PLAYBOOKS & DIVERGENCE HANDLING                             │
│    • Playbook 0A (AH Immediate): 16:00-17:00 EST After-Hours Reaction & Post-Call Hold │
│    • Playbook 0B (BMO Immediate): 04:00-09:15 EST Premarket RVOL & Opening Auction     │
│    • Playbook 1 (Day-1 Gap & Go): 09:30-10:30 EST 5-min VWAP Hold, 1.5x ATR Stops      │
│    • Playbook 2 (Day 1-5 PEAD Swing): 10-30 Day Drift Accumulation on Pullbacks        │
│    • Playbook 3A (Trap Beat): Triple Beat + Price Dump -> Panic Fade vs Accrual Trap   │
│    • Playbook 3B (Kitchen Sink): Double Miss + Price Rip -> Short Squeeze Scalp        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. PORTFOLIO & DASHBOARD INTEGRATION                                                  │
│    • Screener View: Universal ⚡ Flash SUE Badges & SUE column                         │
│    • Trade Desk (Actions): Pre-computed intraday & swing execution cards                │
│    • Portfolio Manager: 48-Hour Earnings Exposure Radar & Health Scorecard             │
│    • Dedicated 5th View: 🏢 Earnings Intelligence & 4-Master Desk                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mathematical Factor Formulations

### 3.1 Standardized Unexpected Earnings (SUE)
$$SUE = \frac{EPS_{\text{actual}} - EPS_{\text{consensus}}}{\max\left(0.04, |EPS_{\text{consensus}}| \times 0.15\right)}$$
- $SUE \ge +1.5\sigma$: **Extreme Bull Surprise**
- $-0.5\sigma < SUE < +0.5\sigma$: **In-Line**
- $SUE \le -1.5\sigma$: **Severe Miss**

### 3.2 Sloan Accrual Anomaly Ratio
$$Sloan = \frac{\text{Net Income} - \text{Operating Cash Flow}}{\text{Total Assets}} \times 100$$
- $Sloan \le +4.0\%$: **🟢 Clean Cash Earnings (High Quality)**
- $4.0\% < Sloan \le 8.0\%$: **🟡 Moderate Accrual Caution**
- $Sloan > +8.0\%$: **🔴 High Accrual Distortion (Red Flag: Aggressive Revenue Recognition)**

### 3.3 Free Cash Flow (FCF) Conversion
$$FCF_{\text{conversion}} = \frac{\text{Operating Cash Flow} - \text{Capex}}{\text{Net Income}} \times 100$$
- Target: $\ge 100\%$ indicates superior earnings quality.

### 3.4 Universal 4-Horizon Consensus Resolution Architecture
To prevent forward-quarter aggregator roll contamination (where `t.calendar` shifts forward to the next quarter immediately post-market), consensus estimates are deterministically resolved across 4 discrete timing horizons:

1. **Horizon 1 — Upcoming Pre-Earnings ($t > 0$, Future)**:
   - Target date is in the future.
   - `est_eps` and `est_rev` represent Wall Street expectations for the upcoming release (`cal["Revenue Average"]` or `re_df["0q"]`).
   - Reported columns display `— (Upcoming MM-DD [Session])`.

2. **Horizon 2 — Day 0 / Active Flash ($t = 0$, Released Today AMC/BMO)**:
   - Reported numbers are anchored to actual released statements.
   - Consensus EPS is resolved from `earnings_dates` matching today's date.
   - Consensus revenue is matched from pre-earnings baseline or derived via reported surprise: $\text{est\_rev} = \frac{\text{actual\_rev}}{1 + \frac{\text{rev\_surprise\_pct}}{100}}$.
   - Rolled-forward calendar estimates (`cal["Revenue Average"]`) are isolated strictly to `next_q_est_rev` (Forward Guidance Target).

3. **Horizon 3 — Recent PEAD Window ($t \in [1, 45\text{ days}]$, Active Drift Window, e.g. DELL, NVDA)**:
   - Company reported within the last 45 trading days; aggregators have rolled forward to $t+1$.
   - **Strict Isolation Rule**: `cal["Revenue Average"]` and `cal["Earnings Average"]` represent the forward $t+1$ target and are **strictly barred** from setting current quarter consensus.
   - Consensus EPS is read from the immutable `past_rep` ledger row on the release date.
   - Consensus revenue is derived from the pre-earnings baseline or implied from the EPS beat proportion, eliminating artificial revenue misses (e.g. DELL reported \$46.97B vs consensus \$45.03B, +4.3% beat).

4. **Horizon 4 — Historical Closed Quarters ($t > 45\text{ days}$)**:
   - Immutable SEC 10-Q/10-K statements retrieved from local DuckDB lake.
   - Multi-quarter tables render 6–8 authentic historical quarters with exact filing and announcement dates.

### 3.5 Forward Guidance 3-Tier Formulation & Decision Tree
$$\text{Guidance Revision \%} = \frac{\text{Management Guidance Midpoint} - \text{Prior Next-Q Consensus}}{\text{Prior Next-Q Consensus}} \times 100\%$$

- **Tier 1 (Explicit Management Guidance)**: Midpoint from press release text / 8-K compared against `next_q_est_rev`.
- **Tier 2 (Consensus Analyst Revisions)**: Post-market delta in `+1q` forward models.
- **Tier 3 (Clean Double-Beat Proportional Raise)**:
  $$\text{Guidance Midpoint} = \text{Consensus} \times \left(1.0 + \min\left(\frac{\text{Actual Rev} - \text{Est Rev}}{\text{Est Rev}} \times 0.65,\; 3.5\%\right)\right)$$
- If the company missed or was in-line, guidance defaults to `Affirmed / In-line (0.0%)`.

---

## 4. Multi-Session Trading Playbooks

```
                                  PLAYBOOK EXECUTION MATRIX
┌──────────────┬──────────────────┬───────────────────────┬────────────────────────────┐
│ Playbook ID  │ Name             │ Trigger Window        │ Entry & Risk Management    │
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 0A  │ AH Breaking      │ 16:00 - 17:00 EST     │ Long when breaking AH VWAP │
│              │ Reaction         │ (Post-Release)        │ with stop at AH Low.       │
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 0B  │ BMO Premarket    │ 04:00 - 09:15 EST     │ Premarket RVOL > 2.0x,     │
│              │ Imbalance        │ (Premarket)           │ enter above premarket mid. │
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 1   │ Day-1 Gap & Go   │ 09:30 - 10:30 EST     │ 5-min VWAP hold, RVOL>2.5x,│
│              │ Momentum         │ (Regular Hours)       │ 1.5x ATR trailing stop.    │
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 2   │ Day 1-5 PEAD     │ Days 1 - 5 Post-ER    │ Buy 20-EMA / VWAP pullback;│
│              │ Drift Swing      │ (Multi-Day Swing)     │ hold 10-30 days.           │
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 3A  │ Trap Beat        │ Post-Earnings Panic   │ If Sloan clean: Buy D1/D2  │
│              │ Divergence       │ (Gap Down on Beat)    │ 15-min reversal double bot.│
├──────────────┼──────────────────┼───────────────────────┼────────────────────────────┤
│ Playbook 3B  │ Kitchen Sink     │ Short Squeeze         │ Scalp morning surge only;  │
│              │ Divergence       │ (Gap Up on Miss)      │ avoid multi-week hold.     │
└──────────────┴──────────────────┴───────────────────────┴────────────────────────────┘
```

---

## 5. Slash Commands & Skill Usage

### 5.1 Single-Ticker Forensic Audit (`/earnings-review`)
- **Syntax**: `/earnings-review TICKER [QUARTER]`
- **Example**: `/earnings-review NVDA` or `/earnings-review AAPL 2026Q1`
- **Output**: Fast quantitative factor scorecard, Sloan accrual audit, and immediate trade desk playbook.

### 5.2 Collaborative 4-Master Team (`/earnings-team`)
- **Syntax**: `/earnings-team TICKER [QUARTER]`
- **Example**: `/earnings-team TSLA 最新`
- **Output**: Comprehensive 4-master deep audit (*Duan Yongping*, *Buffett & Sloan*, *Charlie Munger*, *Li Lu*) synthesized by Lead Quant PM into 0-100 Fundamental Quality Score.

### 5.3 Institutional Company Deep Research (`/deep-research`)
- **Syntax**: `/deep-research TICKER` (alias `/company-research TICKER`)
- **Example**: `/deep-research NVDA`
- **Output**: Full institutional company deep research dossier:
  - 4-Master dialectical synthesis with Munger hard veto on accounting anomalies.
  - Piotroski 9-point F-Score and Messod Beneish 8-variable $M$-Score.
  - Reverse DCF bisection solver calculating market-implied growth, Base Fair Value, Conviction Buy Target (15% margin of safety), and Invalidation Hard Stop.
  - 15% random sample SEC EDGAR statement audit gate.
  - Dual persistence in DuckDB `deep_research_theses` and `data/deep_research/{SYMBOL}.json`.

---

## 6. Maintenance & Data Integrity Rules
1. **Never scrape raw HTML when DuckDB lake Parquet is available.**
2. **Always cross-validate EPS and Revenue deltas against reported SEC 10-Q/8-K exhibits.**
3. **If Sloan Accrual $>+8\%$, automatically downgrade PEAD conviction regardless of headline EPS beat.**
4. **Strict Zero-Redundancy Fundamental Caching**: Never query remote financial APIs during routine 60-second screener loops unless an earnings release is actively breaking (`yesterday_amc`, `today_bmo`, `today_amc`) or explicit `--force-refresh` is passed.

