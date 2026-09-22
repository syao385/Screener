# Institutional Market Intelligence Platform Rules & Standards

## Living Document Governance
This document defines the immutable architectural and operational standards for the Institutional Real-Time Intelligence Platform. All code modifications, screener algorithms, and documentation must adhere to these rules.

---

## 1. Zero Fake / Static Data Rule (Core Axiom)
- **Mandate**: Every single metric, price, rating, option level, economic release, and news catalyst MUST be fetched dynamically in real time from official public web feeds, APIs, or SEC filings.
- **Prohibition**: Hardcoded ticker watchlists, static mock dictionaries, dummy numbers, simulated quotes, or fake fallback data are strictly forbidden. If a source is temporarily unreachable, the system must employ automated fallback retry mechanisms or report `" — "` (unavailable).

---

## 2. Multi-Session Gatekeeping Protocol & Exact RVOL Anchor Times
The platform operates 24/7 across four distinct market sessions with deterministic anchor times:

| Session | Time Window (EST) | Price Breakout Requirement | RVOL Anchor Time |
|---|---|---|---|
| **Premarket** | 00:00 – 09:30 (Weekdays) | $\text{Price} > \text{Yesterday's High}$ | **Midnight – 00:00 AM EST** |
| **Regular Hours** | 09:30 – 16:30 (Weekdays) | $\text{Price} > \text{Yesterday's High}$ **AND** $\text{Price} \ge \text{Premarket High}$ | **09:30 AM EST** |
| **After-Hours** | 16:30 – 23:59:59 (Mon–Thu) | $\text{Price} \ge \text{Latest Business Day's High}$ | **04:30 PM EST (16:30 EST)** |
| **Weekend** | Friday 16:30 – Sunday 23:59:59 | $\text{Price} \ge \text{Latest Business Day's High}$ | **Friday 04:30 PM EST** |

### Mathematical Definition of RVOL at Time T
Relative Volume ($\text{RVOL}$) at any active time $T$ is strictly evaluated as:
$$\text{RVOL}(T) = \frac{\text{Cumulative Volume since Anchor Time up to } T}{\text{20-day Average of Cumulative Volume since Anchor Time up to } T}$$

1. **Premarket RVOL (Anchor: 00:00 AM Midnight EST)**:
   $$\text{RVOL}_{\text{pre}}(T) = \frac{\text{Cumulative Premarket Volume } [00:00 \to T]}{\mathbb{E}_{20\text{d}}\left[\text{Cumulative Premarket Volume } [00:00 \to T]\right]}$$
2. **Regular Hours RVOL (Anchor: 09:30 AM EST)**:
   $$\text{RVOL}_{\text{reg}}(T) = \frac{\text{Cumulative Regular Volume } [09:30 \to T]}{\mathbb{E}_{20\text{d}}\left[\text{Cumulative Regular Volume } [09:30 \to T]\right]}$$
3. **After-Hours RVOL (Anchor: 04:30 PM EST)**:
   $$\text{RVOL}_{\text{post}}(T) = \frac{\text{Cumulative After-Hours Volume } [16:30 \to T]}{\mathbb{E}_{20\text{d}}\left[\text{Cumulative After-Hours Volume } [16:30 \to T]\right]}$$
4. **Weekend RVOL (Anchor: Friday 04:30 PM EST)**:
   $$\text{RVOL}_{\text{weekend}}(T) = \frac{\text{Cumulative Friday Extended Volume } [16:30 \to 20:00]}{\mathbb{E}_{20\text{d}}\left[\text{Cumulative Extended Volume } [16:30 \to 20:00]\right]}$$

### Common Universal Filters (All Sessions)
1. **Market Cap**: $\ge \$1.0\text{B}$
2. **30-Day Average Volume**: $\ge 500,000$ shares
3. **Gap %** (% Change from Previous Close): $\ge +3.0\%$
4. **Session RVOL**: $\ge 1.50\text{x}$
5. **Catalyst Rating**: $\ge 2.0★$ AND `is_positive == True`

---

## 3. Catalyst Intelligence & Disqualification Standard
- **Rating Scale**:
  - `5.0★ [Earnings Beat / M&A Merger]`: Major blowout beats, raised guidance, cash buyout acquisitions.
  - `4.0★ [FDA Approval / Defense Contract]`: Clinical phase 3 approvals, multi-billion defense awards.
  - `3.0★ [Strategic Partnership / AI Product Launch]`: High-impact commercial agreements.
  - `2.5★ [Analyst Upgrade / Index Inclusion]`: Wall Street revisions and S&P/Russell inclusion.
  - `2.0★ [Sector Sympathy]`: Sector-wide tailwinds where the headline relates to the broader sector/industry rather than the specific ticker directly.
  - `< 2.0★ [Disqualified]`: Dilution, offerings, CFO resignations, accounting fraud, and revenue misses disqualify candidates from the dashboard.
- **Arbitration**: When multiple headlines exist for a ticker, the highest-rated catalyst is selected.
- **Display Format**: `[Category] ⭐⭐⭐⭐⭐ Headline`

---

## 4. Institutional 5-Star Setup Quality Index
Every qualified candidate is graded from **1.0★ to 5.0★** using statistical weighting:
1. **Catalyst Quality** ($0.0 - 1.5★$): Normalized score from news classifier.
2. **RVOL Strength** ($0.0 - 1.0★$): $\ge 3.0\text{x} \to 1.0★$; $\ge 2.0\text{x} \to 0.75★$; $\ge 1.5\text{x} \to 0.5★$.
3. **Technical Breakout** ($0.0 - 1.0★$): Clearance above yesterday high ($+0.4$), premarket high ($+0.3$), and gap magnitude ($+0.3$).
4. **Options Gamma Structure** ($0.0 - 0.75★$): Bullish skew ($+0.4$), Call wall headroom ($+0.2$), Put/Call ratio $< 0.7$ ($+0.15$).
5. **Macro Regime Alignment** ($0.0 - 0.75★$): Risk-On ($+0.75$), Neutral ($+0.45$), Risk-Off ($+0.15$).

---

## 5. Watchlist Presentation & Level Distance Standard
- All key price levels (**Call Wall**, **Put Wall**, **Gamma Flip**, **Yesterday's High**, **Premarket High**) MUST display both the absolute strike price and the percentage distance from current price:
  $$\text{Distance \%} = \frac{\text{Level} - \text{Current Price}}{\text{Current Price}} \times 100$$
  - Example: `Call Wall: $105.00 (+4.8%)` | `Put Wall: $92.00 (-8.2%)`
- **Interactive Sorting**: Every table column must support client-side ascending/descending sorting (`▲` / `▼`).

---

## 6. Living Cumulative Documentation & Specification Rule
Whenever features, formulas, or algorithms are added or modified:
6. **`docs/functional_spec.md`** MUST be updated cumulatively with widget-by-widget and field-by-field definitions, data sources, formats, and business rules.
7. **`docs/design_spec.md`** MUST be updated with complete architectural diagrams, quantitative mathematical formulas, decision flowcharts, and engine logic.
8. **`docs/implementation_plan.md`**, **`docs/walkthrough.md`**, and **`docs/data_verification_guide.md`** MUST be updated with updated Version History tables.
9. No obsolete or legacy scanner references (e.g. removed swing trading widget) are permitted to remain in active documentation.

---

## 7. Phase 4 Alpha Attribution & Parameter Auto-Tuning Standards
1. **Analytical Data Lake Segregation**: Trade logging and performance attribution must use dedicated analytical DuckDB storage (`data/attribution_lake.duckdb`), completely independent from fundamental scrapers to guarantee non-blocking concurrent execution.
2. **Hard Safety Clamping Protocol**: All automated parameter calibrations (setup conviction multipliers, risk weights) MUST be clamped strictly within $[0.50\text{x}, 1.35\text{x}]$ to prevent algorithm runaway or extreme leverage in high-volatility regimes.
3. **Toggleable Forward Fills Standard**: Forward incremental trade fills MUST default to **OFF** (`ENABLE_FORWARD_INCREMENTAL_FILLS = False`). The trader may toggle forward fills on/off or execute explicit manual overrides (`manual_override = True`).
4. **Brinson-Fachler Factor Decomposition (Skill 08)**: Active return decomposition must maintain exact mathematical symmetry ($R^P - R^B = \sum (A_i + S_i + I_i)$) across all 11 GICS sectors.

---

## 8. Phase 5 Paper Trading, Intraday Circuit Breakers & Stress Testing Standards
1. **Realistic Execution Modeling**: All paper trade fills in `sources/order_router.py` must account for bid-ask spreads ($0.03\%$) and execution slippage ($1-4\text{ bps}$) before updating balances in `data/paper_trading.duckdb`.
2. **Multi-Tiered Capital Preservation Circuit Breakers**:
   - **Level 1 Warning ($-1.0\%$)**: Ratchet Chandelier stops to tight $1.5\text{x}$ ATR, cap conviction multipliers to $\le 0.85\text{x}$.
   - **Level 2 De-Risk ($-2.0\%$)**: Hard clamp portfolio risk multiplier to $0.50\text{x}$, flag speculative Tier 3 trades for immediate partial trimming.
   - **Level 3 Kill-Switch ($-3.0\%$)**: Autonomous freeze of all new automated BUY executions, lock $100\%$ cash reserves, and dispatch critical emergency alerts.
3. **Historical Crisis Replay Integrity**: The stress testing engine must evaluate current portfolio sector beta weights against deterministic macro shocks across 6 canonical crises (COVID 2020, 2022 Rate Spike, 2008 GFC, 2024 Tech/Yen Shock, 2000 Dot-Com, 1987 Black Monday).
4. **Non-Blocking Broker Gateway**: Alpaca REST API client and Universal Webhook router must handle missing credentials gracefully without impeding offline paper simulation or throwing uncaught dashboard exceptions.

---

## 9. Zero Synthetic Fallback Ingestion Rule (Strict Data Integrity Axiom)
1. **No Dummy Balance Sheets**: When querying financial statements for a ticker (e.g. SEC EDGAR or DuckDB Fundamental Lake), if filings have not yet been ingested or are unavailable, the engine MUST NEVER substitute hardcoded synthetic numbers (e.g. dummy $10B revenue or $2B net income).
2. **Clean Status Reporting**: Unaudited stocks or tickers lacking SEC statements must cleanly output `⚪ PENDING AUDIT (NO DATA)` across all diagnostic portals and modals.
3. **Modal Fallback Integrity**: The HTML/JS modal must never default to an unearned `🟢 PASS (6/6 GATES)` or `1.0x` sizing for tickers awaiting audit data; it must display dedicated pending audit cards until quantitative filings are verified.

---

## 10. Buffett 6-Gate Pre-Purchase Audit & Forensic Accounting Confluence Rule
1. **Asset Quality Index (AQI) Calculation Integrity**:
   - $\text{AQI}$ measures the proportion of non-current assets other than property, plant, and equipment:
     $$\text{AQI} = 1 - \frac{\text{Current Assets} + \text{PP\&E}}{\text{Total Assets}}$$
   - Income statement items (e.g. Gross Profit) must NEVER be subtracted from balance sheet Total Assets.
2. **Hyper-Growth Bias Adjustment**:
   - To prevent penalizing legitimate hyper-growth tech innovators whose revenue expands rapidly ($> 100\%$ YoY), the Sales Growth Index ($\text{SGI}$) contribution ($0.892 \times \text{SGI}$) is capped at $1.25$ when Gross Margins are stable or expanding ($\text{GMI} \le 1.05$).
3. **Sloan Accrual Multi-Quarter Window**:
   - Sloan Accruals ($\frac{\text{Net Income} - \text{CFO}}{\text{Total Assets}}$) must be computed using the **4-quarter rolling mean** of quarterly accruals rather than a single quarter's working capital fluctuation, ensuring seasonal working capital timing spikes do not falsely trip red flags.
4. **Multi-Signal Confluence for Fatal Hard Veto**:
   - **Gray / Caution Zone ($M \in [-1.78, -1.49]$)**: Triggers `🟡 WARN / CAUTION` with $0.5\times$ position sizing and active working capital monitoring.
   - **Fatal Hard Veto ($0.0\times$ Sizing)**: Strictly requires **multi-signal confluence**:
     - Severe Beneish manipulation risk ($M > -1.49$) *conjoined* with elevated Sloan accruals ($> 8.0\%$) or balance sheet distress (Piotroski $F \le 3$), OR
     - Severe structural insolvency (Piotroski $F \le 2$).
     - A standalone borderline M-score or temporary working capital bump must never trigger an unconfirmed fatal 0.0x veto.

---

## 11. Multi-Session RVOL Absolute Anchoring & Ratio Standard
1. **Deterministic Session Anchor Times**:
   - **Premarket**: Anchor is **Midnight – 00:00 AM EST**.
   - **Regular Market Hours**: Anchor is **09:30 AM EST**.
   - **After-Hours**: Anchor is **04:30 PM EST (16:30 EST)**.
   - **Weekend**: Anchor is **Friday 04:30 PM EST**.
2. **Time-Matched Elapsed Volume Calculation**:
   - $\text{RVOL}(T)$ is strictly computed as the cumulative volume since the session anchor up to current time $T$, divided by the 20-day historical average of cumulative volume over that identical elapsed window:
     $$\text{RVOL}(T) = \frac{\text{CumVol}_{\text{anchor} \to T}}{\overline{\text{CumVol}}_{20\text{d}, \text{anchor} \to T}}$$
   - Extended-hours volume must NEVER be divided by full regular-session daily average volume.

---

## 12. Upstream Thematic Intelligence & Physical Chokepoint Arbitrage Rule
1. **Depth4 Causal Cascade Propagation**:
   - Every macro theme must map from D1 (Direct pure plays) $\to$ D2 (Critical component supply chain) $\to$ D3 (Foundational energy & grid infrastructure) $\to$ D4 (Tertiary real-economy enablers).
2. **4-Layer Durability Gate**:
   - Trend evaluation requires passing: (1) Technical Momentum, (2) CapEx Commitment ($\ge 20\%$ YoY growth), (3) Consensus Revision Velocity, and (4) Relative Strength.
3. **Physical Bottleneck Hunter Valuation Gate**:
   - Layer 2–3 physical supplier arbitrage candidates facing lead-time blowouts and capacity shortages must pass a strict valuation gate: **Price-to-Sales ($P/S$) $\le 30\times$**. Hyped companies exceeding $30\times P/S$ are disqualified from chokepoint arbitrage.
4. **Era Alpha Platform Compounding**:
   - Platform compounder selection requires sustainable Return on Invested Capital ($\text{ROIC} > 18\%$), high customer switching moats, and structural S-curve acceleration.

---

## 13. Autonomous 4-Session Cadence & Hands-Off Daemon Automation Rule
1. **Four Institutional Cadence Windows**:
   - **Premarket Session (08:00 – 09:15 EST)**: Overnight SEC filings, gap analysis, macro regime check, News Pulse stealth sentry.
   - **Opening Bell Execution (09:30 – 10:15 EST)**: 5-minute ORB breakouts, volume surges, Tier 1/2 execution queue.
   - **Mid-Day Monitoring (12:00 – 13:00 EST)**: VWAP hold/loss check, thesis drift evaluation, stealth flow surveillance.
   - **Postmarket Reconciliation (16:00 – 17:30 EST)**: Mark-to-market NAV, DuckDB lake commits, EOD 10-Q/K review, trailing stop updates.
2. **Hands-Off Execution**: Daemons running via Windows Task Scheduler must log heartbeats to `data/daemon_heartbeat.json` and persist non-blocking analytical state without manual intervention.
