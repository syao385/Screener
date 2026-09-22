# Institutional Screener: Comprehensive Full-System User Guide

**Document Version:** `8.0.0` (Comprehensive Operational Manual & Phase 8 Upstream Thematic Discovery Release)  
**Last Updated:** `September 19, 2026`  
**Target Audience:** Quantitative Portfolio Managers, Active Discretionary Traders & System Operators  
**Coverage:** All 8 Primary Screens / Tabs, Modals, Autonomous Daemon, Order Desk, Step 10 Deep Research, Reactive Conviction Sizing, Upstream Thematic Discovery, Depth4 D1-D4 Cascade & Bottleneck Hunting


---

## 🧭 System Architecture & Primary Navigation Bar

The dashboard is organized into **8 Primary Operational Desks** accessible via the top navigation bar, plus global real-time telemetry pills:
1. `🚀 Screener & Alpha Flow`: 24/7 multi-session momentum scanner & setup ranking.
2. `🎯 Trade Execution Desk (Actions Tab)`: 5-tier prioritized action queue with Fidelity copy & bracket tickets.
3. `💼 Portfolio Manager (Live Book)`: Live holdings grid, 3 view modes, multi-factor filters, and CRUD persistence.
4. `📊 4D Macro & Allocations`: 4-pillar cross-asset state space, turning points, and sector allocation targets.
5. `🏢 Earnings Intelligence & 4-Master Desk`: Gapless 8-quarter forensics, Sloan accruals, SUE, and PEAD radar.
6. `📈 Alpha Attribution & Auto-Tuning`: DuckDB attribution lake, Brinson-Fachler factor decomposition & parameter tuner.
7. `🛡️ Risk Governance & Stress Testing`: Intraday drawdown circuit breakers, 10,000-path Monte Carlo cones, 6 crisis replays & paper execution desk.
8. `📜 Thesis Lifecycle & News Pulse Terminal`: Two-stage setup promotion, fleet-wide health matrix, drift radar & beta residual news attribution.

---

## 1. Screen 1: 🚀 Screener & Alpha Flow Desk

### Purpose & Operating Philosophy
Filters thousands of US equities in real time against strict institutional criteria, ensuring zero static or fake data. Automatically pivots breakout reference anchors depending on market session (Premarket, Regular Hours, After-Hours, or Weekend).

- **Universal Liquidity Screen**: Enforces $\text{Market Cap} \ge \$1.0\text{B}$, $\text{30D Avg Volume} \ge 500,000$, $\text{Gap} \ge +3.0\%$, and anchored $\text{RVOL} \ge 1.50\text{x}$.
- **Strict Multi-Session RVOL Anchor Standard**:
  Relative Volume ($\text{RVOL}$) is evaluated as the cumulative volume since the session anchor time up to current evaluation time $T$, divided by the 20-day historical average cumulative volume up to that exact same time:
  $$\text{RVOL}(T) = \frac{\text{Cumulative Volume since Anchor Time up to } T}{\text{20-day Average of Cumulative Volume since Anchor Time up to } T}$$
  - **Premarket**: Anchor is **Midnight – 00:00 AM EST** (00:00 to 09:30 EST)
  - **Regular Hours**: Anchor is **09:30 AM EST** (09:30 to 16:30 EST)
  - **After-Hours**: Anchor is **04:30 PM EST (16:30 EST)** (16:30 to 23:59:59 EST Mon–Thu)
  - **Weekend**: Anchor is **Friday 04:30 PM EST** (Friday 16:30 through Sunday 23:59:59 EST)
- **Multi-Factor Setup Scoring (1.0★ to 5.0★)**: Synthesizes news catalyst strength, volume conviction, options skew, technical breakout clearance, and macro alignment.
- **Floating Hover Scorecards**: Hovering over any ticker link displays a floating detailed breakdown scorecard with criteria checklists and sub-factor scores.
- **Expandable Accordion Drawers (`🔍`)**:
  - **4-Master Fundamental & Earnings Audit**: Displays Sloan cash quality, SUE factor, and thesis impact.
  - **Skill 12 Trading Plan**: Entry pivot, Hard Stop, Soft Stop (20-SMA), Chandelier ATR trailing stop, Target 1 (+2.0R), and Target 2 (+3.5R).
  - **Options Gamma Surface**: Call/Put Walls, Gamma Flip level, and net whale premium flow.
- **Interactive Action Buttons**:
  - `⚡ Sizing`: Launches the dynamic Position Sizing Calculator with pre-populated ticker prices.
  - `⚡ SUE`: Opens the Dual-Skill Flash Earnings & 4-Master Consensus modal.

---

## 2. Screen 2: 🎯 Trade Execution Desk (Actions Tab)

### Purpose & Operating Philosophy
Consolidates real-time events from the background SQLite Monitor Engine (`sources/portfolio_monitor_engine.py`) and ranks actionable trading tasks into 5 clear priority tiers.

