# Institutional Real-Time Intelligence Screener: Living Functional Specification

**Document Version**: `3.0.0`  
**Last Updated**: `August 24, 2026`  
**Standard**: Institutional Multi-Session Day Trading, Macro Assessment & Quantitative Execution

---

## 1. System Objective & Operating Philosophy

The **Institutional Real-Time Intelligence Screener** provides hedge-fund-grade premarket, regular-hours, and postmarket intelligence for active US equity traders. 
The system operates under three unbreakable engineering laws:
1. **Zero Fake Data / Zero Random Numbers**: Every metric is ingested live from public market feeds (Finviz, Yahoo Finance, Federal Reserve, CBOE, CME, TradingView).
2. **Session-Specific Reference Anchors & Criteria**: Prices, gap percentages, and breakout reference levels dynamically switch based on the active market session (Premarket, Regular, Postmarket / Weekend).
3. **Multi-Factor Quantitative Setup Scoring**: Every trade setup is rated on a 1.0★ to 5.0★ institutional scale using weighted composite mathematics.

---

## 2. Universal Ingestion Standards vs Interactive Client-Side Filters

### 2.1 Backend Ingestion Standards (Broad Universe Pool)
The backend pipeline ingests and enriches a broad multi-vector universe (500+ candidates) of liquid US equity candidates from TradingView across top volume leaders, top relative volume (RVOL) momentum runners, and top session % gainers using uniform baseline standards:
* **Market Capitalization**: $\ge \$1.0\text{B}$
* **Average 30-Day Volume**: $\ge 500\text{K}$ (or Current Session Volume $\ge 500\text{K}$)
* **Minimum Price**: $\ge \$1.50$
* **Ingestion Breadth**: Multi-vector queries union Volume + RVOL + Gainers to ensure morning momentum runners are never crowded out during midday volume rotation.

### 2.2 Frontend Institutional Default Filter Controls
The web interface features an interactive multi-factor filter bar with pre-selected institutional defaults that users can adjust or remove in real time without backend re-runs:
* ☑️ **`> Last Day High`**: Breakout above previous regular trading day high (Default: **ON**).
* ☑️ **`> Premarket High`**: Breakout above session premarket high during regular hours (Default: **ON**).
* 📈 **`% Chg`**: Total daily change vs previous close (Default: `All % Chg`; Options: `Green Only (>0%)`, `≥ +1%`, `≥ +2%`, `≥ +3%`, `≥ +5%`, `≥ +10%`, `≥ +15%`, `Red Only (<0%)`).
* 📊 **`Gap %`**: Overnight opening jump (Default: `≥ +3.0%`; Options: `All Gaps`, `No Gaps (Flat < 1.0%)`, `≥ +1%`, `≥ +2%`, `≥ +5%`, `≥ +8%`, `Gap Down ≤ -1%`, `Gap Down ≤ -3%`, `Gap Down ≤ -8%`).
* 🚀 **`% Open`**: Intraday extension from 9:30 AM open (Default: `All % Open`; Options: `Above Open (>0%)`, `≥ +1%`, `≥ +2%`, `≥ +3%`, `≥ +5%`, `≥ +10%`, `Below Open (<0%)`).
* ⚡ **`% VWAP`**: Intraday distance from volume-weighted average price (Default: `All VWAP Dist`; Options: `Above VWAP (>0%)`, `⚡ Cross Over (Bullish Cross)`, `🔻 Cross Under (Bearish Cross)`, `≥ +1 STD VWAP (+1σ Upper Band)`, `≥ +2 STD VWAP (+2σ Extended)`, `≤ -1 STD VWAP (-1σ Lower Band)`, `≤ -2 STD VWAP (-2σ Oversold)`, `≥ +1%`, `≥ +2%`, `≥ +3%`, `≥ +5%`, `Below VWAP (<0%)`).
* 🎯 **`Flow / Bias`**: Institutional options flow sentiment & momentum filter (Default: `All Flow Bias`; Options: `🟢 Bullish Flow (Long Gamma, P/C < 0.70)`, `🔴 Bearish Flow (Put Hedge, P/C > 1.00)`, `🐳 Whale Sweeps Active`, `⚡ Bullish Momentum (> VWAP & Bullish Flow)`, `🔻 Bearish Momentum (< VWAP & Bearish Flow)`).
* 📉 **`SMA20`**: 20-Day Simple Moving Average position and dynamics (Default: `All SMA20`; Options: `Above SMA20`, `⚡ Cross Over SMA20`, `🔻 Cross Under SMA20`, `≥ +1%`, `≥ +3%`, `Below SMA20`).
* 📉 **`SMA50`**: 50-Day Simple Moving Average position and dynamics (Default: `All SMA50`; Options: `Above SMA50`, `⚡ Cross Over SMA50`, `🔻 Cross Under SMA50`, `≥ +1%`, `≥ +3%`, `Below SMA50`).
* 📉 **`SMA200`**: 200-Day Simple Moving Average position and dynamics (Default: `All SMA200`; Options: `Above SMA200 (Bullish Trend)`, `⚡ Cross Over SMA200`, `🔻 Cross Under SMA200`, `≥ +1%`, `≥ +3%`, `Below SMA200 (Bearish Trend)`).
* 🌟 **`Catalyst Rating`**: $\ge 2.0★$ Positive Only (Default: **Selected**; Options: `All News`, `≥ 2★`, `≥ 3★`, `≥ 4★`, `5★`). Stocks without news receive 1.0★ baseline. Date/time stamped on all entries.
* 📈 **`Relative Volume (RVOL)`**: $\ge 1.50\text{x}$ (Default: **Selected**; Options: `Any RVOL`, `≥ 1.0x`, `≥ 1.5x`, `≥ 2.0x`, `≥ 3.0x`).
* 🏆 **`Min Setup Score`**: $\ge 2.5★$ (Default: **Selected**; Options: `Any Score`, `≥ 2.5★`, `≥ 3.0★`, `≥ 3.5★`, `≥ 4.0★`).
* 🏢 **`Sector Dropdown`**: Substring-matched sector filter across screened universe.
* ⚡ **`Institutional Defaults Button`**: One-click reset to strict institutional gatekeeping.
* 🌐 **`Show All Candidates Button`**: One-click uncheck of all filters to reveal the entire screened universe.

