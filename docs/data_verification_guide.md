# Manual Data Verification Guide
 
## Living Document Version History

| Version | Date | Changes & Enhancements | Author / Status |
|---|---|---|---|
| **v1.0.0** | 2026-08-20 | Initial manual verification guide for Premarket & Macro feeds. | Production |
| **v2.0.0** | 2026-08-21 | Added verification steps for 45-Day Options GEX, Put/Call Walls, and Whale Sweeps. | Production |
| **v3.1.0** | 2026-08-22 | Added verification for E-mini ES, NQ, Gold, Bitcoin, Market Breadth (A/D %, NH/NL, SMA50/200), and 4-asset portfolio targets. | Production |
| **v4.0.0** | 2026-09-04 | Added verification procedures for DuckDB Alpha Attribution Lake (`data/attribution_lake.duckdb`), Brinson-Fachler Factor Attribution (Skill 08), forward incremental fills toggle & manual override, and parameter auto-tuning safety bounds [0.50x, 1.35x]. | Production |
| **v5.0.0** | 2026-09-05 | Added verification steps for Paper Trading Simulator (`data/paper_trading.duckdb`), Alpaca REST API gateway, intraday drawdown circuit breakers (-1.0%, -2.0%, -3.0%), 10,000-path Monte Carlo forward cones, and 6 crisis historical replays in Tab 7. | Production |
| **v6.0.0** | 2026-09-22 | Phase 9-11 Institutional v2.0 Release: Added verification procedures for Buffett 6-Gate Pre-Purchase Audit, 4-Master Consensus Desk, Beneish M-Score & Sloan Accrual Confluence Veto, Depth4 Causal Cascades, Bottleneck Hunter ($P/S \le 30\times$), and Multi-Session RVOL Anchor verification. | Active Standard |

---

## 1. Widget-by-Widget Verification Sources

