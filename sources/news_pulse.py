"""Skill 13: Quantitative News Signal Detection, Beta Residualization & Attribution Engine (Phase 6).
========================================================================================
Implements institutional news quantification and event-driven attribution:
  1. 2-Factor Beta Residualization: Isolates idiosyncratic single-stock return from
     market (SPY) and sector (GICS ETF) beta drift:
       eps_i,t = R_i,t - (alpha_i + beta_SPY * R_SPY,t + beta_Sec * R_Sec,t)
  2. Multi-Factor Signal Score (0 - 100):
       Signal = 0.40 * Relevance + 0.30 * Novelty + 0.20 * Authority + 0.10 * |Sentiment|
  3. Price Attribution Weighting & Noise Suppression.
  4. Stealth Event Surveillance (Z_eps >= 2.0 with Signal < 50) flagging informed flow.
  5. 4 System Triggers:
       - Portfolio Movers (|R_1d| >= 3.5% or RVOL >= 1.8x)
       - Post-Earnings Price Divergence (PEAD vs Bull Trap)
       - Screener Breakout Catalyst Verification
       - Stealth Anomaly Alerts
"""

import math
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

from config import TZ_EST

logger = logging.getLogger("news_pulse")

# Default Sector Proxy ETF map
SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Healthcare": "XLV",
    "Consumer Discretionary": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Staples": "XLP",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
}

# Authority ratings by source type
AUTHORITY_RATINGS = {
    "SEC_EDGAR": 100.0,
    "10-Q": 100.0,
    "10-K": 100.0,
    "8-K": 100.0,
    "PRESS_RELEASE": 85.0,
    "COMPANY_IR": 85.0,
    "REUTERS": 75.0,
    "BLOOMBERG": 75.0,
    "WSJ": 75.0,
    "FINANCIAL_MEDIA": 70.0,
    "YAHOO_FINANCE": 65.0,
    "MARKETWATCH": 65.0,
    "SOCIAL_MEDIA": 25.0,
    "FORUM_BLOG": 20.0,
}


