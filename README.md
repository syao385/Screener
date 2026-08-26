# ? Institutional Alpha Trading Desk & Screener 2.0
> **High-Performance Multi-Factor Real-Time Stock Screener, Institutional Pattern Recognition Engine & Portfolio Execution Desk**

---

## ?? Overview & Philosophy

The **Institutional Alpha Trading Desk 2.0** is an enterprise-grade quantitative screener and trading workflow engine built for professional momentum, breakout, and reversion traders. It combines real-time volume velocity, multi-timeframe price action, bespoke archetype scoring, volatility-parity position sizing, and institutional options gamma into a unified decision terminal.

### ??? Core Design Principles
1. **Zero One-Size-Fits-All Scoring**: Different market setups require fundamentally different factor weights (e.g. low volume is rewarded for tight consolidations and pullbacks, while explosive volume is required for breakouts).
2. **Strict Exhaustion Gating**: Setups with extended vertical runs, extreme RSI (>80), or massive extension above key moving averages receive mathematical penalties to prevent chasing overbought tops.
3. **Structured Execution Matrix**: Every qualified setup automatically outputs an institutional trade plan with defined **Entry Pivot**, **Hard Stop ($ & %)**, **Soft Stop (Time/VWAP)**, **Profit Target 1 (2.0R)**, **Profit Target 2 (3.5R)**, and **Trailing Rules**.
4. **Interactive Action Queue**: Seamlessly bridges screening and live execution with a unified **Trade Execution Desk** featuring persistent checkboxes (`[? Done]`, `[? Skip]`) saved locally in the browser.

---

## ?? The 9 Institutional Master Setup Archetypes

1. **?? High Tight Flag (HTF)**: Explosive prior $+75\%$ to $+100\%+$ run over 4-8 weeks, consolidating tightly in $<20\%$ range near 52w highs.
2. **? Base Breakout (Cup & Handle / Base-on-Base)**: 7-14 week constructive base breaking above pivot with heavy institutional volume ($RVOL \ge 1.40	imes$).
3. **?? Minervini VCP & Cheat**: Volatility contraction pattern with volume dry-up on contraction and volume expansion on pivot breakout.
4. **?? Episodic Pivot Lifecycle (Days 1, 2 & 3)**: Fundamental shock repricing (Earnings/FDA/M&A) with gap $\ge +7\%$ on heavy volume, Day 2 VWAP touch, and Day 3 high break.
5. **?? Stage 2 Pullback & PEAD**: Trend continuation pullback to rising 10-EMA/20-SMA with low volume dry-up ($RVOL \le 1.10	imes$).
6. **? Market Structure Break (BOS)**: Structural change of character with multi-day swing high/low break on volume.
7. **?? Intraday Velocity & ORB**: Stockbeep-style 5-minute volume surges $\ge 2.2	imes$, opening range breakout, and VWAP bounce.
8. **?? Climax Reversals (Selling Climax Bottoms & Buying Climax Tops)**: Institutional absorption bottoms (e.g. historical inflection dates 3/22/2022, 4/8/2025, 3/27/2026) and parabolic exhaustion tops.
9. **?? Whale Flow & Options Gamma**: Option sweep orders $\ge \$200	ext{K}$, Call Wall headroom within $+2\%$ to $+8\%$ of spot, and bullish skew.

---

## ?? 5 Bespoke Quant Archetype Scoring Engines

| Archetype | Setup Target | Volume Scoring Rule | Key Evaluation Factors |
| :--- | :--- | :--- | :--- |
| **`ARCHETYPE_A`** | HTF & Base Breakouts | **Expansion**: RVOL $\ge 1.5	imes$ awards $+1.2	ext{?}$ | Prior trend, base tightness, pivot clearance |
| **`ARCHETYPE_B`** | Minervini VCP & Cheat | **Dual Mode**: Volume dry-up awarded for Cheat; Expansion awarded for breakout | Contraction symmetry, range compression $\le 6\%$, 52w high proximity |
| **`ARCHETYPE_C`** | Episodic Pivots (EP 1?3) | **Expansion**: RVOL $\ge 1.4	imes$ awards $+1.0	ext{?}$ | Catalyst impact (1?5?), gap size, Day 1 low hold |
| **`ARCHETYPE_D`** | Stage 2 Pullback & PEAD | **Contraction**: RVOL $\le 0.90	imes$ awards $+1.0	ext{?}$ (High volume penalized) | MA ribbon support (10EMA/20SMA), distance to MA $\le 2\%$, PEAD |
| **`ARCHETYPE_E`** | Velocity, BOS & Climax | **Absorption**: RVOL $\ge 2.2	imes$ awards $+1.5	ext{?}$ | Rejection wick $\%$, RSI displacement, intraday velocity |

---

## ?? Trade Execution Desk (Actions Tab)

The interactive Trade Execution Desk displays prioritized actionable trades across 4 urgency tiers:
- **? Tier 1: Immediate Priority Actions**: Urgent entry breakouts, EP Day 1 surges, 3-day down-day exit rules.
- **?? Tier 2: Hard Stops / Risk Alerts**: Portfolio stop breaches, breakdown exits, VCP setup triggers.
- **?? Tier 3: Profit Targets & Trims**: 2.0R / 3.5R target completions, 50% profit trims.
- **?? Tier 4: Trailing Management & Review**: Systematic 20-SMA trailing rules, core portfolio maintenance.

---

## ?? Floating Zero-Clipping Diagnostic Scorecard Portal

Hovering over any **Setup Score (?)** or **Pattern Badge** instantly triggers a high-density diagnostic portal:
1. **?? Setup Criteria Checklist**: Status of Stage 2 trend, 10/20/50 MA ribbon, 5-day range tightness $\%$, distance to 52w high $\%$, session RVOL, and close location.
2. **?? Bespoke Score Breakdown Math**: Exact points awarded for Base Geometry, Volume Behavior, Trend Alignment, Catalyst Shock, Options Gamma, and Exhaustion Penalties.
3. **?? Institutional Trade Plan**: Entry Pivot, Hard Stop $(\$ / \% )$, Soft Stop, Target 1 (2.0R), Target 2 (3.5R), Trailing Rule, and Conviction Multiplier.
4. **?? Catalyst & News Intelligence**: Headline, source link, star rating, sector/industry.

---

## ?? Installation & Running

```bash
# 1. Clone repository
git clone https://github.com/syao385/Screener.git
cd Screener

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Screener Pipeline
python run_screener.py
```
