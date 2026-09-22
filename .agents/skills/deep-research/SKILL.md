---
name: deep-research
description: Institutional 4-Master Company Deep Research Desk. Primary SEC 10-K/Q columnar lake ingestion, Piotroski F-Score, Beneish M-Score manipulation audit, reverse DCF valuation, management commitment tracking, 15% random sample audit gate, and quantitative portfolio sizing.
---

# Institutional Company Deep Research Desk (`/deep-research`)

**Skill Type**: TIER 3 | Comprehensive Institutional Due Diligence & Forensics  
**Purpose**: Multi-year deep research on a single enterprise across economic cycles. Synthesizes qualitative insights from four legendary investors (*Duan Yongping*, *Warren Buffett*, *Charlie Munger*, *Li Lu*) with quantitative forensic accounting (*Richard Sloan Accrual Anomaly*, *Joseph Piotroski F-Score*, *Messod Beneish 8-Variable M-Score*), reverse DCF market-implied growth, and active portfolio sizing.

---

## Invocation Syntax

Type in Antigravity Chat:
```text
/deep-research TICKER [mode=deep|gate] [horizon=long|medium]
```

### Direct Aliases:
```text
/company-research TICKER
/investment-checklist TICKER (Fast 6-Gate Buffett Pre-Purchase Audit: mode=gate)
```

### Dual Operating Modes:
1. **Comprehensive Forensics Mode (`mode=deep`, Default)**:
   - Full 4-Master dialectical synthesis (Duan, Buffett, Munger, Li Lu)
   - Reverse DCF inversion & 3-scenario fair value
   - Messod Beneish 8-variable M-Score manipulation audit
   - Joseph Piotroski 9-point fundamental F-Score
   - 15% random sample audit gate against primary SEC 10-K/Q columnar statements
2. **Fast Gate Mode (`mode=gate` / `/investment-checklist`)**:
   - Structured 6-Gate Buffett/Munger pre-purchase verification in ~10 seconds
   - Gates: Circle of Competence, Economic Characteristics, Moat Depth, Management Integrity, Margin of Safety, Fatal Red Flags
   - Output: Immediate `🟢 PASS (6/6)`, `🟡 CAUTION (4-5/6)`, or `🔴 VETO (< 4 or Fatal Red Flag)` verdict with portfolio sizing multiplier clamp (1.0x / 0.5x / 0.0x)

### Examples:
- `/deep-research NVDA` (Default full 4-master deep due diligence for NVDA)
- `/deep-research AAPL mode=gate` (Fast 6-gate pre-purchase verification)
- `/investment-checklist MSFT` (Direct alias running the 6-gate pre-purchase checklist)
- `/deep-research TSLA horizon=long` (10-year compounding horizon analysis)
- `/deep-research PLTR mode=team` (Parallel multi-subagent collaborative desk)


---

## ⚠️ PERMANENT INSTITUTIONAL PROTOCOLS

1. **Language & Units**: All output must be in English. All currency values formatted in `$T`, `$B`, `$M`, `$K`.
2. **Zero LLM Arithmetic**: All valuation multiples, DCF inversions, margins, and accrual ratios MUST be computed deterministically via `sources/financial_rigor.py` and `sources/deep_research_engine.py`. No LLM mental math.
3. **Mandatory Data Source Hierarchy**:
   - **Tier 1 (Ground Truth)**: SEC EDGAR 10-K/10-Q filings stored in local DuckDB Fundamental Lake (`defeatbeta_client.py`).
   - **Tier 2 (Real-Time Synchronizer)**: TradingView Screener Fundamental API Feed.
   - **Tier 3 (Consensus Reference)**: Yahoo Finance / Finviz consensus calendars.
4. **Epistemic Humility & Anti-Pseudoprecision**:
   - Banned: Arbitrary probability-weighted expected returns ($30\% \times A + 50\% \times B$).
   - Banned: Linear extrapolation of peak-cycle revenue growth.
   - Banned: "Guaranteed / obvious / textbook" subjective hyperbole.
   - Required: Explicit margin-of-safety bands (Bull / Base / Bear).