### Priority Tiers
1. **Tier 1 (Emergency Hard Stops & Broken Theses)**: Positions that breached protective stop-loss levels, broken investment theses ($H < 3.0$), or fatal red-line breaches (fraud, CEO departure). Requires immediate liquidation at open.
2. **Tier 2 (Risk Alerts, Stealth Flow & Sector Invalidation)**: News Pulse stealth volume/price surges ($Z_\epsilon \ge 2.0$), severe regulatory shocks ($S > 80$), and parent sector ETF flow deterioration ($< 40.0$). Triggers immediate surveillance and staged stop-ratchets.
3. **Tier 3 (Profit Targets & Weakened Thesis Trims)**: Positions achieving Target 1 (+2.0R) or Target 2 (+3.5R) ratcheting to breakeven, and Weakened Thesis linear de-risking ($\text{Trim \%} = (6.0 - H) \times 10\%$).
4. **Tier 4 (High-Conviction Breakout Entries & Trailing Ratchets)**: Screened candidates meeting 9 Master Setup criteria with fresh session breakout confirmation, and daily $2.0\times\text{ATR}$ / 20-SMA ratchets.
5. **Tier 5 (Routine Portfolio Rebalancing)**: Capital allocation adjustments based on macro volatility parity and sector target caps.

### Execution Tools
- `📋 Copy`: Copies a single-line order string formatted for rapid notes or web ticket entry:
  `BUY 25 NVDA @ LIMIT $219.62 | STOP $210.00 | T1 $229.24 | TIF: DAY | ACC: Traditional IRA`
- `📑 Bracket`: Opens the Fidelity Active Trader Pro (ATP) Multi-Leg OTOCO Bracket ticket modal.
- `☑️ Checkboxes`: Mark tasks as Done or Skip. Changes persist locally.

---

## 3. Screen 3: 💼 Portfolio Manager (Live Book)

### Purpose & Operating Philosophy
Provides 100% full-stack live visibility into your brokerage holdings (default 73 active positions with live market feeds). Supports custom additions, inline edits, and deletions that persist across browser refreshes via `localStorage`.

### Key Features
- **3 View Mode Tabs**:
  - `Core Overview (14 Columns)`: Cost basis, quantity, market value, total P&L ($ / %), sector tags, and strategy classifications.
  - `Technical & MAs (17 Columns)`: Session % Change, Gap %, VWAP, SMA20, SMA50, SMA200, and distance to prior day high.
  - `Options Structure & Walls (17 Columns)`: Call Wall, Put Wall, Dealer Gamma Flip, Vol/OI ratio, ATM IV, and analyst consensus.
- **Comprehensive Multi-Factor Filtering Bar**:
  - Breakout checkboxes (`> Premarket High`, `> Last Day High`, etc.).
  - Dropdown range filters for `% Chg`, `Gap %`, `% Open`, `% VWAP` ($\pm 1\sigma, \pm 2\sigma$), `Total P&L %`, and `Weight %`.
- **Reactive Conviction Tier Allocation & Concentration Risk Desk (`Skill 07`)**:
  - **3 Institutional Conviction Tiers**:
    - **Tier 1 (Core Champions)**: Max 10% single asset cap | 1.2x base risk tolerance | 35% aggregate portfolio cap.
    - **Tier 2 (Growth Leaders)**: Max 5% single asset cap | 0.8x base risk tolerance | 60% aggregate portfolio cap.
    - **Tier 3 (Tactical / Leveraged)**: Strict 2% single asset cap | 0.5x base risk tolerance | 100% aggregate cap.
  - **Dynamic Overweight Rebalancing Alerts**: Automatically detects any position where $\text{Weight} > \text{Tier Cap} \times 1.05$. Calculates exact dollar excess ($\text{Excess} = \text{Current Value} - \text{NAV} \times \text{Cap}$) and recommended trim shares ($\lceil\text{Excess} / \text{Price}\rceil$).
  - **Reactive Live Synchronization**: When a position's Conviction Tier is modified from the table or modal, all aggregate tier weights, cap status badges, overweight alerts, and Sizing Calculator risk budgets update instantaneously without page reload and persist in `localStorage`.
- **Live Position Editing, Stop-Loss Liquidation & Cross-Widget Synchronized Deletion**:
  - `✏️ Edit`: Modify Conviction Tier, Shares, Cost Basis, Protective Stop, Target, or Trading Strategy.
  - `❌ Delete / Exit`: Remove position upon hitting stop loss or discretionary exit. The system automatically:
    1. Removes the position from the active portfolio book.
    2. Credits liquidated proceeds ($\text{Shares} \times \text{Current Price}$) directly to the `cash_balance`, preserving NAV integrity.
    3. Purges corresponding rows from the **Multi-Tier Adaptive Stop-Loss Desk** and recalibrates Safe/Warning/Action count pills.
    4. Purges portfolio-origin execution tickets from the **Trade Execution Desk (Actions Tab)**.
    5. Purges tracked records across **Phase 6: Thesis Lifecycle Terminal** (Module A Fleet Matrix, Module B Drift Surveillance, Module D PEAD Playbook) and decrements tracked holding counters.
    6. Stores deleted symbols in persistent `localStorage` to guarantee cross-refresh retention.
  - `⚡ Sizing`: Recalculate rebalance sizing and risk budget allocations with automatically pre-selected conviction tier.
  - `📥 Import Fidelity CSV`: Drag and drop or paste your active Fidelity CSV statement to refresh all holdings.
  - `🔄 Restore Defaults`: One-click restoration of initial baseline holdings.

