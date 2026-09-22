---
name: earnings-review
description: Institutional Tier-2 Primary Source Earnings Forensic Audit & 4-Master Consensus Desk. Deep SEC 10-Q/8-K ingestion, rolling 8-quarter time-series & z-scores, forensic Sloan accrual audit, signal conflict resolution, 3-scenario DCF valuation, and PortfolioManager integration.
---

# Earnings Review & 4-Master Research Desk (Enhanced Unified Skill)

**Skill Type**: TIER 2 | Deep Fundamental Research & Quant Verification  
**Purpose**: Primary source read of actual SEC 10-Q/10-K filings, DuckDB fundamental lake, and earnings call transcripts. No sell-side summaries. Optional team mode enables 4-master parallel analysis with weighted consensus and divergence alerts.

## Modes & Invocation Syntax

Type in Antigravity Chat:
```text
/earnings-review TICKER [QUARTER] [mode=single|team]
```

- **Mode 1: Single-Analyst (Default)**: Rapid single-ticker forensic review, SUE calculation, 8Q historical trends, and trade desk action.
- **Mode 2: Team Mode (`mode=team` or `/earnings-team`)**: 4-Master parallel analysis (*Duan Yongping*, *Buffett & Sloan*, *Charlie Munger*, *Li Lu*) with weighted consensus scoring and divergence check.

### Examples:
- `/earnings-review NVDA` (Single forensic audit for latest reported quarter)
- `/earnings-review MRVL mode=team` (4-Master research desk debate for MRVL)
- `/earnings-team TSLA 2025Q4` (Direct team mode shortcut)

---

## ⚠️ PERMANENT RULES (Apply to ALL sections)

1. **Language**: All outputs MUST be in English.
2. **Time Zone**: All times are EST/EDT.
3. **Data Verification**: Every data point must include: `[value] + [source] + [timestamp]`.
4. **No Hallucinations / Inference**: Never guess price movements or fabricate missing line items. If a line item is unavailable, output `" — "` (unavailable).
5. **Deterministic Data Priority**: Always query local DuckDB Fundamental Lake (`data/earnings_lake.duckdb`) and Portfolio Manager first.

---

## Step 0: Portfolio Manager Integration & Deterministic Data Fetch

### 0.1 Ingest Active Portfolio State
Query active positions directly from the internal Portfolio Manager (no brittle CSV file scanning):
```python
from sources.portfolio_manager import portfolio_mgr
active_positions = portfolio_mgr.get_active_positions()
active_tickers = portfolio_mgr.get_active_equity_tickers()
```

### 0.2 Deterministic Fundamental Fetch Chain
Extract verified quarterly financial statements from local DuckDB columnar lake:
```python
from sources.defeatbeta_client import fundamental_engine
from sources.earnings_intelligence import earnings_intel

profile = fundamental_engine.get_historical_profile("$TICKER", fetch_remote=True)
flash = earnings_intel.analyze_flash_earnings("$TICKER", "$QUARTER")
```

---

## Step 1: Data Availability Rating

| Grade | Definition | Confidence Cap |
| :--- | :--- | :--- |
| **A** | Full SEC 10-Q/K filed + DuckDB statement lake + earnings call transcript | **High (Full Position Allocation)** |
| **B** | Press release + partial statements + call transcript | **Medium (50% Allocation)** |
| **C** | Third-party news summary only | **Low (Data Insufficient — DO NOT TRADE)** |

---

## Step 2: Core Financials (GAAP vs Non-GAAP & Forensic Cash Flow)

### 2.1 Income Statement & Guidance Delta
| Metric | Current Q | Prior Q | YoY Growth | QoQ Growth | Management Guidance | Beat / Miss |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Revenue** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | [GUIDANCE] | [SURPRISE%] |
| **Gross Profit** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | — | [GM%] |
| **Operating Income (GAAP)** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | — | [OM%] |
| **Operating Income (Non-GAAP)** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | — | [OM%] |
| **Net Income (GAAP)** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | — | [NM%] |
| **EPS (GAAP / Non-GAAP)** | [ACTUAL] | [PRIOR] | [YoY%] | [QoQ%] | [CONSENSUS] | [SUE σ] |

### 2.2 Forensic Accrual & Balance Sheet Safety Cushion
- **Sloan Accrual Anomaly Ratio**: $(Net Income - OCF) / Total Assets * 100%$ (<= 4.0% = Clean Cash-Backed, > 8.0% = Red-Flag Distortion)
- **Free Cash Flow Conversion**: $(FCF / Net Income) * 100%$ (Target > 85%)
- **Balance Sheet Net Cash Cushion**: Total Cash - Total Debt

---

## Step 3: Rolling 8-Quarter Time-Series & Z-Score Analysis

Calculates normalized dispersion across 8 quarters ($z = (Current - \mu_{8Q}) / \sigma_{8Q}$):

