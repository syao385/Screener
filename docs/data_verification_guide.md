# Manual Data Verification Guide
 
## Living Document Version History

| Version | Date | Changes & Enhancements | Author / Status |
|---|---|---|---|
| **v1.0.0** | 2026-08-20 | Initial manual verification guide for Premarket & Macro feeds. | Production |
| **v2.0.0** | 2026-08-21 | Added verification steps for 45-Day Options GEX, Put/Call Walls, and Whale Sweeps. | Production |
| **v3.0.0** | 2026-08-22 | Updated verification for 5-Star Setup Score, Catalyst NLP, RVOL, and 17 columns. | Production |
| **v3.1.0** | 2026-08-22 | Added verification for E-mini ES, NQ, Gold, Bitcoin, Market Breadth (A/D %, NH/NL, SMA50/200), and 4-asset portfolio targets. | Active Standard |

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
| **Multi-Session RVOL at Time T** | TradingView / Thinkorswim / Yahoo | [TradingView 5m Chart](https://www.tradingview.com/chart/) | On a 5-minute chart, sum cumulative volume from session start (04:00 for Premarket, 09:30 for Regular, 16:00 for Postmarket) vs average 20-day cumulative volume at exact same time. |
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
