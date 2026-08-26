# Walkthrough: Institutional Real-Time Intelligence Screener

## Living Document Version History

| Version | Date | Changes & Enhancements | Author / Status |
|---|---|---|---|
| **v1.0.0** | 2026-08-20 | Initial automated premarket screening engine @ 8:45 AM EST. Dual Day & Swing trading watchlists. Macro Regime (01_macro-regime.md) parser. | Production |
| **v2.0.0** | 2026-08-21 | Added 45-Day Aggregated Institutional Options Structure (GEX, Call/Put Walls, Whale Flow Drawers) and 100% Dynamic Analyst Actions discovery. Fixed pagination. | Production |
| **v3.0.0** | 2026-08-22 | 24/7 Real-Time Screener, Multi-session RVOL & breakout price gatekeeping, NLP Catalyst Intelligence, 17 columns, sorting. | Production |
| **v3.1.0** | 2026-08-22 | **Cross-Asset Futures, Market Breadth Internals & Multi-Asset Targets**: Integrated ES, NQ, Gold, Bitcoin quotes, live universe-wide Breadth Gauges (A/D %, 52W NH/NL, % > SMA50/200), and 4-asset allocation model ($E + G + B + C = 100\%$). | Production |
| **v3.2.0** | 2026-08-24 | **Options Vol/OI, ATM IV, IV Rank, Net Dollar Premium & TradeAlgo Enhancements**: Added 14-column 45D Options Structure grid with default Vol/OI descending sort, ATM IV with Black-Scholes solver fallback, session IV Chg, 30D IV Rank percentile (0-100%), Net Dollar Flow ($), Underlying Stock Price (% Chg), and enriched Whale Sweeps drawers. | Production |
| **v3.3.0** | 2026-08-24 | **Triangulated Return Metrics (% Chg, Gap %, % Open) & Earnings % Chg**: Added dedicated `% Chg` (Total daily % change from previous close) column across all Watchlist Grid view modes and added real-time `% Chg` to the Finviz-style Earnings Calendar widget. | Production |
| **v3.4.0** | 2026-08-24 | **Interactive Return & VWAP Search Filters**: Integrated dynamic `% Chg`, `% Open`, and `% VWAP` dropdown controls to the search criteria bar with client-side real-time filtering and localStorage state persistence. | Production |
| **v3.5.0** | 2026-08-24 | **Enhanced Gap/VWAP/SMA Criteria & Multi-Vector Universe Ingestion**: Added Flat/No Gaps and Gap Down (-1%, -3%, -8%) to Gap% dropdown; Added fresh Cross Over & Cross Under to %VWAP; Added SMA20, SMA50, SMA200 dropdowns with Cross Over, Cross Under, Greater Than, Less Than; Upgraded scanner to multi-vector ingestion pool (500+ candidates) across Volume, RVOL, and Gainers. | Production |
| **v3.6.0** | 2026-08-24 | **VWAP STD Bands, Flow/Bias Momentum Filter, Catalyst Timestamps & Macro Regime Correction**: Added $\pm 1\sigma, \pm 2\sigma$ VWAP standard deviation bands; Added dedicated Options Flow/Bias momentum filter; Added live catalyst date/time stamps to Catalyst column & drawers with 1.0★ baseline for no news; Overhauled macro regime composite scoring with multi-factor weighting (ES/NQ 30%, VIX 25%, Breadth 25%, Yield/Oil 20%) and strict $\le 0.95\text{x}$ multiplier ceiling when futures/markets pull back. | Production |
| **v4.0.0** | 2026-08-24 | **Institutional Portfolio Manager, Fidelity Brokerage CSV Sync, Championship ATR-Parity Sizing & 4D Macro Radar**: Created full-featured Portfolio Manager with NAV ($336.87K), liquid cash ($70.83K, 21.0%), and 73 active holdings. Integrated Fidelity CSV drag-and-drop & paste ingestion modal. Added Championship ATR-Parity Position Sizing engine (`⚡ Size & Add`) calculating exact shares, capital required, and dollar risk adjusted for Macro Multiplier and Options Flow Conviction Score. Visualized 4D Macro Regime Radar state space across Liquidity, Growth, Volatility, and Breadth. | Production |
| **v4.1.0** | 2026-08-24 | **Portfolio Manager Full Parity (3 View Modes, Multi-Factor Filters & 4-Quadrant Drawers)**: Upgraded Portfolio Manager to 100% full parity with Screener. Added 3 view mode tabs (`Core Overview (14)`, `Technical & MAs (17)`, `Options Structure & Walls (17)`). Added multi-factor filter panel with breakout checkboxes, `% Chg`, `Gap %`, `% Open`, `% VWAP` ($\pm 1\sigma, \pm 2\sigma$), `Total% P&L` (9 buckets from $<-20\%$ to $>+100\%$), `Weight%` (8 buckets), `Flow/Bias`, `SMA20/50/200`, `Catalyst`, `Min RVOL`, `Min Score`, `Sector`, `Asset Type`, and `Strategy Tag`. Added 4-card matrix expandable drawers with live underlying intelligence mapping. | Production |
| **v4.2.0** | 2026-08-24 | **TradingView Session % Change Integration, High-Momentum Candidate Prioritization & ETF Network Optimization**: Integrated official TradingView `change` and `change_from_open` fields. Expanded multi-vector prioritization to rank across `% Change`, `Gap %`, `RVOL`, and volume, ensuring morning winners (such as `BMNR +5.74%`) are included and evaluated (410 total candidates). Increased HTTPAdapter connection pool to 60, bypassed slow Finviz quote scraping, and added automatic ETF bypass eliminating yfinance 404 fundamentals errors. | Production |
| **v4.3.0** | 2026-08-24 | **Break Up/Down Multi-Select Parity, Bucket Standardized % Chg & % Open Filters & Premarket Low Breakdowns**: Verified `% Chg` formula for regular hours ($\frac{\text{Current Price} - \text{Previous Close}}{\text{Previous Close}} \times 100\%$). Refined Break Up / Down dropdowns across both Watchlist and Portfolio screens to 6 choices: `> Last Week High`, `> Last Day High`, `> Premarket High`, `< Premarket Low`, `< Last Week Low`, `< Last Day Low` (all unchecked by default). Integrated `premarket_low` and `breakdown_pm_low`. Standardized `% Chg` and `% Open` dropdowns to match Total P&L% buckets (9 ranges: $<-20\%$ to $>+100\%$) across both screens. | Production |
| **v4.3.1** | 2026-08-24 | **Refined Top Momentum Thresholds & Granular 0-5% / 5-10% Buckets**: Enhanced `% Chg`, `% Open`, and `Total P&L %` dropdowns on both screens with `> +3.0%` and `< -3.0%` at the top, replaced `0-10%` with fine-grained `0% to 5%` and `5% to 10%` buckets, and updated client-side range filtering. | Active Standard |