---

## 4. Screen 4: 📊 4D Macro & Allocations Desk

### Purpose & Operating Philosophy
Operates under the `01_macro-regime-new.md` v3.0 standard. Continuously maps global cross-asset signals to generate dynamic portfolio risk multipliers and optimal capital allocations.

### Key Features
- **4-Pillar Cross-Asset State Space**: Real-time radar visualizer tracking Liquidity (EFFR, 10Y), Growth (Copper/Gold, Semis), Volatility (VIX, MOVE), and Breadth (A/D %, Net Highs).
- **Dual Temporal Turning-Point Engine**:
  - **Intraday Climax/Capitulation Gauge**: Detects opening gap exhaustion and extreme intraday tick reversals.
  - **Swing Macro Top/Bottom Gauge (0-100)**: Quantitative 9-factor model grading market posture (e.g. `🟡 TOP WARNING: 51.0`).
- **4-Quadrant Bayesian Scenario Matrix**: Probability distribution across Goldilocks, Reflation, Stagflation, and Deflation regimes.
- **Asset Allocation Targeter**: Dynamically balances Equity (70-80%), Gold (8-12%), Bitcoin (2-4%), and SPAXX Cash Reserves (15-20%) according to the rule $E + G + B + C = 100\%$.

---

## 5. Screen 5: 🏢 Earnings Intelligence & 4-Master Desk

### Purpose & Operating Philosophy
Replaces unverified financial blog headlines with forensic SEC 10-K / 10-Q accounting analysis, consensus forecasting, post-earnings announcement drift (PEAD) models, and multi-year company deep research dossiers.

### Key Features
- **Gapless 8-Quarter Time-Series Reconciler**: Audits 8 consecutive quarters of EPS, Revenue, and Free Cash Flow to verify organic growth.
- **Sloan Accrual Quality Meter**: Calculates $(\text{Net Income} - \text{Operating Cash Flow}) / \text{Total Assets}$.
  - $< 4.0\%$: High-quality cash earnings (Green flag).
  - $> 10.0\%$: Accrual anomaly / aggressive earnings inflation (Red warning).
- **Standardized Unexpected Earnings (SUE)**: Measures $(EPS_{actual} - EPS_{est}) / \sigma_{est}$ in standard deviations.
- **PEAD Drift Radar**: Tracks stocks with blowout earnings for multi-week post-announcement momentum continuations.
- **🔬 Step 10: Institutional Company Deep Research Dossier & Forensics (`/deep-research`)**:
  - **4-Master Dialectical Synthesis**: Duan Yongping (25%), Warren Buffett & Sloan (30%), Charlie Munger (25%), Li Lu (20%).
  - **Forensic Accounting Models**:
    - **Joseph Piotroski 9-Point F-Score**: Financial health, leverage, and operating efficiency checks.
    - **Messod Beneish 8-Variable Manipulation Model ($M$-Score)**: Verifies that $M \le -1.78$ to rule out financial statement distortion.
  - **Reverse DCF Inversion Engine**: Bisection solver extracting market-implied FCF compounding growth rate; establishes 3-scenario fair value hierarchy (Bull, Base, Bear) with 15% margin of safety.
  - **15% Random Sample SEC EDGAR Audit Gate**: Programmatically verifies extracted figures against raw regulatory filings before granting `【准出】` clearance.
  - **Dual Persistence & Live On-Demand Fallback**: Theses are stored in DuckDB `deep_research_theses` with file mirror in `data/deep_research/{SYMBOL}.json`. Watchlist stocks without pre-saved dossiers feature an interactive `⚡ Populate Deep Research Live` button that computes complete forensics client-side in <300ms.

---

## 6. Screen 6: 📈 Alpha Attribution & Auto-Tuning Desk

### Purpose & Operating Philosophy
Institutional Brinson-Fachler Factor Attribution engine powered by an analytical DuckDB Data Lake (`data/attribution_lake.duckdb`). Provides mathematical accountability and machine-calibrated risk parameters.

### Key Features
- **Brinson-Fachler Factor Decomposition (11 GICS Sectors)**:
  - **Allocation Effect ($A$)**: Measures alpha generated by overweighting winning sectors vs S&P 500 benchmark.
  - **Selection Effect ($S$)**: Measures alpha from single-stock stock picking within sectors.
  - **Interaction Effect ($I$)**: Measures the combined cross-effect of allocation and selection.
  - **Total Active Alpha**: Exact mathematical sum $R^P - R^B = \sum (A_i + S_i + I_i)$.
- **Rolling Institutional Risk Ratios**: Sharpe Ratio (252D), Sortino Ratio, Information Ratio, Tracking Error, and Maximum Drawdown.
- **Continuous Parameter Auto-Tuning**:
  - Automatically calibrates conviction multipliers for the 9 Master Setup Archetypes.
  - **Hard Safety Clamps**: Enforces strict mathematical limits $[0.50\text{x}, 1.35\text{x}]$ to prevent over-leveraging.
  - **Regime-Adaptive Chandelier Stops**: VIX-adjusted ATR trailing stops ($1.8\text{x}$ low vol, $2.0\text{x}$ baseline, $2.4\text{x}$ high vol).
  - **Execution Slippage Governor**: Quantifies realized slippage in basis points.