5. **Munger Hard Veto**:
   - If Messod Beneish $M\text{-Score} > -1.78$ (Earnings Manipulation Risk) OR Sloan Accrual Ratio $> 8.0\%$, the Trade Desk MUST trigger a **Hard Veto** (`sizing_multiplier = 0.0x`).

---

## Execution Workflow

```
[Preflight Audit] ──► [AI Bias Tiering] ──► [Deterministic Lake Ingestion]
                                                        │
                                                        ▼
[Reverse DCF Solver] ◄── [Piotroski & Beneish Forensics] ◄── [Sloan Accrual & Cash Flow]
         │
         ▼
[4-Master Dialectic Desk (Duan 25%, Buffett 30%, Munger 25%, Li Lu 20%)]
         │
         ▼
[Divergence Check (Δ >= 2.0★) & Munger Hard Veto Test]
         │
         ▼
[15% Random Sample Audit Gate: PASS / REJECT]
         │
         ▼
[DuckDB Thesis Lake Commitment & reports/deep_research/ Dossier Generation]
```

---

## Step 0: Operational Preflight & Lake Ingestion

Verify that the local DuckDB lake and financial rigor engines are initialized:
```python
from sources.deep_research_engine import deep_research_engine
from sources.defeatbeta_client import fundamental_engine
from sources.thesis_lake import thesis_lake

# Deterministic extraction of multi-year statements
profile = fundamental_engine.get_historical_profile("$TICKER", fetch_remote=True)
```

---

## Step 1: AI Research Bias Awareness (Information Density Rating)

Before proceeding, classify the company into an Information Density Tier to prevent LLM hallucinations:

| Tier | Characteristics | Vulnerability | Mandatory Counter-Strategy |
| :--- | :--- | :--- | :--- |
| **Tier A (Abundant)** | Mega/large-cap, >20 sell-side analysts, heavy financial media. | Strong herd consensus; AI regurgitates consensus without alpha. | Focus on **Inversion**: Why do smart short-sellers doubt the thesis? Where does the market misprice terminal ROIC? |
| **Tier B (Moderate)** | Mid-cap, 3-10 analysts, limited historical cycle data. | AI fills gaps with plausible generalizations. | Tag every derived estimate with confidence bounds and multi-source tolerance. |
| **Tier C (Scarce)** | Small/micro-cap, spin-off, recent IPO, emerging market. | AI becomes overly timid or hallucinates data points. | Pivot to **First-Principles**: Unit economics, replacement cost of assets, customer payback duration. |

---

## Step 2: Forensic Accounting Audit

The engine programmatically calculates three fundamental forensic measures:

### 2.1 Richard Sloan Accrual Anomaly
$$\text{Sloan Ratio} = \frac{\text{Net Income} - \text{Operating Cash Flow}}{\text{Total Assets}} \times 100\%$$
- $\le 4.0\%$: 🟢 Clean Cash-Backed Quality
- $4.0\% - 8.0\%$: 🟡 Moderate Accrual Distortion
- $> 8.0\%$: 🔴 Red-Flag Distortion (Aggressive Revenue/Expense Recognition)

### 2.2 Joseph Piotroski 9-Point F-Score
Audits 9 binary accounting signals across Profitability, Leverage/Liquidity, and Operating Efficiency:
- **8 - 9 Points**: 🟢 Elite Fundamental Compounder
- **5 - 7 Points**: 🟡 Stable Financial Health
- **0 - 4 Points**: 🔴 Severe Structural Deterioration

### 2.3 Messod Beneish 8-Variable Manipulation Model (M-Score)
$$M = -4.84 + 0.920 \cdot \text{DSRI} + 0.528 \cdot \text{GMI} + 0.404 \cdot \text{AQI} + 0.892 \cdot \text{SGI} + 0.115 \cdot \text{DEPI} - 0.172 \cdot \text{SGAI} + 4.037 \cdot \text{TATA} + 0.0327 \cdot \text{LVGI}$$
- **Threshold**:
  - $M > -1.78$: 🔴 High probability of earnings manipulation (**Automatic Munger Hard Veto**)
  - $M \le -1.78$: 🟢 Clean, low manipulation probability