---

## 1. Verified Core Features & Architecture

### ⚡ 1. 24/7 Real-Time Multi-Session Engine, `% Chg` & `Gap %` Formulas
- **`% Chg` (Session-Independent Performance Metric)**:
  - Calculated as:
    $$\text{\% Chg} = \frac{\text{Current Close} - \text{Previous Close}}{\text{Previous Close}} \times 100\%$$
  - Applies **universally** across all sessions (Premarket, Regular Market Hours, Postmarket / After-Hours, and Weekends), exactly matching TradingView's official `change` metric.
- **`Gap %` (Session-Specific Overnight / Intraday Gap Metric)**:
  - **Premarket**:
    $$\text{Gap \%} = \frac{\text{Premarket Price} - \text{Previous Close}}{\text{Previous Close}} \times 100\%$$
  - **Regular Hours**:
    $$\text{Gap \%} = \frac{\text{Premarket Close / Open} - \text{Previous Close}}{\text{Previous Close}} \times 100\%$$
  - **After-Hours / Weekend**:
    $$\text{Gap \%} = \frac{\text{Current Postmarket Price} - \text{Regular Close}}{\text{Regular Close}} \times 100\%$$
- **Continuous Live Streaming**: Run with `--realtime` / `-r` to auto-refresh the dashboard every 60 seconds with rate-limiting backoff.
- **Session-Specific Price Gatekeeping**:
  - **Premarket (04:00 - 09:30 EST)**: Requires `Price > Yesterday's High`. RVOL anchored to `04:00 EST`.
  - **Regular Market Hours (09:30 - 16:00 EST)**: Requires `Price > Yesterday's High` **AND** `Price >= Premarket High`. RVOL anchored to `09:30 EST`.
  - **After-Hours (16:00 - 20:00 EST) & Weekend**: Requires `Price >= Latest Business Day's High`. RVOL anchored to `16:00 EST`.