### 2.3 Catalyst Freshness Window & Classification Rules
To avoid using stale background events as active day-trading catalysts:
* **Freshness Window**:
  * **Tuesday – Friday**: News articles and earnings releases must be published **Today or Yesterday (within 24–48 hours)**.
  * **Monday Pre-Market & Weekends**: News articles and reports must be published **Friday (last regular trading session), Saturday, Sunday, or Monday (within 72–96 hours)**.
* **Outdated News (> 3–4 Days Old)**:
  * Any news published before the freshness cutoff window is automatically disqualified from Tier 1 ($4.5★ - 5.0★$) classification.
  * If no fresh company news exists within 48–72h, elevated volume/gap moves are classified as **`[Sector Sympathy]` ($2.0★$)** (*"Moving on sector momentum (No fresh company news in past 48h)"*).

---

## 3. Session Reference Anchor & Return Decomposition

### 3.1 Return Metrics Decomposition Matrix
During active trading hours, price moves are decomposed into 3 distinct metrics to clearly distinguish overnight positioning from intraday execution:

1. **Total Session % Change (`% Chg`)**:
   $$\text{\% Chg} = \frac{\text{Current Live Price} - \text{Yesterday's Regular Close}}{\text{Yesterday's Regular Close}} \times 100\%$$
   * Measures the full day-over-day price return relative to yesterday's closing bell ($4\text{:00 PM EST}$).
   * Displayed as a primary pill badge (Green/Red) in the **Main Screener Grid**, **Options Flow Table**, and **Earnings Calendar**.

2. **Overnight Opening Gap (`Gap %`)**:
   * **Premarket**: $\frac{\text{Premarket Price} - \text{Yesterday's Close}}{\text{Yesterday's Close}} \times 100\%$
   * **Regular Hours**: $\frac{\text{9:30 AM Open} - \text{Yesterday's Close}}{\text{Yesterday's Close}} \times 100\%$
   * Strictly captures the overnight gap jump at the opening bell.

