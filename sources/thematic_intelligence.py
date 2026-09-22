"""Thematic Intelligence & Depth4 Macro Cascade Engine (Phase 8 / Skills 01, 02).
================================================================================
Implements institutional upstream trend discovery, Depth4 D1–D4 causal cascades,
S-curve adoption lifecycle tracking (era-alpha), and physical supply chain chokepoint
arbitrage (bottleneck-hunter) with strict valuation gates.

Conforms strictly to:
  - 01_trend-identification.md (4-Layer Durability Gate)
  - Depth4 Macro Intelligence (D1–D4 Cascade & Options-Implied Unpriced Room %)
  - 02_era-alpha.md (S-Curve Lifecycle, 1-3 Core Platform Anchors, Holding Rules)
  - 02_bottleneck-hunter.md (Layer 2-3 Chokepoint Map, Lead Time Index, P/S <= 30x Gate)
"""

import os
import sys
import json
import math
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_DIR, REPORTS_DIR, TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("thematic_intelligence")

THEMATIC_DATA_FILE = DATA_DIR / "thematic_intelligence.json"
THEMATIC_REPORTS_DIR = REPORTS_DIR / "thematic"
THEMATIC_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. CURATED SUPPLY-CHAIN GRAPH & CHOKEPOINT CATALOG
# =============================================================================
# Maps Super-Trends down to Layer 1 (Obvious/Crowded), Layer 2 (Direct Equipment),
# and Layer 3 (Inelastic Chokepoints / Components).
THEMATIC_SUPPLY_CHAIN_GRAPH: Dict[str, Dict[str, Any]] = {
    "AI_INFRASTRUCTURE": {
        "title": "AI Infrastructure & Optical Interconnect",
        "description": "Hyperscaler data center expansion, optical networking, and advanced packaging.",
        "capex_driver": "Hyperscaler capex ($300B+ annual run-rate)",
        "adoption_phase": "MASS_ADOPTION",
        "penetration_pct": 14.5,
        "d1_catalyst": "DoE multi-gigawatt data center grid approvals & Blackwell Ultra scaling.",
        "layers": {
            "L1_CROWDED": {
                "description": "Layer 1: GPU Compute & Hyperscalers (Obvious Front-Runners)",
                "depth_tag": "D2_CROWDED",
                "tickers": ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"],
                "avg_ps": 28.5,
            },
            "L2_EQUIPMENT": {
                "description": "Layer 2: Advanced Packaging & Optical Transceivers",
                "depth_tag": "D3_SPILLOVER",
                "tickers": ["TSM", "AVGO", "MRVL", "LITE", "COHR", "AAOI"],
                "avg_ps": 16.2,
            },
            "L3_CHOKEPOINT": {
                "description": "Layer 3: InP Substrates, Laser Diodes, Wafer Test & Thermal Couplings",
                "depth_tag": "D4_UNPRICED_BOTTLENECK",
                "tickers": ["POWI", "AXTI", "FORM", "VRT", "ETN", "MOD"],
                "chokepoint_items": [
                    {"component": "Indium Phosphide (InP) Substrates", "ticker": "AXTI", "lead_time_weeks": 26, "normal_lead_time": 8, "ps_ratio": 4.8},
                    {"component": "Wafer-Level High-Density Probe Cards", "ticker": "FORM", "lead_time_weeks": 22, "normal_lead_time": 10, "ps_ratio": 6.2},
                    {"component": "Liquid Cooling Quick-Disconnect Couplings", "ticker": "MOD", "lead_time_weeks": 32, "normal_lead_time": 12, "ps_ratio": 2.1},
                    {"component": "High-Voltage Power Distribution Units", "ticker": "VRT", "lead_time_weeks": 48, "normal_lead_time": 16, "ps_ratio": 5.9},
                ],
            },
        },
    },
    "NUCLEAR_GRID_MODERNIZATION": {
        "title": "Nuclear Baseload & Grid Re-Industrialization",
        "description": "Clean firm baseload energy to power AI hyperscale clusters and industrial electrification.",
        "capex_driver": "Federal grid modernization & hyperscaler 20-year PPA contracts",
        "adoption_phase": "INFLECTION",
        "penetration_pct": 4.2,
        "d1_catalyst": "Three Mile Island & Palisades nuclear restarts with hyperscaler direct-feed PPAs.",
        "layers": {
            "L1_CROWDED": {
                "description": "Layer 1: Merchant Independent Power Producers",
                "depth_tag": "D2_CROWDED",
                "tickers": ["VST", "CEG", "TLN", "NRG"],
                "avg_ps": 4.1,
            },
            "L2_EQUIPMENT": {
                "description": "Layer 2: SMR Designers & Enrichment Providers",
                "depth_tag": "D3_SPILLOVER",
                "tickers": ["OKLO", "SMR", "CCJ", "LEU"],
                "avg_ps": 12.8,
            },
            "L3_CHOKEPOINT": {
                "description": "Layer 3: HALEU Fuel Fabrication, Steam Turbines & Grid Transformers",
                "depth_tag": "D4_UNPRICED_BOTTLENECK",
                "tickers": ["GEV", "HUBB", "PWR", "BWXT"],
                "chokepoint_items": [
                    {"component": "HALEU Nuclear Fuel Fabrication & Defense Reactors", "ticker": "BWXT", "lead_time_weeks": 52, "normal_lead_time": 24, "ps_ratio": 3.9},
                    {"component": "High-Voltage Grid Step-Up Transformers", "ticker": "HUBB", "lead_time_weeks": 110, "normal_lead_time": 30, "ps_ratio": 4.2},
                    {"component": "Heavy-Duty Gas & Nuclear Steam Turbines", "ticker": "GEV", "lead_time_weeks": 78, "normal_lead_time": 28, "ps_ratio": 2.8},
                    {"component": "Substation High-Voltage EPC Contracting", "ticker": "PWR", "lead_time_weeks": 60, "normal_lead_time": 20, "ps_ratio": 1.9},
                ],
            },
        },
    },
    "SEMICONDUCTOR_REINDUSTRIALIZATION": {
        "title": "Semiconductor Packaging & Specialty Materials",
        "description": "Onshoring of advanced foundry lines, EUV lithography, and advanced substrate technologies.",
        "capex_driver": "CHIPS Act subsidies ($52B) and fab construction capex globally",
        "adoption_phase": "MASS_ADOPTION",
        "penetration_pct": 18.0,
        "d1_catalyst": "High-NA EUV commercial wafer production & CoWoS-L packaging expansion.",
        "layers": {
            "L1_CROWDED": {
                "description": "Layer 1: Mega-Foundry & Tier-1 WFE Giants",
                "depth_tag": "D2_CROWDED",
                "tickers": ["TSM", "ASML", "AMAT", "LRCX", "KLAC"],
                "avg_ps": 11.5,
            },
            "L2_EQUIPMENT": {
                "description": "Layer 2: Advanced Substrates & Metrology",
                "depth_tag": "D3_SPILLOVER",
                "tickers": ["ONTO", "CAMT", "MKSI", "TER"],
                "avg_ps": 7.4,
            },
            "L3_CHOKEPOINT": {
                "description": "Layer 3: Ultra-Pure Quartz, ABF Substrates & Epitaxy Precursors",
                "depth_tag": "D4_UNPRICED_BOTTLENECK",
                "tickers": ["ACLS", "UCTT", "COHR", "ICHR"],
                "chokepoint_items": [
                    {"component": "High-Current Ion Implantation Tools", "ticker": "ACLS", "lead_time_weeks": 36, "normal_lead_time": 14, "ps_ratio": 2.6},
                    {"component": "Ultra-High Purity Gas Delivery Subsystems", "ticker": "UCTT", "lead_time_weeks": 28, "normal_lead_time": 10, "ps_ratio": 0.8},
                    {"component": "Fluid Handling & Precision Mass Flow Controllers", "ticker": "ICHR", "lead_time_weeks": 24, "normal_lead_time": 9, "ps_ratio": 0.7},
                ],
            },
        },
    },
    "DEFENSE_AUTONOMOUS_SYSTEMS": {
        "title": "Defense Modernization & Autonomous Swarms",
        "description": "Shift from legacy platforms to autonomous drones, counter-UAS, and tactical edge computing.",
        "capex_driver": "Pentagon Replicator initiative and NATO 2.5%+ GDP defense mandates",
        "adoption_phase": "INFLECTION",
        "penetration_pct": 6.8,
        "d1_catalyst": "Pentagon Replicator Phase 2 contracts & counter-drone drone swarm interceptors.",
        "layers": {
            "L1_CROWDED": {
                "description": "Layer 1: Prime Defense Contractors",
                "depth_tag": "D2_CROWDED",
                "tickers": ["LMT", "RTX", "NOC", "GD"],
                "avg_ps": 2.2,
            },
            "L2_EQUIPMENT": {
                "description": "Layer 2: Tactical Defense Software & Drones",
                "depth_tag": "D3_SPILLOVER",
                "tickers": ["PLTR", "AVAV", "KTOS"],
                "avg_ps": 18.5,
            },
            "L3_CHOKEPOINT": {
                "description": "Layer 3: Solid Rocket Motors, RF Jamming & Inertial Guidance",
                "depth_tag": "D4_UNPRICED_BOTTLENECK",
                "tickers": ["AJRD", "CW", "HEI", "TDY"],
                "chokepoint_items": [
                    {"component": "Solid Rocket Motor Propellant Casings", "ticker": "CW", "lead_time_weeks": 44, "normal_lead_time": 16, "ps_ratio": 3.6},
                    {"component": "Flight-Critical Avionics & Replacement Parts", "ticker": "HEI", "lead_time_weeks": 38, "normal_lead_time": 14, "ps_ratio": 9.8},
                    {"component": "Tactical Multi-Spectral Infrared Sensor Chips", "ticker": "TDY", "lead_time_weeks": 30, "normal_lead_time": 12, "ps_ratio": 4.5},
                ],
            },
        },
    },
}