- **DuckDB Trade Ledger & Forward Fills Control**:
  - 73 synthesized baseline holdings pre-loaded.
  - **Forward Incremental Fills Toggle**: Defaults to **OFF** per platform platform rules; toggleable on/off anytime.
  - **Manual Trade Override (`⚡`)**: Interactive modal to record custom trade fills directly into DuckDB.

---

## 7. Screen 7: 🛡️ Risk Governance & Stress Testing Desk

### Purpose & Operating Philosophy
Phase 5 institutional tail-risk fortress combining automated capital preservation circuit breakers, forward Monte Carlo probability cones, historical crisis replays, and a unified paper execution gateway.

### Key Features
- **Executive Tail-Risk KPI Banner**:
  - **High-Water Mark NAV**: Tracks session peak equity with real-time drawdown percentage.
  - **1-Day VaR (95% & 99% Parametric & Historical)**: Maximum expected loss under normal market conditions.
  - **1-Day CVaR (Expected Shortfall 95%)**: Expected loss severity when the 95% VaR threshold is breached.
  - **Portfolio Beta & Annualized Volatility**: Weighted beta across all holdings and cash.
  - **VIX Term Structure & Gamma Flip Sentry**: Inversion detector ($VIX / VXV > 1.00$) and SPX dealer gamma flip alert.
- **6 Crisis Historical Replay Stress Engine**:
  - Deterministically replays current portfolio sector weights against 6 major historical market crashes:
    1. **2020 COVID Liquidity Freeze** ($-34.0\%$ SPY shock)
    2. **2022 Fed Rate Hike & Multiple Compression** ($-19.4\%$ SPY shock)
    3. **2008 Global Financial Crisis** ($-56.8\%$ SPY shock)
    4. **2024 Tech/Yen Carry Shock** ($-8.5\%$ SPY shock)
    5. **2000 Dot-Com Meltdown** ($-49.1\%$ SPY shock)
    6. **1987 Black Monday** ($-20.5\%$ 1-day shock)
  - Displays projected portfolio shock %, estimated dollar loss, and active alpha vs SPY.
- **10,000-Path Monte Carlo Forward Simulation Cones**:
  - Geometric Brownian motion forward projections over 30-day, 60-day, and 90-day horizons.
  - Displays probability of profit %, 5th percentile worst-case tail loss, and 95th percentile upside target.
- **Autonomous Intraday Drawdown Circuit Breakers**:
  - **Level 1 Warning ($-1.0\%$)**: Tightens Chandelier trailing stops to $1.5\text{x}$ ATR, caps archetype conviction to $\le 0.85\text{x}$.
  - **Level 2 De-Risk ($-2.0\%$)**: Clamps portfolio risk multiplier to $0.50\text{x}$, flags Tier 3 speculative trades for partial trimming.
  - **Level 3 Kill-Switch ($-3.0\%$)**: Autonomous halt of all automated BUY orders, locks $100\%$ cash reserves, and dispatches critical alert.
  - **Simulation & Reset Controls**: Test trigger buttons (`Normal`, `-1.0%`, `-2.0%`, `-3.0%`) and 1-click manual breaker reset.
- **Unified Paper Trading Simulator & Gateway**:
  - Ingests simulated orders into dedicated DuckDB tables (`data/paper_trading.duckdb`).
  - Realistic fill modeling with bid-ask spread ($0.03\%$) and market slippage ($1-4\text{ bps}$).
  - **Smart Limit Order Slicing (`🪜 Ladder`)**: Automatically decomposes large orders into a 3-tranche execution ladder ($40\%$ breakout pivot, $35\%$ pullback fill, $25\%$ volume confirm).
  - **Alpaca Free-Tier REST Gateway**: Natively routes orders to official Alpaca Paper/Live accounts when API keys are supplied.
  - **Universal Webhook Gateway**: Dispatches JSON execution payloads to external institutional execution routers.

---

## 8. Screen 8: 📜 Thesis Lifecycle & News Pulse Terminal

### Purpose & Operating Philosophy
Unifies short-term tactical momentum trading (9 Master Archetypes) with long-term institutional fundamental thesis monitoring (Skills 08, 13, and 14). Operates as a continuous two-stage state machine that automatically promotes winning setups to core holdings while executing mathematical de-risking upon fundamental degradation.

### Key Interactive Modules
1. **Module A: Fleet-Wide Thesis Health Matrix**:
   - Displays all active positions categorized by **Promotion Stage**: `TACTICAL_SETUP` (Days 1–10, governed by technical pivots & 2.0R targets) vs `CORE_THESIS` (promoted holdings governed by 8-quarter financial baselines).
   - Real-time **Composite Health Score ($0.0 - 10.0$)** with color-coded classification:
     - `🟢 STRONG (9.0 - 10.0)`: Full conviction; add on Stage 2 pullbacks.
     - `🟢 INTACT (7.0 - 8.9)`: Healthy core holding; standard trailing stops.
     - `🟡 WEAKENED (5.0 - 6.9)`: Linear trim triggered: $\text{Trim \%} = (6.0 - H) \times 10\%$.
     - `🟠 DAMAGED (3.0 - 4.9)`: 50% risk trim; Tier 2 escalation.
     - `🔴 BROKEN (<3.0 or Fatal Red-Line)`: 100% liquidation order routed to Tier 1 Execution Desk.