3. **Intraday Momentum (`% from Open` / `% Open`)**:
   $$\text{\% Open} = \frac{\text{Current Live Price} - \text{9:30 AM Open Price}}{\text{9:30 AM Open Price}} \times 100\%$$
   * Measures true intraday momentum and extension since the $9\text{:30 AM EST}$ opening bell (e.g. if a stock opened $+3.53\%$ and is now trading $+15.20\%$ total, `% Open` is $+11.27\%$).

| Session Type | Active Window (EST) | Price Anchor ($P$) | Total % Chg Formula | Gap % Formula | Breakout High Reference | Gatekeeper Criteria |
|---|---|---|---|---|---|---|
| **PREMARKET** | 04:00 – 09:30 AM EST | `premarket_close` | $\frac{P - \text{Prev Close}}{\text{Prev Close}} \times 100\%$ | $\frac{P - \text{Prev Close}}{\text{Prev Close}} \times 100\%$ | Previous Regular Day High (`high`) | $P > \text{Last High}$, $\text{Gap} \ge 3\%$, $\text{RVOL} \ge 1.5\text{x}$, $\text{Cat} \ge 2★$ (Pos) |
| **REGULAR** | 09:30 AM – 04:00 PM EST | `close` (live last) | $\frac{P - \text{Prev Close}}{\text{Prev Close}} \times 100\%$ | $\frac{\text{Open} - \text{Prev Close}}{\text{Prev Close}} \times 100\%$ | Yesterday High (`high[1]`) AND Premarket High (`premarket_high`) | $P > \text{Last High} \land P \ge \text{PM High}$, $\text{Gap} \ge 3\%$, $\text{RVOL} \ge 1.5\text{x}$, $\text{Cat} \ge 2★$ (Pos) |
| **POSTMARKET / WEEKEND** | 04:00 – 08:00 PM EST & Weekends | `postmarket_close` | $\frac{P - \text{Close}}{\text{Close}} \times 100\%$ | $\frac{P - \text{Close}}{\text{Close}} \times 100\%$ | Friday / Latest Regular High (`high`) | $P \ge \text{Last High}$, $\text{Gap} \ge 3\%$, $\text{RVOL} \ge 1.5\text{x}$, $\text{Cat} \ge 2★$ (Pos) |

---

## 4. Watchlist Grid Presentation & View Modes

To maintain a clean, high-performance interface while providing full depth, the Watchlist grid features **4 View Modes** and an **Expandable Row Detail Accordion Drawer**:

### 4.1 View Modes (Tabs)
1. **🌟 Core View** (Default clean view):
   * Columns: `Ticker`, `Score`, `Price`, `% Chg`, `Gap %`, `% Open`, `RVOL`, `Earnings Date`, `Last High`, `Sector`, `Industry`, `Catalyst`, `Skew`, `P/C`, `Details 🔍`.
2. **📈 Technical & MAs View**:
   * Columns: `Ticker`, `Score`, `Price`, `% Chg`, `Gap %`, `% Open`, `RVOL`, `Earnings Date`, `Last High`, `PM High`, `VWAP`, `SMA5`, `SMA20`, `SMA50`, `SMA200`, `Skew`, `P/C`, `Details 🔍`.
3. **⚡ Options & Gamma View**:
   * Columns: `Ticker`, `Price`, `% Chg`, `Earnings Date`, `Call Wall`, `Put Wall`, `Gamma Flip`, `Skew`, `P/C Ratio`, `Analyst Rating`, `Details 🔍`.
4. **📋 All Columns View (Expanded Matrix)**:
   * Full 25-column comprehensive matrix with horizontal scroll and fixed columns (including separate `Sector` and `Industry` columns, and `Earnings Date`).