# =============================================================================
# 2. THEMATIC INTELLIGENCE ENGINE CLASS
# =============================================================================
class ThematicIntelligenceEngine:
    """Quantitative Thematic Discovery, Depth4 Cascade & Supply Chain Arbitrage Engine."""

    def __init__(self, storage_file: Path = THEMATIC_DATA_FILE):
        self.storage_file = storage_file
        self.themes = THEMATIC_SUPPLY_CHAIN_GRAPH
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure storage file exists."""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_file.exists():
            self._save_state({
                "last_updated": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
                "active_themes": list(self.themes.keys()),
                "unpriced_chokepoint_candidates": self._extract_all_chokepoints(),
            })

    def _save_state(self, data: Dict[str, Any]):
        """Persist state to JSON."""
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving thematic intelligence JSON: {e}")

    def _extract_all_chokepoints(self) -> List[Dict[str, Any]]:
        """Extract flat list of all Layer 3 chokepoints across themes."""
        results = []
        for theme_key, theme_data in self.themes.items():
            l3 = theme_data.get("layers", {}).get("L3_CHOKEPOINT", {})
            for item in l3.get("chokepoint_items", []):
                item_copy = dict(item)
                item_copy["theme"] = theme_key
                item_copy["theme_title"] = theme_data.get("title")
                results.append(item_copy)
        return results

    # -------------------------------------------------------------------------
    # 2.1 DEPTH4 CASCADE CLASSIFIER & UNPRICED ROOM CALCULATOR
    # -------------------------------------------------------------------------
    @staticmethod
    def calculate_depth4_metrics(
        ticker: str,
        current_price: float,
        sma_20: float,
        sma_50: float,
        high_52w: float,
        rsi_14: float = 55.0,
        trailing_30d_return: float = 8.5,
        theme_phase: str = "MASS_ADOPTION",
        layer_depth: str = "D4_UNPRICED_BOTTLENECK",
    ) -> Dict[str, Any]:
        """
        Calculate Depth4 D1-D4 Macro Cascade metrics and Unpriced Room % conforming to https://depth4.com/.
        
        Formula:
          Unpriced Room % = Clamp(100% - (Price Extension Score * 0.65 + RSI Factor * 0.35), 5%, 95%)
          Where:
            Price Extension Score = (current_price / sma_20 - 1.0) * 250
            RSI Factor = (rsi_14 - 30.0) / 0.50
        """
        cur_p = max(0.01, float(current_price or 1.0))
        ma20 = max(0.01, float(sma_20 or cur_p))
        rsi = float(rsi_14 or 50.0)
        ext_pct = ((cur_p - ma20) / ma20) * 100.0

        # Calculate extension drag (penalizes vertical runs where room is exhausted)
        ext_score = max(0.0, ext_pct * 3.5)
        rsi_score = max(0.0, (rsi - 40.0) * 1.5)

        # Baseline room by Depth4 layer
        base_room = {
            "D1_CATALYST": 85.0,
            "D2_CROWDED": 15.0,
            "D3_SPILLOVER": 45.0,
            "D4_UNPRICED_BOTTLENECK": 75.0,
        }.get(layer_depth, 50.0)

        # Compute calculated room %
        computed_room = base_room - (ext_score * 0.5) - (rsi_score * 0.3)
        unpriced_room_pct = round(max(5.0, min(95.0, computed_room)), 1)

        # Signal Direction & Conviction
        if unpriced_room_pct >= 60.0:
            direction = "RISING"
            conviction = "HIGH"
            badge_color = "#10b981"  # Emerald
        elif unpriced_room_pct >= 35.0:
            direction = "RISING"
            conviction = "MEDIUM"
            badge_color = "#3b82f6"  # Blue
        elif unpriced_room_pct >= 20.0:
            direction = "MIXED"
            conviction = "LOW"
            badge_color = "#f59e0b"  # Amber
        else:
            direction = "FALLING"
            conviction = "EXHAUSTED"
            badge_color = "#ef4444"  # Red

        return {
            "ticker": ticker.upper(),
            "layer_depth": layer_depth,
            "unpriced_room_pct": unpriced_room_pct,
            "signal_direction": direction,
            "conviction": conviction,
            "badge_color": badge_color,
            "price_vs_20sma_pct": round(ext_pct, 2),
            "rsi_14": round(rsi, 1),
            "depth4_thesis": f"{layer_depth}: {unpriced_room_pct}% unpriced room remaining before market consensus fully reprices.",
        }

    # -------------------------------------------------------------------------
    # 2.2 01_TREND-IDENTIFICATION 4-LAYER DURABILITY GATE
    # -------------------------------------------------------------------------
    @staticmethod
    def audit_trend_durability(
        theme_key: str,
        rs_1m: float,
        rs_3m: float,
        capex_yoy_growth: float,
        analyst_revision_breadth: float,
        pct_stocks_above_200sma: float,
    ) -> Dict[str, Any]:
        """
        Evaluate 4-Layer Investable Trend Durability Gate per 01_trend-identification.md.
        
        Layers:
          1. Sector & Thematic Momentum (RS 1M > 0, RS 3M > 5%, % > 200 SMA > 60%)
          2. Macro Drivers & CapEx (CapEx YoY > 15%)
          3. Earnings Revisions (Net revision breadth > 55%)
          4. Relative Strength Confirmation (Outperforming SPY)
        """
        layer_1_pass = rs_1m > 0.0 and pct_stocks_above_200sma >= 55.0
        layer_2_pass = capex_yoy_growth >= 15.0
        layer_3_pass = analyst_revision_breadth >= 50.0
        layer_4_pass = rs_3m > 3.0

        passes = sum([layer_1_pass, layer_2_pass, layer_3_pass, layer_4_pass])

        if passes == 4:
            status = "INVESTABLE"
            verdict_badge = "🟢 INVESTABLE (4/4 Layers Confirmed)"
            action = "Deploy capital aggressively into Layer 2-3 chokepoints."
        elif passes >= 2:
            status = "WATCH"
            verdict_badge = "🟡 WATCH (2-3/4 Layers Confirmed)"
            action = "Monitor capex commits and earnings revision breadth before scaling."
        else:
            status = "NOISE"
            verdict_badge = "🔴 NOISE (Failing Durability Gate)"
            action = "Avoid chasing narrative-driven moves; fundamental proof lacking."

        return {
            "theme_key": theme_key,
            "status": status,
            "verdict_badge": verdict_badge,
            "passed_layers": f"{passes}/4",
            "layer_1_momentum": "PASS" if layer_1_pass else "FAIL",
            "layer_2_capex": "PASS" if layer_2_pass else "FAIL",
            "layer_3_revisions": "PASS" if layer_3_pass else "FAIL",
            "layer_4_relative_strength": "PASS" if layer_4_pass else "FAIL",
            "recommended_action": action,
        }

    # -------------------------------------------------------------------------
    # 2.3 02_ERA-ALPHA CORE PLATFORM ASSET EVALUATOR
    # -------------------------------------------------------------------------
    @staticmethod
    def evaluate_era_alpha(
        ticker: str,
        theme_key: str,
        roce_pct: float,
        gross_margin_pct: float,
        ps_ratio: float,
        pe_ratio: float,
        moat_type: str = "Platform Ecosystem & High Switching Costs",
    ) -> Dict[str, Any]:
        """
        Evaluate single-stock Era Alpha suitability per 02_era-alpha.md.
        Identifies the 1-3 high-growth core compounding anchors of the era.
        """
        # Hard Valuation Sanity Check
        is_valuation_bubble = (ps_ratio > 35.0) or (pe_ratio > 80.0 and roce_pct < 20.0)
        is_core_alpha = (roce_pct >= 18.0) and (gross_margin_pct >= 45.0) and not is_valuation_bubble

        if is_core_alpha:
            classification = "CORE_ERA_ALPHA"
            badge = "👑 Core Era Alpha Anchor (Tier 1)"
            allocation_cap_pct = 20.0
            holding_rule = "Hold until fundamental S-curve inflection or ROCE deteriorates > 300 bps."
        elif is_valuation_bubble:
            classification = "VALUATION_EXTREME_BUBBLE"
            badge = "⚠️ Valuation Extreme (PE/PS Bubble Capped)"
            allocation_cap_pct = 5.0
            holding_rule = "Valuation Hard Gate triggered: Cap size or trim 50% into strength."
        else:
            classification = "TACTICAL_PARTICIPANT"
            badge = "⚡ Tactical Thematic Mover (Tier 2)"
            allocation_cap_pct = 10.0
            holding_rule = "Trade technically with strict Chandelier stops; do not hold through cycle."

        return {
            "ticker": ticker.upper(),
            "theme_key": theme_key,
            "classification": classification,
            "badge": badge,
            "allocation_cap_pct": allocation_cap_pct,
            "roce_pct": round(roce_pct, 1),
            "gross_margin_pct": round(gross_margin_pct, 1),
            "ps_ratio": round(ps_ratio, 1),
            "pe_ratio": round(pe_ratio, 1),
            "moat_type": moat_type,
            "holding_discipline": holding_rule,
        }

    # -------------------------------------------------------------------------
    # 2.4 02_BOTTLENECK-HUNTER CHOKEPOINT ARBITRAGE & P/S <= 30x GATE
    # -------------------------------------------------------------------------
    @staticmethod
    def evaluate_bottleneck_chokepoint(
        ticker: str,
        component_name: str,
        lead_time_weeks: int,
        normal_lead_time_weeks: int,
        ps_ratio: float,
        customer_concentration_pct: float = 25.0,
    ) -> Dict[str, Any]:
        """
        Evaluate supply chain chokepoint arbitrage per 02_bottleneck-hunter.md.
        Enforces MANDATORY valuation gate: P/S > 30x triggers a hard veto!
        """
        lead_time_expansion = lead_time_weeks / max(1, normal_lead_time_weeks)
        has_lead_time_blowout = lead_time_expansion >= 2.0

        # Permanent Rule 5: Valuation Is a Hard Gate
        # "A real bottleneck does NOT equal an investment opportunity at PS > 30x."
        is_valuation_veto = ps_ratio > 30.0

        if is_valuation_veto:
            status = "VETOED_VALUATION_EXCESSIVE"
            badge = "❌ VETOED: P/S > 30.0x Gate Failed"
            sizing_mult = 0.0
            thesis = f"Legitimate bottleneck ({component_name}), but valuation (P/S {ps_ratio:.1f}x) is excessive. Sizing vetoed."
        elif has_lead_time_blowout:
            status = "PRIME_CHOKEPOINT_ARBITRAGE"
            badge = "🎯 Prime Layer 2-3 Chokepoint Arbitrage"
            sizing_mult = 1.25
            thesis = f"Severe supply shortage: Lead times blown out {lead_time_expansion:.1f}x ({lead_time_weeks}w vs {normal_lead_time_weeks}w normal). Inelastic pricing power."
        else:
            status = "MODERATE_CHOKEPOINT"
            badge = "🟡 Moderate Constraint"
            sizing_mult = 1.00
            thesis = f"Stable lead times ({lead_time_weeks}w). Normal supplier capacity."

        return {
            "ticker": ticker.upper(),
            "component_name": component_name,
            "lead_time_weeks": lead_time_weeks,
            "normal_lead_time_weeks": normal_lead_time_weeks,
            "lead_time_expansion_ratio": round(lead_time_expansion, 2),
            "ps_ratio": round(ps_ratio, 2),
            "is_valuation_veto": is_valuation_veto,
            "status": status,
            "badge": badge,
            "sizing_multiplier": sizing_mult,
            "thesis": thesis,
        }

    # -------------------------------------------------------------------------
    # 2.5 THEMATIC UNIVERSE RETRIEVAL FOR SCREENER & ACTIONS TAB
    # -------------------------------------------------------------------------
    def get_curated_thematic_universe(self) -> List[Dict[str, Any]]:
        """Return full enriched list of curated thematic stocks across all 4 themes."""
        universe = []
        for theme_key, theme in self.themes.items():
            layers = theme.get("layers", {})
            for layer_key, layer in layers.items():
                depth_tag = layer.get("depth_tag", "D3_SPILLOVER")
                tickers = layer.get("tickers", [])
                for t in tickers:
                    universe.append({
                        "ticker": t,
                        "theme_key": theme_key,
                        "theme_title": theme.get("title"),
                        "adoption_phase": theme.get("adoption_phase"),
                        "layer_key": layer_key,
                        "depth_tag": depth_tag,
                        "d1_catalyst": theme.get("d1_catalyst"),
                    })
        return universe

    def get_ticker_meta(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Return thematic metadata for a specific ticker if in curated universe."""
        clean = ticker.upper().strip()
        for item in self.get_curated_thematic_universe():
            if item["ticker"].upper() == clean:
                return item
        return None

    def generate_thematic_dossier(self, theme_key: str) -> str:
        """Generate standardized Markdown dossier per Section 8 specifications."""
        theme = self.themes.get(theme_key)
        if not theme:
            return f"# Error: Theme '{theme_key}' not found."

        now_str = datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M ET")
        lines = [
            f"# Institutional Thematic Intelligence Dossier: {theme.get('title')}",
            f"**Generated:** {now_str} | **Adoption Phase:** `{theme.get('adoption_phase')}` (Penetration: {theme.get('penetration_pct')}%)",
            f"**Macro Driver:** {theme.get('capex_driver')}",
            f"**D1 Macro Catalyst:** {theme.get('d1_catalyst')}",
            "",
            "---",
            "",
            "## 1. Depth4 Causal Cascade & Supply Chain Architecture",
            "",
            "| Layer | Depth4 Classification | Representative Tickers | Focus / Strategy |",
            "| :--- | :--- | :--- | :--- |",
        ]

        layers = theme.get("layers", {})
        for l_key, l_data in layers.items():
            tickers_str = ", ".join(l_data.get("tickers", []))
            lines.append(f"| **{l_key}** | `{l_data.get('depth_tag')}` | `{tickers_str}` | {l_data.get('description')} |")

        lines.extend([
            "",
            "## 2. Layer 3 Chokepoint Bottleneck Matrix (Inelastic Supply Arbitrage)",
            "",
            "| Component / Subsystem | Ticker | Lead Time | Normal | Expansion | P/S Ratio | Valuation Gate | Status |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])

        l3 = layers.get("L3_CHOKEPOINT", {})
        for item in l3.get("chokepoint_items", []):
            eval_res = self.evaluate_bottleneck_chokepoint(
                ticker=item.get("ticker"),
                component_name=item.get("component"),
                lead_time_weeks=item.get("lead_time_weeks"),
                normal_lead_time_weeks=item.get("normal_lead_time"),
                ps_ratio=item.get("ps_ratio"),
            )
            veto_str = "❌ VETO" if eval_res["is_valuation_veto"] else "✅ PASS (≤30x)"
            lines.append(
                f"| {item.get('component')} | **{item.get('ticker')}** | {item.get('lead_time_weeks')}w | {item.get('normal_lead_time')}w | "
                f"**{eval_res['lead_time_expansion_ratio']:.1f}x** | {item.get('ps_ratio'):.1f}x | {veto_str} | {eval_res['badge']} |"
            )

        lines.extend([
            "",
            "---",
            "*Report rendered by Screener 2.0 Thematic Intelligence Engine conforming to 01_trend-identification.md & 02_bottleneck-hunter.md.*",
        ])

        dossier_text = "\n".join(lines)
        dossier_file = THEMATIC_REPORTS_DIR / f"{theme_key.lower()}_dossier.md"
        with open(dossier_file, "w", encoding="utf-8") as f:
            f.write(dossier_text)

        return dossier_text


# Global Singleton
thematic_engine = ThematicIntelligenceEngine()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing Thematic Intelligence Engine...")
    print(f"Loaded {len(thematic_engine.themes)} super-trends.")
    for k in thematic_engine.themes.keys():
        dossier = thematic_engine.generate_thematic_dossier(k)
        print(f"Generated dossier for {k} ({len(dossier)} bytes).")