---

## Step 3: Capital Allocation & Management Track Record

Audits how management converts earnings into shareholder equity:
1. **3-Year Commitment Fulfillment**: Measures percentage of past public guidance met or exceeded.
2. **Buyback Valuation Discipline**: Audits historical share repurchases against historical P/E multiples (did buybacks occur below intrinsic value or peak valuation?).
3. **Net Share Dilution**: Measures share count expansion net of Stock-Based Compensation (SBC).
4. **Insider Alignment**: Net insider open-market buying/selling from SEC Form 4 filings.

---

## Step 4: Reverse DCF & Valuation Inversion

Rather than guessing distant future cash flows, the engine solves for what the market is currently pricing in:
- **Implied Annual FCF Growth Rate ($g_{\text{implied}}$)**: The hurdle rate the company must achieve over the next 5 years to justify current market capitalization.
- **3-Scenario Fair Value**:
  - **Bull Case**: $g_{\text{implied}} \times 1.25$ with $+15\%$ terminal multiple expansion.
  - **Base Case (Target)**: $g_{\text{implied}} \times 0.95$ with normalized multiple.
  - **Bear Case**: $g_{\text{implied}} \times 0.50$ with $-25\%$ multiple compression.
- **Margin of Safety**: $\frac{\text{Base Fair Value} - \text{Current Price}}{\text{Base Fair Value}} \times 100\%$

---

## Step 5: Four-Master Dialectical Synthesis

| Master | Analytical Dimension | Target Criteria | Weight |
| :--- | :--- | :--- | :---: |
| **Duan Yongping** | Business Essence & Ben-Fen | Gross Margin $\ge 50\%$, high customer pricing power, focused product line. | **25%** |
| **Buffett & Sloan** | Economic Moat & Cash Quality | Sloan Accrual $\le 4\%$, FCF Conversion $\ge 100\%$, Net Cash balance sheet. | **30%** |
| **Charlie Munger** | Inversion, Manipulation & Risk | Beneish $M \le -1.78$, Piotroski $\ge 7$, zero corporate governance red flags. | **25%** |
| **Li Lu** | Civilizational Megatrend & TAM | Long-term technological secular tailwind, high insider skin-in-the-game. | **20%** |
| **Composite Desk** | **Unified Fundamental Quality** | **Composite Score (0-100) & Weighted Stars (1.0 - 5.0★)** | **100%** |

### Divergence & Hard Veto Rules:
- **Divergence Detected**: If $\max(\text{Stars}) - \min(\text{Stars}) \ge 2.0\star$, output divergence warning and cap sizing multiplier at `0.5x`.
- **Munger Hard Veto**: If Beneish $M > -1.78$ or Sloan Accrual $> 8.0\%$, override score to `0.0x` sizing (Pass / Short Candidate).

---

## Step 6: Post-Run 15% Random Sample Audit Gate

Before publishing the dossier and committing to DuckDB, the engine executes `audit_dossier_data`:
1. Randomly samples 15% - 40% of extracted metrics (Market Cap, Revenue, Net Income, FCF, Sloan Accrual, Current Price).
2. Audits extracted numbers against the primary SEC EDGAR source.
3. If any item deviates by $> 5.0\%$:
   - Verdict: **【打回】AUDIT REJECTED - DATA DRIFT**.
4. If all items within tolerance:
   - Verdict: **【准出】PASSED VERIFICATION**.

---

## Step 7: Output Artifacts & UI Delivery

Running `/deep-research TICKER` automatically outputs:
1. **Markdown Dossier**: Saved to `reports/deep_research/{TICKER}_dossier_{YYYYMMDD}.md`.
2. **DuckDB Database Record**: Persisted to `data/attribution_lake.duckdb -> deep_research_theses`.
3. **Interactive Modal View**: Rendered in Screener `latest_report.html`.