| Metric | Q-4 | Q-3 | Q-2 | Q-1 | Current | 8Q Avg (\mu) | 8Q StdDev (\sigma) | Trend | z-score* |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Revenue Growth (YoY)** | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [Accel / Decel] | **[+X.Xσ]** |
| **Gross Margin %** | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [Expanding / Contracting] | **[+X.Xσ]** |
| **Sloan Accrual %** | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [Cash-Backed / Accrual] | **[+X.Xσ]** |
| **FCF Conversion %** | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [Compounder / Weak] | **[+X.Xσ]** |

*\* $z > +1.5\sigma$: Strong Positive Breakout | $z < -1.5\sigma$: Severe Fundamental Deterioration*

---

## Step 4: Management Conference Call & Subtext Analysis

### 4.1 Linguistic Tone Check
| Signal Type | Search Keywords / Patterns | Frequency | Classification |
| :--- | :--- | :--- | :--- |
| **🟢 Candid** | "challenges", "headwinds we are addressing", "operational difficulties" | [#] | [Candid / Mixed / Defensive] |
| **🟢 Specific** | "we expect $X.X billion", "unit volume trajectory of X%" | [#] | [Specific / Vague] |
| **🔴 Vague** | "we believe in long term", "excited about future opportunities" | [#] | [Vague / Specific] |
| **🔴 Defensive** | "broader macroeconomic climate", "uncontrollable macro headwinds" | [#] | [Defensive / Candid] |

### 4.2 Q&A Friction Points & Prior Commitment Tracking
- **Analyst Inquiries & Management Delivery**: Key analyst friction topics and management responsiveness.
- **Prior Commitment Tracker**: Status of commitments made in prior quarters (`✅ Met` / `⚠️ Mixed` / `❌ Missed`).

---

## Step 5: Catalyst Quality Classification

| Catalyst Archetype | Fundamental Signature | Desk Action | Sizing Multiplier |
| :--- | :--- | :--- | :--- |
| **Clean Beat** | Revenue beat + EPS beat + Guidance raised + Sloan <= 4% | **✅ BUY (High Conviction)** | **1.0x (Full Sizing)** |
| **Mixed Beat** | EPS beat BUT revenue miss / segment margin contraction | **⚠️ REDUCE CONVICTION** | **0.5x (Half Sizing)** |
| **Headline Beat, Fundamental Miss** | EPS beat driven purely by tax/cost cuts, revenue missed, high Sloan accruals | **❌ DO NOT BUY / SHORT TRAP** | **0.0x (No Longs)** |
| **Miss** | Revenue miss + EPS miss + Guidance cut | **❌ DO NOT BUY / EXIT** | **Exit 100%** |

---

## Step 6: Signal Conflict Resolution Matrix

When headline metrics conflict, apply institutional priority weighting:

Final Signal = 0.40 * Guidance + 0.25 * Cash Flow + 0.20 * Revenue + 0.10 * EPS + 0.05 * Tone

| Signal A | Signal B | Conflict Nature | Resolution Protocol |
| :--- | :--- | :--- | :--- |
| **EPS Beat** | **Guidance Cut** | Conflicting | Guidance ALWAYS overrides EPS (forward-looking). Conviction downgraded. |
| **Revenue Beat** | **Margin Compression** | Conflicting | Evaluate price vs volume mix. Check whether growth is bought with discounts. |
| **High Cash Flow** | **Weak Guidance** | Conflicting | Cash flow is backward; guidance is forward. Weight guidance 40%. |
| **Management Optimism** | **Weak Segment Data** | Conflicting | Hard segment data overrides subjective executive tone. |

---

## Step 7: Three-Scenario Valuation & Margin of Safety

| Scenario | Growth Rate | Target P/E | Price Target | Implied Return | Probability Weight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Optimistic (Bull)** | [X.X]% | [XX]x | $[XXX] | +[XX]% | 25% |
| **Base Case** | [X.X]% | [XX]x | $[XXX] | +[XX]% | 50% |
| **Pessimistic (Bear)** | [X.X]% | [XX]x | $[XXX] | -[XX]% | 25% |

- **Weighted Fair Value**: $[XXX]
- **Current Market Price**: $[XXX]
- **Post-Earnings Margin of Safety**: [XX]%

---

## Step 8: 4-Master Consensus Desk (Mode 2 / Team Mode)

*Triggered when `mode=team` is specified or via `/earnings-team`.*

| Master | Analytical Focus | Institutional Metric Thresholds | Master Star Rating | Verdict | Weight |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Duan Yongping** | Business Moat & Pricing Power | Gross Margin $\ge 40\%$, Op Margin $\ge 15\%$, pricing power intact | **★★★★★ (1.0 to 5.0★)** | 🟢 Expanding Moat | **30%** |
| **Buffett & Sloan** | Forensic Cash Flow & Accruals | Sloan Accrual $\le 4\%$, FCF Conv $\ge 100\%$, Net Cash $> 0$ | **★★★★★ (1.0 to 5.0★)** | 🟢 Cash-Backed | **35%** |
| **Charlie Munger** | Inversion & Tech Disruption | 5-year competitive moat vs custom silicon, ROIC > WACC | **★★★★★ (1.0 to 5.0★)** | 🟢 Gaining Share | **20%** |
| **Li Lu** | Management Trust & Tone NLP | Candid tone, guidance delivered, SBC $\le 3\%$ rev | **★★★★★ (1.0 to 5.0★)** | 🟢 High Trust | **15%** |
| **Total 4-Master Consensus** | **Unified Fundamental Health** | **Score: 0 to 100 & Total Weighted Stars (out of 5.0★: Buffett 35%, Duan 30%, Munger 20%, Li Lu 15%)** | **★★★★☆ (X.X/5.0★)** | **🟢 Conviction BUY** | **100%** |

### Divergence Alert:
If Max(Master Stars) - Min(Master Stars) $\ge 2.0\star$ -> "🚨 Divergence Detected: Conflicting Master Perspectives"

---

## Step 9: Trade Desk Verdict & Execution Playbook

### 9.1 Synthesis Verdict
- **Fundamental Quality Score**: `[SCORE]/100`
- **Thesis Impact**: `🟢 STRONGLY STRENGTHENED` | `🟡 MAINTAINED` | `🟠 WEAKENED` | `🔴 BROKEN`
- **Trade Desk Action**: `ADD` | `HOLD` | `REDUCE` | `SELL` | `AVOID`

### 9.2 Execution Playbooks
- **Playbook 1: Day-1 Gap & Go Momentum**: Enter on breakout of opening 5-min range high with trailing 20-SMA.
- **Playbook 2: Day 2-5 PEAD Swing**: Accumulate on orderly pullback to Day-1 VWAP or 5-SMA on dry volume.
- **Playbook 3A: Panic Fade Reversal**: Buy long on Day-1 intraday VWAP reclaim on panic gap-downs with clean balance sheet.
- **Playbook 3B: Trap Fade Short**: Sell short / buy puts on breakdown of opening VWAP with high Sloan accruals.

---

## Step 10: Multi-Source Financial Rigor & Verification Protocol

Inspired by `ai-berkshire/tools/financial_rigor.py`, all ingested line items undergo deterministic multi-source reconciliation:

```
[Tier 1: Primary SEC 10-Q/K (DuckDB Lake)]
               │
               ▼
[Tier 2: Real-Time TradingView Screener API] ──► FinancialRigorEngine (<=5% tolerance audit)
               │                                            │
               ▼                                            ▼
[Tier 3: Consensus Calendar (Finviz/Yahoo)]   [Gapless 8Q Time Series & Verified Sloan Accrual]
```

1. **Exact Precision**: Decimal calculations for Sloan Accruals $\frac{NI - OCF}{\text{Assets}}$ and FCF Conversion rates.
2. **Tolerance Validation**:
   - $\le 2.0\%$: `✅ Verified High Confidence`
   - $2.0\% - 5.0\%$: `⚠️ Acceptable Timing / Rounding Delta`
   - $> 5.0\%$: `❌ Discrepancy Flagged — Primary SEC Precedence Rule Applied`
3. **Data Provenance**: Every metric in reports tagged with `[value] + [source] + [timestamp]`.

---

## 📜 Living Cumulative Version History

| Version | Date (EST) | Changes & Enhancements | Author / Engine |
| :--- | :--- | :--- | :--- |
| **v2.5** | 2026-08-30 | **Financial Rigor & Multi-Source Cross-Validation Protocol**: Integrated `sources/financial_rigor.py` with exact Sloan accrual reconciliation, TradingView live release synchronization, and gapless 8Q historical series. | Lead Quant Architect |
| **v2.4** | 2026-08-30 | **Unified Single-Source Modal Architecture**: Merged 10-step institutional review and 4-master consensus desk into single reusable UI engine across all 5 dashboard screens. Fixed DOM modal container nesting. | UI & System Architect |
| **v2.3** | 2026-08-30 | **TradingView & Finviz Calendar Integration**: Anchored Day 1 price/gap metrics strictly on earnings release date (AMC/BMO) and eliminated last-business-day miscalculations. | Data Pipeline Engineer |
| **v2.0** | 2026-08-28 | **4-Master Research Desk Consensus**: Integrated Duan Yongping, Warren Buffett & Richard Sloan, Charlie Munger, and Li Lu evaluation matrix with weighted stars (/5.0★). | Quantitative Research Team |
| **v1.0** | 2026-08-20 | **Initial SEC 10-Q Forensic Audit Skill**: SUE score, PEAD drift classification, and DuckDB lake ingestion. | System Base |