### 🧠 2. Catalyst Intelligence & NLP Scoring
- **Multi-Source Arbitration**: Aggregates news streams across Yahoo Finance, Finviz, and SEC filings.
- **Institutional 1★-5★ Scale**: Major earnings beats / buyouts (5★), FDA / mega-contracts (4★), partnerships / product launches (3★), analyst upgrades / index inclusions (2.5★), sector sympathy (2★).
- **Strict Disqualification**: Any stock with catalyst score $< 2.0★$ or negative catalysts (dilution, offerings, CFO resignation) is disqualified from the dashboard.

### 🌟 3. Institutional 5-Star Setup Quality Score
- Calculates an objective quality grade from **1.0★ to 5.0★** combining:
  - Catalyst Impact (0 – 1.5★)
  - RVOL Multiplier (0 – 1.0★)
  - Technical Breakout Magnitude (0 – 1.0★)
  - Options Gamma Skew & Headroom (0 – 0.75★)
  - Macro Regime Alignment (0 – 0.75★)

### 📊 4. Watchlist Table & Level % Distances (17 Columns)
- All price levels (**Call Wall**, **Put Wall**, **Gamma Flip**, **Yesterday High**, **Premarket High**) display the absolute price and percentage distance from current price (e.g. `$105.00 (+4.8%)` / `$92.00 (-8.2%)`).
- Table displays: `Ticker`, `Setup Score`, `Price`, `Gap %`, `% from Open`, `RVOL`, `Last Day High`, `Premarket High`, `Sector`, `Industry`, `Catalyst`, `Analyst Rating`, `Call Wall`, `Put Wall`, `Gamma Flip`, `Gamma Skew`, `P/C Ratio`.

### 🔀 5. Interactive Column Header Sorting
- Clicking any column header toggles **Ascending / Descending** sorting (`▲` / `▼`) client-side across numbers, percentages, dollar values, and text strings without reloading the page.

### 🌐 6. Cross-Asset Futures, Breadth & Multi-Asset Allocation Model
- **Major Futures**: E-mini S&P 500 (`ES=F`), Nasdaq 100 (`NQ=F`), Gold (`GC=F`), and Bitcoin (`BTC-USD`) real-time quotes and 24h % changes.
- **Market Breadth Internals**: Advancing / Declining %, 52-Week New Highs vs Lows, % of stocks above 50-day SMA, and % above 200-day SMA.
- **Multi-Asset Allocation Targets**: Dynamically balances `Equity Target` ($40\%-90\%$), `Gold Target` ($3\%-12\%$), `Bitcoin Target` ($0\%-6\%$), and `Cash Target` ($5\%-40\%$) constrained to $100\%$ total portfolio equity.