2. **Module B: Drift Radar & Forensic Accounting Monitor**:
   - Tracks 8-quarter drift across core quantitative metrics (YoY Revenue CAGR, Gross Margin, Richard Sloan Accrual Ratio, Free Cash Flow Conversion).
   - Highlights critical red-lines (auditor qualification, sudden CEO/CFO departure, customer concentration breach).
   - Quantifies semantic narrative drift across consecutive SEC 10-Q filing management discussions.
3. **Module C: Breaking News & Beta Residual Attribution Stream (Skill 13)**:
   - Real-time tape of single-stock price moves decomposed into Systematic Market Return (SPY), Sector Return (GICS ETF), and **Idiosyncratic Residual ($\epsilon_{i,t}$)**:
     $$\epsilon_{i,t} = R_{i,t} - (\alpha_i + \beta_{\text{SPY}} R_{\text{SPY},t} + \beta_{\text{Sec}} R_{\text{Sec},t})$$
   - **Multi-Source Authority Hierarchy**:
     - **SEC Regulatory Disclosures (Authority: 100.0)**: Form 8-K, 10-Q, 10-K, Form 4. Unconditional fundamental truth.
     - **Company Press Releases (Authority: 85.0)**: Business Wire, PR Newswire, GlobeNewswire corporate earnings & guidance releases.
     - **Tier-1 Financial Media (Authority: 75.0)**: Wall Street Journal, Bloomberg, Reuters, Financial Times. 1-to-3-day narrative shocks.
     - **Mainstream Financial Portals (Authority: 65.0 - 70.0)**: CNBC, MarketWatch, Yahoo Finance.
     - **Retail & Social Media (Authority: 25.0)**: Reddit, X, StockTwits. Crowding sentry and climax top/squeeze detection.
   - Computes multi-factor **News Signal Score ($0 - 100$)**:
     $$\text{Signal Score} = 0.40 \cdot \text{Relevance} + 0.30 \cdot \text{Novelty} + 0.20 \cdot \text{Authority} + 0.10 \cdot |\text{Sentiment}|$$
   - **Blended Institutional Catalyst Rating & Setup Quality Scoring**:
     $$\text{Blended Catalyst} = 0.50 \cdot \text{Stars} + 0.30 \cdot \left(\frac{\text{Signal Score}}{20}\right) + 0.20 \cdot \text{Sentiment Direction}$$
   - **Enhanced Composite Catalyst Dual-Badge Grid Display**:
     - **Screener & Portfolio Tables**: Feature dual badges `[5★ M&A]` + `[Sig: 85 • Primary]` with hover telemetry scorecard detailing source breakdown, sentiment delta ($\Delta S_7$), and authority weighting.
   - **7-Day Delta Sentiment ($\Delta S_7$) & Divergence Regimes**:
     - `🕵️ Stealth Accumulation`: Institutional sentiment surge ($\Delta S \ge +0.30$) during price consolidation ($P_{\Delta} \le +1.0\%$).
     - `🔴 Climax Distribution / Retail Trap`: Social sentiment euphoria ($S_{\text{social}} \ge 0.75$) with heavy volume stall or negative institutional sentiment delta.
     - `🚀 PEAD Momentum Alignment`: Positive earnings shock + guidance hike confirmed by price continuation ($P_{\Delta} \ge +2.0\%$).
   - **Stealth Event Detector**: Automatically flags abnormal residual price moves ($Z_\epsilon \ge 2.0$) with zero public high-signal news, alerting the desk to institutional accumulation or non-public order flow.

---

## 9. Modal Dialogues & Interactive Calculators

1. **Institutional Position Sizing Calculator (`⚡ Sizing Calc`)**:
   - Computes exact share count, required capital, and dollar risk using the Skill 07 formula:
     $$\text{Shares} = \min\left(\frac{\text{NAV} \times \text{Tier Cap}}{\text{Price}}, \frac{\text{NAV} \times \text{Risk Budget}}{\text{Price} - \text{Stop Loss}}\right) \times \text{Macro Mult} \times \text{Options Mult}$$
   - Features full Skill 12 protective stop levels (Hard Stop, 20-SMA Soft Stop, Chandelier Trailing ATR, Targets 1 & 2).
2. **Fidelity CSV Ingestion Modal (`📥 Import Fidelity CSV`)**:
   - Drag-and-drop or paste raw brokerage CSV exports. Automatically parses account name, number, cash balance, and positions.
3. **Fidelity ATP OTOCO Bracket Ticket Modal (`📑 Bracket`)**:
   - Pre-populates ready-to-execute bracket tickets defining Primary Limit Entry, +1.0R Breakeven Lock, GTC Hard Stop Loss, and +2.5R Profit Target.
4. **Dual-Skill Flash Earnings & 4-Master Modal (`⚡ SUE`)**:
   - Tab 1: SEC 10-K/10-Q forensic audit, Sloan accruals, quarterly comparisons, and PEAD action playbook.
   - Tab 2: 4-Master consensus scores, price targets, and bull/bear thesis debates.
