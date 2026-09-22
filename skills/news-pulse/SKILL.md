---
name: news-pulse
description: Institutional Catalyst & Sentiment Engine for Screener. Integrates SEC filings, Tier-1 financial media, and social media sentiment signals into actionable catalyst attribution, multi-source weighting, sentiment delta tracking, and PEAD divergence telemetry.
version: 1.0.0
category: Analysis & Intelligence
tags:
  - news
  - catalyst
  - sentiment
  - pead
  - institutional
---

# News Pulse (Skill 13) - Institutional Catalyst & Sentiment Engine

The News Pulse skill provides institutional-grade intelligence on corporate catalysts, news sentiment, and retail vs. institutional divergence tracking for US equities. It bridges real-time narrative flow with quantitative market telemetry to explain price action deviations, predict post-earnings drift sustainability, and identify stealth institutional accumulation.

## Core Capabilities

1. Multi-Source Authority Hierarchy:
   - SEC Regulatory Filings (Authority: 1.00): Form 8-K, 10-Q, 10-K disclosures, insider transactions (Form 4), proxy statements (DEF 14A). Unconditional fundamental truth.
   - Company Official PR (Authority: 0.85): Business Wire, PR Newswire, GlobeNewswire corporate earnings releases, guidance revisions, M&A announcements.
   - Tier-1 Financial Media (Authority: 0.75): Wall Street Journal, Bloomberg, Reuters, Financial Times, Barron's. 1-to-3-day narrative shocks and analyst re-ratings.
   - Mainstream Financial Portals (Authority: 0.50): CNBC, MarketWatch, Yahoo Finance, Seeking Alpha.
   - Retail & Social Media (Authority: 0.25): Reddit (r/wallstreetbets, r/stocks), X (Twitter), StockTwits. Crowding sentry and climax top/squeeze detection.

2. Catalyst Taxonomy & Impact Scoring:
   - 5-Star Structural & Existential: M&A / Takeover bids, FDA drug approvals, activist stakes (13D), major strategic pivots.
   - 4-Star Fundamental Shifts: Triple-beat earnings with guidance hikes, major tier-1 product launches, mega contract awards.
   - 3-Star Tactical Momentum: Wall Street analyst upgrades with price target raises, index inclusion announcements, patent grants.
   - 2-Star Baseline Noise: Routine executive commentary, industry conferences, minor partnership updates.
   - 1-Star Speculative / Rumor: Unverified social media chatter, anonymous blog posts, retail message board speculation.

3. Sentiment & Price Divergence Telemetry:
   - Stealth Accumulation: Strong institutional/SEC news (Delta Sentiment > +0.30) during price consolidation or modest pullback (Delta Price < 0).
   - Climax Distribution: High retail euphoria (Social Sentiment > 0.80, high social volume) accompanied by heavy volume stalls or upper shadows.
   - PEAD Acceleration: Positive earnings surprise + tier-1 guidance beat confirming price drift over 5-to-20 trading sessions.
   - Earnings Deviation Attribution: Explains why price diverged from earnings beats/misses (e.g. forward guidance cuts, margin compression, decelerating ARR).

## Integration in Screener & Portfolio

- Table Grids: Screener and Portfolio tables display an Enhanced Composite Catalyst Cell featuring dual badges:
  - Quality Badge: [5-Star M&A] or [4-Star Earnings Beat]
  - Pulse Telemetry: [Sig: 85 | Primary] with interactive hover card showing source breakdown, sentiment delta (Delta S_7), and authority weight.
- Setup Scorer: Blended catalyst sub-score:
  Catalyst Score = 0.50 * Stars + 0.30 * (Signal Score / 20) + 0.20 * Sentiment Direction
- Drawers & Intelligence Center:
  - Step 6: Divergence Alert & Telemetry Card in Earnings Intelligence Center modal.
  - Card 3: News Pulse Attribution & Media Hierarchy in row inspection drawer.
  - Screen 8: News Pulse Engine Terminal with real-time ticker stream and PEAD playbook.