| Widget / Data Point | Primary Public Web Source | Direct URL / Path | What to Check & Compare |
|---|---|---|---|
| **Fed Funds Rate (EFFR)** | Federal Reserve Bank of New York | [NY Fed Reference Rates](https://markets.newyorkfed.org/api/rates/all/latest.json) or [NY Fed Home](https://www.newyorkfed.org/markets/reference-rates/effr) | Look for `EFFR` (Effective Federal Funds Rate, e.g. 3.63%) and Target Band (e.g. 3.50%-3.75%). |
| **10-Year Treasury Yield** | CNBC / Yahoo Finance / CBOE | [Yahoo Finance ^TNX](https://finance.yahoo.com/quote/%5ETNX) or [CNBC US10Y](https://www.cnbc.com/quotes/US10Y) | Compare live index yield (e.g. 4.65%) and 1-day net change. |
| **CBOE Volatility Index (VIX)** | CBOE / Yahoo Finance | [Yahoo Finance ^VIX](https://finance.yahoo.com/quote/%5EVIX) or [CBOE VIX](https://www.cboe.com/tradable_products/vix/) | Compare live VIX reading (e.g. 14.89) and net change. |
| **WTI & Brent Crude Oil** | NYMEX / ICE via Yahoo Finance | [Yahoo WTI CL=F](https://finance.yahoo.com/quote/CL=F) and [Yahoo Brent BZ=F](https://finance.yahoo.com/quote/BZ=F) | Compare active front-month crude contracts and 1-day dollar changes. |
| **2s10s Yield Curve** | US Treasury / Yahoo Finance | [Yahoo 13-Week ^IRX](https://finance.yahoo.com/quote/%5EIRX) vs [^TNX](https://finance.yahoo.com/quote/%5ETNX) | Difference between 10Y Yield (`^TNX`) and Short-Term Rate (`^IRX`). |
| **Futures (ES=F & NQ=F)** | CME via Yahoo Finance / TradingView | [Yahoo ES=F](https://finance.yahoo.com/quote/ES=F) and [Yahoo NQ=F](https://finance.yahoo.com/quote/NQ=F) | Compare live front-month contract price and 24h % change. |
| **Gold Futures (GC=F)** | COMEX via Yahoo Finance | [Yahoo GC=F](https://finance.yahoo.com/quote/GC=F) | Compare live Gold contract price and 24h % change. |
| **Bitcoin (BTC-USD)** | CoinMarketCap / Yahoo Finance | [Yahoo BTC-USD](https://finance.yahoo.com/quote/BTC-USD) | Compare live 24/7 Bitcoin price and % change. |
| **Market Breadth Internals** | TradingView Screener / Finviz | [TradingView Screener](https://www.tradingview.com/screener/) | Compare Adv/Decl % ratio, Net 52W Highs, % > SMA50, and % > SMA200. |
| **Qualified Watchlist Tickers** | TradingView Screener / Finviz | [TradingView Screener](https://www.tradingview.com/screener/) or [Finviz Top Gainers](https://finviz.com/screener.ashx?v=111&s=ta_topgainers) | Verify Ticker, Real-Time Price, Gap % vs Prev Close, Market Cap $\ge \$1.0\text{B}$, and Breakout Level (Price > Yest High / Premarket High). |
| **Institutional Setup Score (1★-5★)** | Setup Scorer Algorithm | Code verification / Table column | Verify composite scoring based on Catalyst (0-1.5★), RVOL (0-1.0★), Breakout (0-1.0★), Gamma (0-0.75★), Macro (0-0.75★). |
| **Multi-Session RVOL at Time T** | TradingView / Thinkorswim / Primary SEC | [TradingView 5m Chart](https://www.tradingview.com/chart/) | Compute cumulative volume strictly since anchor time up to current time $T$ divided by the 20-day historical average cumulative volume up to that exact same time $T$. Anchors: **Midnight 00:00 AM EST** (Premarket), **09:30 AM EST** (Regular), **04:30 PM EST** (After-Hours), **Friday 04:30 PM EST** (Weekend). |
| **Buffett 6-Gate Pre-Purchase Audit** | SEC EDGAR 10-K/10-Q / DuckDB Lake | [SEC EDGAR Search](https://www.sec.gov/edgar/searchedgar/companysearch) | Verify Gate 1 (Circle of Competence), Gate 2 (Moat Gross Margin $\ge 40\%$), Gate 3 (Piotroski $F \ge 5/9$), Gate 4 (Share Dilution $\le 2\%$), Gate 5 (Reverse DCF Hurdle), Gate 6 (Beneish $M < -1.78$ & 4Q Rolling Sloan $\le 8\%$). Confirm fatal veto ($0.0\times$) strictly requires multi-signal confluence, while borderline M-scores trigger $0.5\times$ Warning. |
| **Piotroski F-Score (0-9)** | SEC EDGAR 10-K/10-Q Financials | [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch) | Verify 9 binary criteria across Profitability (ROA, CFO, $\Delta\text{ROA}$, Accrual), Leverage/Liquidity ($\Delta\text{Leverage}$, $\Delta\text{Liquidity}$, Equity Offering), and Operating Efficiency ($\Delta\text{Gross Margin}$, $\Delta\text{Asset Turnover}$). |
| **Beneish M-Score & Sloan Accrual** | SEC EDGAR 10-K/10-Q Statements | [SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch) | Verify AQI does not subtract Gross Profit; SGI contribution is capped at $1.25$ for stable/expanding gross margins ($GMI \le 1.05$); Sloan Accruals use 4-quarter rolling mean. |
| **Thematic Depth4 Cascades** | Depth4 / SEC / Industry Filings | [Depth4](https://depth4.com/) | Verify D1 (Direct pure play) $\to$ D2 (Critical components) $\to$ D3 (Power/Grid) $\to$ D4 (Tertiary raw materials). Verify Unpriced Room % $> 0\%$ and Bottleneck Hunter $P/S \le 30\times$. |
| **Catalyst & Star Rating (1★-5★)** | Yahoo Finance / Finviz / SEC EDGAR | [Finviz News Feed](https://finviz.com/news.ashx) or [SEC Company Filings](https://www.sec.gov/edgar/searchedgar/companysearch) | Verify news headline matches live wire; verify rating scale (e.g. 5★ for Earnings Beat, 2★ for Sector Sympathy). Verify negative dilution is disqualified. |
| **Economic Calendar** | Finviz Calendar | [Finviz Economic Calendar](https://finviz.com/calendar.ashx) | Compare today's scheduled US releases with time (EST), impact (HIGH/MED/LOW), forecast, and prior. |
| **Earnings Calendar (3-Day Active)** | Finviz Screener Filter | [Finviz Earnings Calendar](https://finviz.com/screener.ashx?v=111&f=earningsdate_todaybefore&o=-marketcap) | Compare list of companies reporting: Yesterday AMC, Today BMO, Today AMC, and Tomorrow. |
| **Analyst Actions & Price Targets** | Finviz Feed / Yahoo Finance | [Finviz Homepage](https://finviz.com/) | Verify recent analyst upgrades, downgrades, research firm name, and price targets strictly from Yesterday and Today. |
| **45-Day Options GEX Structure** | Yahoo Live Options Chains / CBOE | [Yahoo Options Chain (e.g. NVDA)](https://finance.yahoo.com/quote/NVDA/options) | For qualified tickers, check Call Wall (strike with highest call open interest), Put Wall (highest put open interest), and Gamma Flip level. |

---

## 2. Step-by-Step Verification Procedure

1. **Verify Macro Regime**:
   - Open [Yahoo Finance ^TNX](https://finance.yahoo.com/quote/%5ETNX) and [Yahoo Finance ^VIX](https://finance.yahoo.com/quote/%5EVIX). Confirm that 10Y Yield and VIX in the dashboard match live quotes.
   - Check the **B. Riley Rule**: If both 10Y Yield and Oil are falling, confirm the banner displays *"Markets are Good (Bullish Tailwind)"*.

2. **Verify Session-Specific Price Breakout**:
   - In Premarket: Confirm all tickers have `Price > Yesterday's High`.
   - In Regular Hours: Confirm all tickers have `Price > Yesterday's High` **AND** `Price >= Premarket High`.
   - In After-Hours/Weekend: Confirm all tickers have `Price >= Latest Day's High`.

3. **Verify Level % Distances**:
   - For any ticker (e.g., current price $P = \$100.00$), if Call Wall is $\$105.00$, confirm the dashboard displays `$105.00 (+5.0%)`.

4. **Verify Interactive Column Sorting**:
   - Click the **Setup Score** or **RVOL** or **Gap %** column header in `latest_report.html`.
   - Confirm the table immediately re-sorts ascending/descending with the `▲` / `▼` arrow indicator.

5. **Verify Buffett 6-Gate Pre-Purchase Modal & Confluence Veto**:
   - Click on the 6-Gate audit pill for a benchmark ticker (e.g. `NVDA` or `AAPL`).
   - Confirm all 6 individual gate cards render with quantitative metrics:
     - Gate 1: Circle of competence validation.
     - Gate 2: Gross Margin ($\ge 40\%$).
     - Gate 3: Piotroski F-Score ($\ge 5/9$).
     - Gate 4: Share dilution ($\le 2\%$).
     - Gate 5: Reverse DCF implied growth hurdle.
     - Gate 6: Beneish M-Score & Sloan Accrual.
   - Verify that NVDA displays `🟡 WARN / CAUTION` with `0.5x Sizing` and Gate 6 warning ("Elevated Beneish M-Score -1.51 > -1.78 - Monitor working capital"), verifying that a single borderline M-Score does NOT trigger a fatal 0.0x veto.
   - Verify that un-audited tickers cleanly display `⚪ PENDING AUDIT (NO DATA)` cards, never hardcoded dummy $10B passes.

6. **Verify Multi-Session RVOL Anchor Integrity**:
   - In after-hours or weekend sessions, check tickers on the watchlist.
   - Verify RVOL readings are in the realistic range ($1.0\text{x} - 4.0\text{x}$) rather than displaying false $10\text{x}-20\text{x}+$ ratios.
   - Verify the tooltip or badge confirms the anchor time: **Midnight 00:00 AM EST** for Premarket, **09:30 AM EST** for Regular, **04:30 PM EST** for After-Hours, and **Friday 04:30 PM EST** for Weekend.