### 4.2 Expandable Row Accordion Drawer (3-Column Deep Dive)
Clicking any row or the `🔍 Details` button expands an accordion sub-card with 3 analytical panels:
* **Card 1: Trend & Moving Average Matrix**: Live values and distance percentages for `VWAP`, `5-Day SMA`, `20-Day SMA`, `50-Day SMA`, and `200-Day SMA`.
* **Card 2: Breakout & Options Gamma Matrix**: `Last Day High`, `Premarket High`, `Call Wall (Magnet)`, `Put Wall (Floor)`, `Gamma Flip Level`, and `P/C Ratio / Skew`.
* **Card 3: Catalyst & Analyst Intelligence**: Full clickable headline, NLP classification category, star rating, separate `Sector` and `Industry`, `Upcoming Earnings Date`, analyst revisions, and market cap.

---

## 5. Moving Average & Key Level Distance Formulas

All levels in table columns and drawer cards follow the universal distance formula:

$$\text{Level Distance \%} = \frac{\text{Current Price} - \text{Level}}{\text{Level}} \times 100\%$$

* **Positive (+) Value**: Current price is trading **above** the level (e.g. `BMNR Last High $23.34 (+0.9%)`, `SMA50 $16.65 (+41.4%)`).
* **Negative (-) Value**: Current price is trading **below** the level (e.g. `Call Wall $26.00 (-9.4%)`).

---

## 6. Institutional Options Structure & Gamma (45-Day Aggregate) Protocol

The **Institutional Options Structure & Gamma (45-Day Aggregate)** widget provides dealer positioning and order flow insights across the US equity universe and market bellwethers (`SPY`, `QQQ`, `IWM`).

### 6.1 Core Metric Definitions & Mathematical Formulas

1. **Volume-to-Open Interest Ratio (Vol/OI)**:
   $$\text{Vol/OI Ratio} = \frac{\text{Total 45D Option Volume}}{\text{Total 45D Open Interest}}$$
   * Measures institutional positioning velocity and unusual contract turnover.
   * **Default Grid Sorting**: Table defaults to sorting by **`Vol/OI Ratio` descending** upon load.

2. **At-The-Money (ATM) Implied Volatility & 1-Day Change**:
   $$\text{ATM IV} = \frac{\text{IV}_{\text{ATM Call}} + \text{IV}_{\text{ATM Put}}}{2}$$
   * Target expiration cycle: 15–45 DTE institutional liquidity cycle.
   * Solved analytically via Black-Scholes root-finding if market-maker bid/ask spreads reset outside market hours.
   * **`IV Chg`**: Session-over-session delta ($\Delta \text{IV} = \text{IV}_{\text{Today}} - \text{IV}_{\text{Prior}}$) with green/red color coding.

3. **IV Rank (30-Day / 1-Year Percentile)**:
   $$\text{IV Rank} = \frac{\text{ATM IV} - \text{IV}_{\text{Min}}}{\text{IV}_{\text{Max}} - \text{IV}_{\text{Min}}} \times 100\%$$
   * $\le 30\%$ (Green): Cheap options (ideal for directional long breakouts).
   * $\ge 70\%$ (Red): Expensive options (elevated IV crush risk / favorable for credit spreads).

4. **Net Dollar Premium Flow**:
   $$\text{Net Flow (\$)} = \sum (\text{Call Volume} \times \text{Call Price} \times 100) - \sum (\text{Put Volume} \times \text{Put Price} \times 100)$$
   * Surfaces whether institutional capital is aggressively accumulating net bullish upside exposure or hedging downside put risk.

5. **Underlying Stock % Change**:
   $$\text{Stock \% Chg} = \frac{\text{Current Spot} - \text{Previous Close}}{\text{Previous Close}} \times 100\%$$

6. **Whale Trades Sub-Drawer**:
   * Individual contract level breakdown for orders with Premium $\ge \$500\text{K}$ or $\text{Vol/OI} \ge 3.0\text{x}$ with $\$200\text{K}+$ notional:
   * Attributes: `Contract Strike`, `Expiry (DTE)`, `Vol / OI Ratio`, `Contract IV`, `Notional Premium`, `Order Type (Institutional Sweep vs Whale Trade)`, and `Sentiment`.

---

## 7. Institutional Portfolio Manager, Fidelity CSV Sync & Position Sizing Engine

