---
name: bottleneck-hunter
description: Supply Chain Chokepoint Arbitrage & Inelastic Monopoly Hunter. Scans Layer 2-3 suppliers facing severe capacity shortages and lead-time blowouts with strict P/S <= 30x valuation gating.
---

# Bottleneck Hunter — Supply Chain Chokepoint Arbitrage (`/bottleneck-hunter`)

**Skill Type**: TIER 1 | Thematic Alpha & Inelastic Supply Arbitrage  
**Purpose**: Systematically identify physical supply chain chokepoints within super-trends before they become crowded. The real alpha is in **Layer 2–3** (photonics, laser sources, InP substrates, SOI wafers, epitaxy equipment, wafer-level probe cards, quick-disconnect cooling couplings, transformers) rather than the already-priced Layer 1 (GPU, hyperscalers, merchant power).

---

## Invocation Syntax

Type in Antigravity Chat:
```text
/bottleneck-hunter [THEME]
```

### Examples:
- `/bottleneck-hunter AI_INFRASTRUCTURE` (Optical interconnect, InP substrates, liquid cooling couplings)
- `/bottleneck-hunter NUCLEAR_GRID_MODERNIZATION` (HALEU fuel, grid transformers, steam turbines)
- `/bottleneck-hunter SEMICONDUCTOR_REINDUSTRIALIZATION` (Ion implantation, ultra-pure quartz, gas subsystems)
- `/bottleneck-hunter DEFENSE_AUTONOMOUS_SYSTEMS` (Solid rocket motor casings, tactical avionics)
- `/bottleneck-hunter all` (Full scan across all 4 super-trends)

---

## ⚠️ PERMANENT INSTITUTIONAL RULES

1. **Zero LLM Arithmetic**: All lead-time expansion ratios, P/S multiples, and margin metrics are deterministically computed via `sources/thematic_intelligence.py`.
2. **Rule 5: Valuation Is a Hard Gate**:
   - A real bottleneck does **NOT** equal an investment opportunity at $P/S > 30.0\times$.
   - If a company's $P/S > 30.0\times$, the engine triggers an automatic **Valuation Veto** (`sizing_multiplier = 0.0x`). Narrative appeal never overrides valuation.
3. **Cross-Validation Mandate**: Every chokepoint thesis requires at least 2 independent data confirmations (customer 10-K disclosures + vendor lead-time verification).
4. **Integration with Screener 2.0**: Qualifying chokepoint candidates automatically populate into `run_screener.py` thematic universe and receive prioritized allocation tags on the Trade Execution Desk.