5. **Manual Trade Override Modal (`⚡ Manual Trade Override`)**:
   - Allows instant logging of manual fills into the DuckDB analytical lake with custom archetype and tier tagging.

---

## 10. Background System Daemon & Automation Schedules

The platform features an autonomous background daemon (`scheduler/system_daemon.py`) executing across structured market operational sessions:
- **04:00 - 09:15 EST (Premarket Ingestion & Catalyst Verification)**: Evaluates early gap momentum, overnight macro feeds, and runs `sources/news_pulse.py` to filter false PR pump candidates and populate catalyst scores.
- **09:15 - 09:30 EST (Pre-Open Execution Prep)**: Syncs SQLite monitor tables and prepares prioritized Tier 1–5 action queues in the Trade Execution Desk.
- **09:30 - 16:00 EST (Continuous Intraday Micro-Scan & Surveillance)**: Evaluates drawdown circuit breakers every 60s, executes stop ratchets, checks Target 1 (+2.0R) triggers, and flags stealth volume/price surges ($Z_\epsilon \ge 2.0$).
- **16:00 - 16:30 EST (Closing Cross Audit)**: Captures daily closing NAV and ingests MOC imbalances.
- **16:30 - 20:00 EST (Postmarket Reconciliation & Thesis Drift)**: Ingests 10-Q statements into DuckDB, executes post-earnings price divergence attribution, and runs `sources/thesis_monitor.py` to update fleet-wide Thesis Health Scores and drift history.

---

## 11. Operational Best Practices & Troubleshooting

1. **Zero Fake Data Integrity**: If an external provider is temporarily unresponsive, the system gracefully logs a warning and shows `" — "` rather than generating placeholder numbers.
2. **Database Concurrency Protection**: The analytical DuckDB lakes (`attribution_lake.duckdb` and `paper_trading.duckdb`) employ connection-level read-only fallbacks to prevent file locking conflicts between background daemon tasks and interactive UI builds.
3. **Resetting Circuit Breakers**: If an intraday market flash breach triggers Level 1 or Level 2, evaluate market posture on Screen 4. Once stabilized, click `🔄 Reset Breaker` on Screen 7 to resume standard automated trading operations.

---

## 12. Zero-Redundancy Fundamental Caching & Change Detection Protocol

To ensure sub-second latency and prevent rate-limiting during continuous 60-second market scans, the system enforces a strict **Zero-Redundancy Fundamental Caching Protocol**:
1. **Primary Persistence & Lake Ingestion**: Historical 8-quarter income statements, balance sheets, cash flows, and deep research dossiers are persisted in DuckDB (`data/attribution_lake.duckdb`) and mirrored in `data/fundamental_cache/{TICKER}.json` and `data/deep_research/{TICKER}.json`.
2. **Change Detection Sentry**: Remote network scraping (Yahoo Finance, TradingView, SEC EDGAR) is completely bypassed during routine screener loops unless:
   - An active corporate earnings event is scheduled for `yesterday_amc`, `today_bmo`, or `today_amc` and actual reported numbers are missing.
   - The user explicitly triggers an on-demand audit via `--force-refresh` or `/deep-research TICKER`.
   - The local cache file does not exist.
3. **Execution Speed Benefit**: Eliminating repetitive network pulls for unchanged fundamental profiles reduces minute-by-minute pipeline runtimes from ~90 seconds to under 5 seconds.

---

## 13. Smart Real-Time UI Auto-Refresh (`Start_Live_Screener.bat`)

When running the screener in continuous live mode via `Start_Live_Screener.bat` (`python run_screener.py --realtime`), the generated HTML report (`latest_report.html`) automatically stays synchronized:
- **60-Second Polling Cycle**: Synchronized with background market data ingestion.
- **Top Navigation Status Pill (`🔄 Auto-Refresh: 60s`)**: Provides a live countdown. Click to toggle Pause / Resume anytime.
- **Intelligent Non-Intrusive Pause Protection**:
  - Automatically pauses countdown if any modal dialogue is open (Sizing, SUE, Edit Position, Fidelity CSV).
  - Automatically pauses countdown if an `<input>`, `<select>`, or `<textarea>` has active focus.
- **State Preservation Across Reloads**: Saves the user's active desk/view (e.g. Portfolio Manager, Earnings Desk) and vertical scroll position to `sessionStorage`, immediately restoring exact context upon each reload.

---

## 10. Thematic Discovery & Depth4 Macro Cascade Guide

The system includes upstream thematic discovery tools powered by `sources/thematic_intelligence.py` to identify durable trends before they become crowded:

### Key Workflows:
1. **Upstream Trend Audit (`/trend-discovery`)**:
   - Runs the **4-Layer Durability Gate** (`01_trend-identification.md`):
     - Layer 1: Sector Momentum (RS $1\text{M} > 0$, $>55\%$ stocks $> 200$-SMA).
     - Layer 2: CapEx Commitments (Primary filing capex YoY $\ge +15\%$).
     - Layer 3: Earnings Revisions (Net revision breadth $\ge 50\%$).
     - Layer 4: Relative Price Strength (Outperforming SPY).
   - Classifies trends into `🟢 INVESTABLE`, `🟡 WATCH`, or `🔴 NOISE`.

