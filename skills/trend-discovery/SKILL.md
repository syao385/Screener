---
name: trend-discovery
description: Upstream Macro Trend Discovery & Depth4 Causal Cascade Desk. Executes 4-layer durability gating (momentum, capex, revisions, relative strength) and calculates Depth4 D1-D4 unpriced room before moves get crowded.
---

# Trend Discovery & Depth4 Macro Cascade Desk (`/trend-discovery`)

**Skill Type**: TIER 1 | Upstream Macro Foundation & Pre-Crowding Universe Discovery  
**Purpose**: Systematically discover durable multi-year macro trends before they become crowded. Bridges macro policy/capex catalysts with Depth4's D1–D4 causal cascade (`https://depth4.com/`), measuring the options-implied **"Unpriced Room %"** before retail volume chases the charts.

---

## Invocation Syntax

Type in Antigravity Chat:
```text
/trend-discovery [mode=all|scan] [theme=AI_INFRASTRUCTURE|NUCLEAR_GRID|SEMIS|DEFENSE]
```

### Examples:
- `/trend-discovery` (Runs full 4-layer durability audit across all macro themes)
- `/trend-discovery theme=AI_INFRASTRUCTURE` (Audits AI datacenter capex and optical interconnect)
- `/trend-discovery mode=depth4` (Lists tickers with Depth4 Unpriced Room $\ge 50\%$)

---

## 4-Layer Investable Trend Durability Gate

A trend is classified as **`INVESTABLE`** only when all 4 layers pass:
1. **Layer 1: Sector Momentum**: Relative strength $1\text{M} > 0$ and $>55\%$ of sector stocks above 200-SMA.
2. **Layer 2: Macro Drivers & CapEx**: Verifiable capex growth $\ge +15\%$ YoY in primary company filings.
3. **Layer 3: Earnings Revisions**: Net upward analyst estimate revisions $\ge 50\%$.
4. **Layer 4: Relative Price Strength**: Outperforming the SPY benchmark.

### Depth4 D1–D4 Time-Horizon Cascade
- **`D1_CATALYST`**: Fresh macro news, policy grant, or capex hike.
- **`D2_CROWDED`**: First-order obvious reaction (Retail chasing; Unpriced Room $<20\%$).
- **`D3_SPILLOVER`**: Second-order equipment/component providers.
- **`D4_UNPRICED_BOTTLENECK`**: Structural chokepoints where market consensus is still behind (Unpriced Room $>60\%$).