### 7.1 Real-Time Portfolio Management & Fidelity Brokerage Ingestion
* **Hybrid Dual-Sync Storage**: Ingested holdings and active trading book are maintained simultaneously in client-side `localStorage` and synchronized with backend `data/portfolio.json`.
* **Fidelity CSV Ingestion**: Direct drag-and-drop or text-paste parser for standard Fidelity brokerage exports:
  - Detects and isolates liquid cash holdings (`SPAXX**`, `Pending activity`, money market balances).
  - Classifies stock, ETF, and options contracts (` -PLTR261016P125`, ` -PLTR261016C190`).
  - Computes real-time **Account NAV**, **Liquid Cash Balance & Weight %**, **Total Equity Value**, **Today's Session P&L ($ / %)**, and **Total Unrealized P&L ($ / %)**.

### 7.2 Championship ATR-Parity Position Sizing Engine
Every candidate in the screener and active book features dynamic position sizing calibrated to the user's real portfolio capital:
$$\text{Shares to Buy} = \left\lfloor \frac{\text{Account NAV} \times \text{Risk Budget } (\%)}{\max\big(1.2 \times \text{ATR}_{14\text{m}}, \; |\text{Price} - \text{Stop Level}|\big)} \times \mathbf{M}_{\text{Macro Regime}} \times \mathbf{W}_{\text{Options Conviction}} \right\rfloor$$
* **Macro Regime Multiplier ($\mathbf{M}_{\text{Macro}}$)**: Dynamically scales position exposure between $0.50\text{x}$ (defensive risk-off) and $1.25\text{x}$ (aggressive growth).
* **Options Flow Conviction Score ($\mathbf{W}_{\text{Options Conviction}}$)**: Evaluates Vol/OI, Gamma Skew, ATM IV, Put/Call ratio, and Net Dollar Premium to boost high-conviction trades ($1.25\text{x}$) or contract put-hedged setups ($0.75\text{x}$).

### 7.3 4D Cross-Asset Macro Regime State Space
Renders 4 orthogonal pillar balance meters on the dashboard:
1. **💧 Liquidity & Yields**: Fed Funds, 10Y Yield $\Delta$, 2s10s Curve Slope.
2. **⚡ Growth vs Inflation**: WTI Crude Oil, Energy Cap, TIPS Breakeven.
3. **🛡️ Volatility & Credit**: VIX Volatility Index Level & Term Structure.
4. **📈 Breadth & Futures**: ES/NQ Futures Momentum, Advancing/Declining %, % > SMA200.

### 7.4 Portfolio Manager View Modes, Multi-Factor Filtering & Full Analytics Parity
The Portfolio Manager (Live Book) achieves 100% full analytical parity with the Qualified Watchlist & Universe Screener, featuring:

#### 1. Three Dedicated View Modes:
* **📊 Core Overview (14 Columns)**: `Symbol`, `Score`, `Price`, `Today P&L ($)`, `Today %`, `Total P&L ($)`, `Total %`, `Value ($)`, `Weight %`, `Qty`, `Avg Cost`, `% Chg`, `Gap %`, `% Open`, `RVOL`, `Earnings`, `Last High`, `Sector`, `Industry`, `Catalyst`, `Strategy Tag`, `Actions (⚡ / ✏️ / ❌ / 🔍)`.
* **📈 Technical & MAs (17 Columns)**: `Symbol`, `Score`, `Price`, `Today P&L ($)`, `Today %`, `Total P&L ($)`, `Total %`, `Value ($)`, `Weight %`, `Qty`, `Avg Cost`, `% Chg`, `Gap %`, `% Open`, `RVOL`, `Earnings`, `Last High`, `PM High`, `VWAP`, `SMA5`, `SMA20`, `SMA50`, `SMA200`, `Actions`.
* **🎯 Options Structure & Walls (17 Columns)**: `Symbol`, `Score`, `Price`, `Today P&L ($)`, `Today %`, `Total P&L ($)`, `Total %`, `Value ($)`, `Weight %`, `Qty`, `Avg Cost`, `Call Wall`, `Put Wall`, `Gamma Flip`, `Vol/OI`, `ATM IV`, `Skew`, `P/C`, `Analyst`, `Actions`.