2. **Depth4 D1–D4 Causal Cascades (`https://depth4.com/`)**:
   - Categorizes equities across four time horizons:
     - `D1_CATALYST`: Policy or regulatory catalyst.
     - `D2_CROWDED`: First-order obvious repricing (Unpriced Room $<20\%$; avoid chasing).
     - `D3_SPILLOVER`: Tier-1 equipment suppliers.
     - `D4_UNPRICED_BOTTLENECK`: Structural chokepoints with high Unpriced Room ($>60\%$).

3. **Chokepoint Arbitrage & Valuation Gate (`/bottleneck-hunter [THEME]`)**:
   - Scans Layer 2–3 suppliers (InP substrates, laser sources, wafer-level probe cards, quick-disconnect couplings, transformers).
   - Enforces **Permanent Rule 5 Valuation Gate**: If $P/S > 30.0\times$, position sizing is automatically vetoed (`0.0x`).

4. **S-Curve Core Alpha Evaluator (`/era-alpha [THEME] [TICKER]`)**:
   - Identifies 1–3 platform compounding anchors ($\text{ROCE} \ge 18\%$, gross margin $\ge 45\%$) for Tier 1 Core holding ($20\%$ NAV cap).

---

## 14. Cumulative Living Version Changelog

| Version | Release Date | Key Enhancements & Milestones | Lead Author |
| :--- | :--- | :--- | :--- |
| **`v1.0.0`** | August 2026 | Initial baseline multi-session momentum screener & Finviz fundamental scraper. | Senior Quant PM |
| **`v2.0.0`** | August 2026 | Added 4-Master Fundamental & Earnings Audit modal and SQLite execution monitor. | Senior Quant PM |
| **`v3.0.0`** | August 2026 | Universal 4-Horizon Earnings Consensus architecture; eliminated calendar roll distortions. | Senior Quant PM |
| **`v4.0.0`** | September 2026 | Integrated Phase 4 DuckDB Alpha Attribution Lake and Brinson-Fachler factor decomposition. | Senior Quant PM |
| **`v5.0.0`** | September 2026 | Added Phase 5 Intraday Drawdown Circuit Breakers, 10k Monte Carlo, and Crisis Replay stress-testing. | Senior Quant PM |
| **`v6.0.0`** | September 2026 | Added Phase 6 Thesis Lifecycle Promotion & Multi-Source News Pulse Terminal with residual beta attribution. | Senior Quant PM |
| **`v7.0.0`** | September 13, 2026 | **Phase 7 Deep Research & Reactive Portfolio Architecture**: Deployed Step 10 Deep Research Desk (4-Master dialectic, Reverse DCF, Piotroski 9-pt F-Score, Beneish 8-var M-Score, 15% SEC audit gate). Implemented reactive Conviction Tier Allocation Desk with dynamic trim shares, zero-redundancy fundamental caching protocol, and smart 60-second live UI auto-refresh engine. | Senior Quant PM |
| **`v8.0.0`** | September 19, 2026 | **Phase 8 Upstream Thematic Discovery & Depth4 Macro Cascade Engine**: Deployed `sources/thematic_intelligence.py` integrating 4-Layer Durability Gate (`01_trend-identification.md`), Depth4 D1–D4 Causal Cascades (`https://depth4.com/`) with Unpriced Room % calculation, Era Alpha platform compounding evaluator (`02_era-alpha.md`), and Layer 2–3 physical chokepoint arbitrage with $P/S \le 30\times$ valuation gate (`02_bottleneck-hunter.md`). Added Antigravity skills `/bottleneck-hunter`, `/era-alpha`, and `/trend-discovery`. | Senior Quant PM |
| **`v9.0.0`** | September 22, 2026 | **Phase 9-11 Institutional v2.0 Production Release**: Formally synthesized Buffett 6-Gate Pre-Purchase Verification Audit & 4-Master Consensus Desk into modal and table UI; engineered Forensic Accounting Confluence Engine (corrected Beneish M-Score AQI formula, SGI hyper-growth capping, 4Q rolling Sloan accruals, and multi-signal confluence veto gating); standardized Multi-Session RVOL Anchors (00:00 Midnight, 09:30 AM, 16:30 PM, Friday 16:30 PM); instituted Hands-Off Earnings Review Daemon; eliminated synthetic fallback data; packaged Antigravity Institutional Skills suite; and validated 100% test coverage. | Senior Quant PM |

---

## 15. The Buffett 6-Gate Pre-Purchase Verification Audit & Forensic Desk

Accessible by clicking the `6-Gate Audit` button on any ticker row in the Screener, Portfolio, or Earnings Center tabs:

### 15.1 The 6 Immutable Pre-Purchase Gates
1. **Gate 1: Circle of Competence**: Evaluates business model intelligibility, revenue predictability, and high ROCE ($> 15\%$).
2. **Gate 2: Enduring Moat & Pricing Power**: Requires Gross Margin $\ge 40.0\%$ with stable or expanding trajectory over consecutive quarters.
3. **Gate 3: Capital Allocation & Conservative Balance Sheet**: Requires Piotroski F-Score $\ge 5/9$, low leverage ($D/E < 1.5\times$), and robust interest coverage.
4. **Gate 4: Honest & Competent Management**: Annual share dilution capped at $\le 2.0\%$ YoY, disciplined capital return, and high insider alignment.
5. **Gate 5: Reverse DCF & Margin of Safety**: Solves for market-implied FCF growth hurdle $g^*$. Current market price must trade at a $\ge 20\%$ discount to intrinsic DCF fair value under conservative baseline assumptions.
6. **Gate 6: Forensic Accounting & Red Flag Audit**:
   - **Beneish M-Score ($M < -1.78$ Pass)**:
     $$M = -4.84 + 0.920 \cdot \text{DSRI} + 0.528 \cdot \text{GMI} + 0.404 \cdot \text{AQI} + 0.892 \cdot \text{SGI} + 0.115 \cdot \text{DEPI} - 0.172 \cdot \text{SGAI} + 4.037 \cdot \text{TATA} + 0.0327 \cdot \text{LVGI}$$
     - *AQI Standard*: $\text{AQI} = 1 - \frac{\text{Current Assets} + \text{PP\&E}}{\text{Total Assets}}$. Gross Profit is never subtracted from balance sheet assets.
     - *Hyper-Growth Cap*: For companies with expanding gross margins ($\text{GMI} \le 1.05$), $\text{SGI}$ contribution is capped at $1.25$ to avoid penalizing legitimate hyper-growth.
     - *Sloan Accruals*: Evaluated using the **4-quarter rolling mean** ($\le 8.0\%$ safe) to eliminate single-quarter working capital timing distortions.
     - *Confluence Gating*: A borderline M-score ($M \in [-1.78, -1.49]$) triggers `🟡 WARN / CAUTION` with $0.5\times$ sizing. A fatal $0.0\times$ veto strictly requires **multi-signal confluence** ($M > -1.49$ conjoined with severe accounting flags like Sloan $> 8\%$ or Piotroski $F \le 3$, or structural insolvency $F \le 2$).

### 15.2 Sizing Verdicts & Case Studies
- **🟢 PASS (6/6 Gates Cleared)**: Full Conviction ($1.0\times$ Sizing).
- **🟡 CAUTION / GRAY ZONE (5/6 Gates Cleared, Gate 6 Warn)**: $0.5\times$ Position Sizing (e.g. `NVDA` with M-score -1.51 and safe 5.63% rolling Sloan accruals).
- **🟡 SPECULATIVE (4/6 Gates Cleared)**: $0.25\times$ Allocation.
- **🔴 FATAL HARD VETO (Multi-Signal Confluence or Solvency Failure)**: $0.0\times$ Sizing (e.g. `CRML` with $0.0 revenue, -$145M net loss, Piotroski $F=2/9$, and 79.9% dilution).
- **⚪ PENDING AUDIT (NO DATA)**: Tickers with un-cached SEC filings cleanly display pending status cards, preventing premature approvals.

---

## 16. Multi-Session Anchored RVOL & 4 Cadence Workflows

### 16.1 Deterministic Session RVOL Anchoring
Relative Volume ($\text{RVOL}$) at any active time $T$ is computed strictly as:
$$\text{RVOL}(T) = \frac{\text{CumVol}_{\text{anchor} \to T}}{\overline{\text{CumVol}}_{20\text{d}, \text{anchor} \to T}}$$
- **Premarket (00:00 – 09:30 EST)**: Anchor is **Midnight – 00:00 AM EST**.
- **Regular Hours (09:30 – 16:30 EST)**: Anchor is **09:30 AM EST**.
- **After-Hours (16:30 – 23:59:59 EST Mon–Thu)**: Anchor is **04:30 PM EST**.
- **Weekend (Friday 16:30 through Sunday 23:59:59 EST)**: Anchor is **Friday 04:30 PM EST**.

### 16.2 Cadence Workflows Reflected in the UI
The platform reflects 4 structured daily workflows across the UI and automation daemon:
1. **Premarket Session (08:00 – 09:15 EST)**:
   - *UI Surface*: Top Macro V3 Bar & Screener Tab (anchored to 00:00 EST).
   - *Engine*: Checks overnight macro gaps, evaluates News Pulse stealth sentry on portfolio holdings, and ranks breakout setups.
2. **Opening Bell Execution (09:30 – 10:15 EST)**:
   - *UI Surface*: Trade Execution Desk (Actions Tab).
   - *Engine*: Prioritizes 5-minute ORB breakouts, monitors rapid volume expansion against 09:30 anchor, and stages Tier 1/2 bracket tickets.
3. **Mid-Day Monitoring (12:00 – 13:00 EST)**:
   - *UI Surface*: Portfolio Manager & Risk Governance (Tab 7).
   - *Engine*: Verifies VWAP support, monitors intraday drawdown circuit breakers, and audits intra-day thesis drift.
4. **End-of-Day Reconciliation & Lake Synchronization (16:00 – 17:30 EST)**:
   - *UI Surface*: Earnings Center & Alpha Attribution Lake (Tabs 5 & 6).
   - *Engine*: Reconciles closing NAV, commits snapshots to DuckDB lake, audits fleet-wide Thesis Health scores, and triggers hands-off earnings reviews for after-hours reporters.