### ⚡ 7. Institutional Options Structure & Gamma (45-Day Aggregate) + TradeAlgo Engine
- **14-Column Aggregated Table**: `Ticker`, `Price (% Chg)`, `Vol/OI Ratio` (**Default sorted DESC**), `ATM IV`, `IV Chg`, `IV Rank (0-100%)`, `Net Premium Flow ($)`, `Call Wall (Magnet)`, `Put Wall (Floor)`, `Gamma Flip Level`, `P/C Ratio`, `Gamma Skew`, `45D Total Volume`, `Whale Flow Details`.
- **Black-Scholes Fallback Solver**: Analytical root-finding engine solves exact IV during premarket/after-hours when market-maker quotes are offline.
- **Session-over-Session IV Tracking (`options_iv_cache.json`)**: Calculates exact 1-day basis point changes in ATM IV and 52-week IV Rank percentile.
- **Top Whale Sweeps Drawer**: Displays contracts with $\ge \$500\text{K}$ premium or $\text{Vol/OI} \ge 3.0\text{x}$ with DTE, Contract IV, Vol/OI ratio, notional premium, order type, and directional conviction.

### 💼 8. Institutional Portfolio Manager & Full Screener Parity
- **Portfolio Book Tab**: Instant toggle between `🚀 Screener & Alpha Flow`, `💼 Portfolio Manager (Live Book)`, and `📊 4D Macro & Allocations`.
- **Three View Mode Tabs**: `Core Overview (14 Cols)`, `Technical & MAs (17 Cols)`, and `Options Structure & Walls (17 Cols)`.
- **Multi-Factor Filter Bar**: Comprehensive filtering across Break Up / Down multi-select dropdown, `% Chg`, `Gap %`, `% Open`, `% VWAP`, `Total% P&L` (9 buckets), `Weight%` (8 buckets), `Flow/Bias`, `SMA20/50/200`, `Catalyst`, `Min RVOL`, `Min Score`, `Sector`, `Asset Type`, and `Strategy Tag`.
- **Break Up / Break Down Multi-Select Dropdown**: 8 independent interactive checkboxes (`> Last Week High`, `> Last Day High`, `> Premarket High`, `< Last Week High`, `< Last Day High`, `< Premarket High`, `< Last Week Low`, `< Last Day Low`), default all unchecked.
- **Cleaned Table Columns**: Standardized `% Chg` (calculated from previous close) and `Gap %`, and removed redundant `Today %` column with 34 active data columns.
- **Interactive Sorting & Pagination**: Sort any column ascending/descending and paginate with page size controls (15, 25, 50, All).
- **Expandable 4-Quadrant Row Drawers**: Detailed breakdown containing Trend Matrix, Options Gamma Matrix, Catalyst Intelligence, and Portfolio Risk Management & Sizing.
- **Fidelity Brokerage Ingestion & Live Analytics**: Real-time parsing of Fidelity CSV exports with automatic underlying ticker extraction for options contracts, enriched with live technicals, earnings dates, and options walls.
- **Dynamic ATR-Parity Sizing Modal (`⚡ Size & Add`)**: Calculates exact shares, dollar risk ($), total required capital ($), and portfolio weight (%) tailored to user's real NAV and macro risk multiplier + options conviction boost.
- **4D Quantitative Macro Regime Radar**: Displays 4 orthogonal state-space meters (Liquidity & Yields, Growth vs Inflation, Volatility & Credit, Breadth & Futures).

---

## 2. CLI Execution Modes

```powershell
# 1. Run single real-time snapshot and open latest_report.html in default browser
python run_screener.py

# 2. Run single snapshot in terminal-only mode without opening browser
python run_screener.py --no-browser

# 3. Run continuous live streaming mode (auto-refreshes every 60s during trading hours)
python run_screener.py --realtime

# 4. Run headlessly (for Task Scheduler / background tasks)
python run_screener.py --headless

# 5. Run full automated unit test suite
python -m unittest tests/test_suite.py
```