class NewsPulseEngine:
    """Quantitative News Signal Detection and Price Attribution Engine."""

    def __init__(self):
        self.default_market_beta = 1.05
        self.default_sector_beta = 0.85
        self.market_return_default = 0.004  # +0.4% market benchmark reference
        self.sector_return_default = 0.005  # +0.5% sector reference

    def calculate_residual_return(
        self,
        stock_return: float,
        market_return: Optional[float] = None,
        sector_return: Optional[float] = None,
        beta_spy: Optional[float] = None,
        beta_sector: Optional[float] = None,
        alpha: float = 0.0,
    ) -> Dict[str, float]:
        """Compute idiosyncratic return eps_i,t adjusted for market and sector betas.
        
        Formula:
          eps_i,t = R_i,t - (alpha + beta_SPY * R_SPY,t + beta_Sec * R_Sec,t)
        """
        m_ret = market_return if market_return is not None else self.market_return_default
        s_ret = sector_return if sector_return is not None else self.sector_return_default
        b_spy = beta_spy if beta_spy is not None else self.default_market_beta
        b_sec = beta_sector if beta_sector is not None else self.default_sector_beta

        market_component = b_spy * m_ret
        sector_component = b_sec * s_ret
        systematic_return = alpha + market_component + sector_component
        residual_return = stock_return - systematic_return

        # Estimate rolling residual volatility proxy (assume ~1.8% daily residual std dev)
        residual_vol_proxy = 0.018
        residual_zscore = residual_return / residual_vol_proxy if residual_vol_proxy > 0 else 0.0

        return {
            "stock_return": round(stock_return, 4),
            "market_component": round(market_component, 4),
            "sector_component": round(sector_component, 4),
            "systematic_return": round(systematic_return, 4),
            "residual_return": round(residual_return, 4),
            "residual_zscore": round(residual_zscore, 2),
        }

    def compute_signal_score(
        self,
        relevance: float,
        novelty: float,
        authority_or_source: Any,
        sentiment: float,
    ) -> Dict[str, float]:
        """Compute multi-factor news signal score (0 - 100).
        
        Formula:
          Signal Score = 0.40 * Relevance + 0.30 * Novelty + 0.20 * Authority + 0.10 * |Sentiment|
        """
        # Resolve authority score
        if isinstance(authority_or_source, (int, float)):
            authority_score = float(authority_or_source)
        else:
            source_key = str(authority_or_source).upper().replace(" ", "_")
            authority_score = AUTHORITY_RATINGS.get(source_key, 65.0)

        # Ensure scales are bounded [0, 100]
        r = max(0.0, min(100.0, float(relevance)))
        n = max(0.0, min(100.0, float(novelty)))
        a = max(0.0, min(100.0, float(authority_score)))
        s = max(0.0, min(100.0, abs(float(sentiment)) * (100.0 if abs(sentiment) <= 1.0 else 1.0)))

        composite_score = (0.40 * r) + (0.30 * n) + (0.20 * a) + (0.10 * s)
        composite_score = round(composite_score, 1)

        # Classification
        if composite_score >= 70.0:
            classification = "HIGH_SIGNAL"
        elif composite_score >= 50.0:
            classification = "MEDIUM_SIGNAL"
        else:
            classification = "NOISE"

        return {
            "composite_score": composite_score,
            "relevance": r,
            "novelty": n,
            "authority": a,
            "sentiment_magnitude": s,
            "classification": classification,
        }

    def attribute_news_event(
        self,
        residual_return: float,
        residual_zscore: float,
        signal_score: float,
        event_name: str = "",
        source: str = "",
    ) -> Dict[str, Any]:
        """Determine attribution weight and stealth flow classification."""
        # Check for stealth event: high residual z-score but low signal news
        is_stealth = bool(abs(residual_zscore) >= 2.0 and signal_score < 50.0)

        # Attribution weight calculation
        if is_stealth:
            attribution_weight = 0.10
            driver_type = "STEALTH_FLOW"
            label = "🕵️ Stealth Event (Informed Flow / Leakage)"
        elif signal_score >= 70.0:
            attribution_weight = min(0.95, round(0.50 + (signal_score / 200.0), 2))
            driver_type = "PRIMARY_DRIVER"
            label = "🔴 Primary Driver"
        elif signal_score >= 50.0:
            attribution_weight = min(0.60, round(0.20 + (signal_score / 250.0), 2))
            driver_type = "CONTRIBUTING_DRIVER"
            label = "🟡 Contributing Factor"
        else:
            attribution_weight = 0.15
            driver_type = "COINCIDENTAL"
            label = "⚪ Coincidental / Noise"

        return {
            "is_stealth": is_stealth,
            "attribution_weight": attribution_weight,
            "driver_type": driver_type,
            "driver_label": label,
            "event_name": event_name or "Market Volatility",
            "source": source or "Market Tape",
        }

    def evaluate_portfolio_position(
        self,
        symbol: str,
        price_change_pct: float,
        rvol: float = 1.0,
        catalyst_text: str = "",
        catalyst_source: str = "",
        sector: str = "Technology",
    ) -> Dict[str, Any]:
        """Evaluate a single portfolio holding for abnormal mover triggers and attribution."""
        ret_1d = price_change_pct / 100.0
        
        # Trigger condition: |R_1d| >= 3.5% or RVOL >= 1.8x
        is_mover = abs(price_change_pct) >= 3.5 or rvol >= 1.8

        residuals = self.calculate_residual_return(ret_1d)
        res_ret = residuals["residual_return"]
        res_z = residuals["residual_zscore"]

        # If text is provided, score it, otherwise default based on presence
        if catalyst_text and len(catalyst_text.strip()) > 5:
            rel = 85.0
            nov = 80.0
            auth = catalyst_source or "FINANCIAL_MEDIA"
            sent = 0.7 if price_change_pct > 0 else -0.7
            sig = self.compute_signal_score(rel, nov, auth, sent)
        else:
            sig = {
                "composite_score": 35.0,
                "relevance": 30.0,
                "novelty": 30.0,
                "authority": 40.0,
                "sentiment_magnitude": 20.0,
                "classification": "NOISE",
            }

        attr = self.attribute_news_event(
            residual_return=res_ret,
            residual_zscore=res_z,
            signal_score=sig["composite_score"],
            event_name=catalyst_text,
            source=catalyst_source,
        )

        return {
            "symbol": symbol,
            "is_mover": is_mover,
            "is_stealth": attr.get("is_stealth", False),
            "return_1d_pct": price_change_pct,
            "residuals": residuals,
            "signal": sig,
            "attribution": attr,
            "timestamp": datetime.datetime.now(TZ_EST).strftime("%Y-%m-%d %H:%M:%S ET"),
        }

    def evaluate_earnings_divergence(
        self,
        symbol: str,
        pead_classification: str,
        sue: float,
        post_earnings_return_pct: float,
        rev_surprise_pct: float = 0.0,
        eps_surprise_pct: float = 0.0,
    ) -> Dict[str, Any]:
        """Cross-reference earnings financial surprise with price reaction to flag divergence."""
        is_beat = sue >= 0.2 or pead_classification in ["TRIPLE_BULL_BEAT", "BEAT_CONFIRMED"]
        is_miss = sue < -0.2 or pead_classification in ["DOUBLE_MISS", "BEAR_MISS"]

        if is_beat and post_earnings_return_pct <= -2.5:
            scenario = "PEAD_OVERREACTION_OPPORTUNITY"
            label = "🟢 PEAD Overreaction (Dip-Buy Candidate / Archetype D)"
            action = "STAGE2_PULLBACK_CANDIDATE"
            desc = f"Strong operational beat (SUE: {sue:+.2f}) was sold off ({post_earnings_return_pct:+.1f}%). Guidance/positioning dislocation."
        elif is_miss and post_earnings_return_pct >= +2.5:
            scenario = "BULL_TRAP_DISTRIBUTION"
            label = "🔴 Bull Trap Distribution (Short / Exit Candidate)"
            action = "LIQUIDATE_OR_FADE"
            desc = f"Fundamental quality miss (SUE: {sue:+.2f}) artificially pumped ({post_earnings_return_pct:+.1f}%). High risk of sharp reversal."
        elif is_beat and post_earnings_return_pct >= +2.5:
            scenario = "CONFIRMED_EP_BREAKOUT"
            label = "🚀 Confirmed EP Breakout (Hold / Add / Archetype C)"
            action = "HOLD_AND_TRAIL"
            desc = f"Clean earnings beat confirmed by institutional volume repricing ({post_earnings_return_pct:+.1f}%)."
        elif is_miss and post_earnings_return_pct <= -2.5:
            scenario = "CONFIRMED_STRUCTURAL_BREAKDOWN"
            label = "⚠️ Structural Breakdown (Enforce Hard Stops)"
            action = "EXIT_ON_CLOSE"
            desc = f"Fundamental miss confirmed by price liquidation ({post_earnings_return_pct:+.1f}%). Thesis damaged."
        else:
            scenario = "IN_LINE_STABLE"
            label = "🟡 In-Line Execution"
            action = "MAINTAIN"
            desc = "Price and fundamental reaction within normal statistical bounds."

        return {
            "symbol": symbol,
            "scenario": scenario,
            "label": label,
            "action": action,
            "description": desc,
            "sue": sue,
            "price_return_pct": post_earnings_return_pct,
            "rev_surprise_pct": rev_surprise_pct,
            "eps_surprise_pct": eps_surprise_pct,
        }

    def compute_composite_catalyst_score(
        self,
        pattern_stars: float,
        source: str = "FINANCIAL_MEDIA",
        sentiment_score: float = 0.5,
        relevance: float = 85.0,
        novelty: float = 80.0,
    ) -> Dict[str, Any]:
        """Compute unified composite catalyst score across pattern stars, source authority, and sentiment.
        
        Formula:
          Blended = 0.50 * Pattern Stars + 0.30 * (Signal Score / 20) + 0.20 * Directional Sentiment
        """
        sig = self.compute_signal_score(relevance=relevance, novelty=novelty, authority_or_source=source, sentiment=sentiment_score)
        signal_score = sig["composite_score"]
        authority = sig["authority"]
        
        # Directional sentiment mapped to 0-5
        sent_component = (max(-1.0, min(1.0, sentiment_score)) + 1.0) * 2.5
        blended_score = round(
            0.50 * float(pattern_stars) +
            0.30 * (float(signal_score) / 20.0) +
            0.20 * sent_component,
            2
        )
        blended_score = max(1.0, min(5.0, blended_score))
        return {
            "blended_score": blended_score,
            "pattern_stars": float(pattern_stars),
            "signal_score": float(signal_score),
            "authority": float(authority),
            "sentiment_score": float(sentiment_score),
            "classification": sig["classification"],
        }

    def evaluate_divergence_and_sentiment_delta(
        self,
        symbol: str,
        current_sentiment: float,
        prior_sentiment: Optional[float] = None,
        price_change_pct: float = 0.0,
        social_sentiment: Optional[float] = None,
        social_volume_surge: bool = False,
    ) -> Dict[str, Any]:
        """Evaluate 7-day Sentiment Delta and Narrative-Price Divergence regimes."""
        if prior_sentiment is None:
            prior_sentiment = current_sentiment
        
        delta_sentiment = round(current_sentiment - prior_sentiment, 2)
        
        # 1. Stealth Accumulation: High institutional news/sentiment, price flat or consolidating
        if delta_sentiment >= 0.30 and price_change_pct <= 1.0:
            regime = "STEALTH_ACCUMULATION"
            label = "🕵️ Stealth Accumulation"
            badge_color = "#38bdf8"
            action = "ACCUMULATE_ON_PULLBACK"
            desc = f"Institutional sentiment surge (ΔS: {delta_sentiment:+.2f}) during price consolidation ({price_change_pct:+.1f}%)."
        # 2. Climax Distribution: Retail euphoria (social sentiment high) but heavy price resistance
        elif (social_sentiment is not None and social_sentiment >= 0.75 and social_volume_surge) or (delta_sentiment <= -0.30 and price_change_pct >= 2.0):
            regime = "CLIMAX_DISTRIBUTION"
            label = "🔴 Climax Distribution / Retail Trap"
            badge_color = "#f87171"
            action = "TRIM_OR_FADE"
            desc = f"Retail social sentiment climax accompanied by distribution or negative institutional delta (ΔS: {delta_sentiment:+.2f})."
        # 3. PEAD / Momentum Alignment
        elif delta_sentiment >= 0.20 and price_change_pct >= 2.0:
            regime = "PEAD_MOMENTUM_ALIGNMENT"
            label = "🚀 PEAD Momentum Alignment"
            badge_color = "#34d399"
            action = "HOLD_AND_TRAIL"
            desc = f"Positive narrative expansion (ΔS: {delta_sentiment:+.2f}) confirmed by price momentum ({price_change_pct:+.1f}%)."
        # 4. Bearish Breakdown
        elif delta_sentiment <= -0.25 and price_change_pct <= -2.0:
            regime = "BEARISH_BREAKDOWN"
            label = "⚠️ Institutional Liquidation"
            badge_color = "#ef4444"
            action = "EXIT_DISCIPLINE"
            desc = f"Sharp negative sentiment shift (ΔS: {delta_sentiment:+.2f}) with downward price drift ({price_change_pct:+.1f}%)."
        else:
            regime = "NARRATIVE_STABLE"
            label = "⚪ Narrative Stable"
            badge_color = "#94a3b8"
            action = "MAINTAIN"
            desc = f"Sentiment change (ΔS: {delta_sentiment:+.2f}) and price return within normal variance."
            
        return {
            "symbol": symbol,
            "regime": regime,
            "label": label,
            "badge_color": badge_color,
            "action": action,
            "description": desc,
            "delta_sentiment": delta_sentiment,
            "current_sentiment": round(current_sentiment, 2),
            "prior_sentiment": round(prior_sentiment, 2),
            "price_change_pct": round(price_change_pct, 2),
        }


# Global singleton instance
news_pulse = NewsPulseEngine()