#### 2. Multi-Factor Filter Panel:
* **Breakout Checkboxes**: `> Last Day High`, `> Premarket High`.
* **Intraday Metrics**: `% Chg` (All, POS, $\ge 1\%$, $2\%$, $3\%$, $5\%$, $10\%$, $15\%$, NEG), `Gap %` (All, No Gaps $<1\%$, $+1\%$, $+2\%$, $+3\%$, $+5\%$, $+8\%$, Gap Down $\le -1\%$, $-3\%$, $-8\%$), `% Open` (All, POS, $\ge 1\%$, $2\%$, $3\%$, $5\%$, $10\%$, NEG).
* **VWAP & Standard Deviation Bands**: `% VWAP` (All, POS, Cross Over ⚡, Cross Under 🔻, $\ge +1\sigma$ Upper Band, $\ge +2\sigma$ Extended, $\le -1\sigma$ Lower Band, $\le -2\sigma$ Oversold, $\ge +1\%$, $+2\%$, $+3\%$, $+5\%$, NEG).
* **Total P&L % Filter**: `All Total %`, `<-20%` (Deep Underwater), `-20% to -10%`, `-10% to -5%`, `-5% to 0%`, `0% to +10%`, `+10% to +20%`, `+20% to +50%`, `+50% to +100%`, `> +100%` (Multibaggers).
* **Weight % Filter**: `All Weights`, `≥ 10.0%` (Core Pillar), `≥ 5.0%`, `≥ 3.0%`, `≥ 1.0%`, `< 1.0%` (Starter / Small), `1.0% - 3.0%`, `3.0% - 5.0%`, `5.0% - 10.0%`.
* **Flow & Bias**: `Bullish Flow` (Long Gamma, P/C $< 0.70$), `Bearish Flow` (Put Hedge, P/C $> 1.00$), `Whale Sweeps Active`, `Bullish Momentum` ($>\text{VWAP}$ & Bull Flow), `Bearish Momentum` ($<\text{VWAP}$ & Bear Flow).
* **Moving Averages (SMA20, SMA50, SMA200)**: `Above (> SMA)`, `Cross Over (XO)`, `Cross Under (XU)`, `+1.0% above`, `+3.0% above`, `Below (< SMA)`.
* **Setup Criteria**: `Catalyst` ($\ge 2.0\star$ to $5.0\star$), `Min RVOL` ($\ge 1.0\text{x}$ to $3.0\text{x}$), `Min Score` ($\ge 2.5\star$ to $4.0\star$), `Sector` (All active universe/portfolio sectors), `Asset Type` (`All Assets`, `Stocks & ETFs`, `Options Contracts`), and `Strategy Tag` (`Core Long Holding`, `Tactical Momentum`, `Options Hedge / Income`, etc.).
* **Quick Presets**: `⚡ Institutional Defaults`, `🌐 Show All Positions`, and `💾 Auto-Saved` persistence in `localStorage`.

#### 3. Expandable 4-Quadrant Row Drawers:
* **Card 1: 📈 Trend & Moving Average Matrix**: Live session VWAP, 5-Day SMA, 20-Day SMA, 50-Day SMA, and 200-Day SMA distance percentages.
* **Card 2: 🎯 Institutional Options Gamma & Sizing**: Gamma Skew, Flow Conviction Badge, Call Wall, Put Wall, Gamma Flip Level, Vol/OI, P/C Ratio, ATM IV, and Net Dollar Premium Flow.
* **Card 3: 📰 Catalyst & Analyst Intelligence**: Full clickable headline, NLP classification category, star rating, separate Sector and Industry, Upcoming Earnings Date, and Analyst Revisions.
* **Card 4: 💼 Portfolio Position & Risk Sizing**: Holding Quantity, Average Cost, Total Cost Basis, Current Value, Weight %, Today Session P&L ($ / %), Total Unrealized P&L ($ / %), Stop Loss / Target Price, Strategy Tag, and Trade Notes.


