# Institutional Market Intelligence Platform Rules & Standards

## Living Document Governance
This document defines the immutable architectural and operational standards for the Institutional Real-Time Intelligence Platform. All code modifications, screener algorithms, and documentation must adhere to these rules.

---

## 1. Zero Fake / Static Data Rule (Core Axiom)
- **Mandate**: Every single metric, price, rating, option level, economic release, and news catalyst MUST be fetched dynamically in real time from official public web feeds, APIs, or SEC filings.
- **Prohibition**: Hardcoded ticker watchlists, static mock dictionaries, dummy numbers, simulated quotes, or fake fallback data are strictly forbidden. If a source is temporarily unreachable, the system must employ automated fallback retry mechanisms or report `" — "` (unavailable).

---

## 2. Multi-Session Gatekeeping Protocol
The platform operates 24/7 across four distinct market sessions:

| Session | Time Window (EST) | Price Breakout Requirement | RVOL Anchor Time |
|---|---|---|---|
| **Premarket** | 04:00 – 09:30 (Weekdays) | $\text{Price} > \text{Yesterday's High}$ | 04:00 EST |
| **Regular Hours** | 09:30 – 16:00 (Weekdays) | $\text{Price} > \text{Yesterday's High}$ **AND** $\text{Price} \ge \text{Premarket High}$ | 09:30 EST |
| **After-Hours** | 16:00 – 20:00 (Weekdays) | $\text{Price} \ge \text{Latest Business Day's High}$ | 16:00 EST |
| **Weekend / Overnight** | All other times | $\text{Price} \ge \text{Latest Business Day's High}$ | 16:00 EST (Friday Close) |

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
1. **`docs/functional_spec.md`** MUST be updated cumulatively with widget-by-widget and field-by-field definitions, data sources, formats, and business rules.
2. **`docs/design_spec.md`** MUST be updated with complete architectural diagrams, quantitative mathematical formulas, decision flowcharts, and engine logic.
3. **`docs/implementation_plan.md`**, **`docs/walkthrough.md`**, and **`docs/data_verification_guide.md`** MUST be updated with updated Version History tables.
4. No obsolete or legacy scanner references (e.g. removed swing trading widget) are permitted to remain in active documentation.
