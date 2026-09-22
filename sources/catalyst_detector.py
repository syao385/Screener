"""Catalyst Intelligence Engine: Multi-source headline detection, NLP classification, and 1★-5★ rating."""

import re
import logging
import datetime
import yfinance as yf
from bs4 import BeautifulSoup
from typing import Dict, Tuple, List, Optional, Any
from config import TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("catalyst_detector")

# Negative news patterns that disqualify a stock immediately
NEGATIVE_PATTERNS = [
    r"\boffering\b", r"\bdilution\b", r"\bpublic offering\b", r"\bdirect offering\b",
    r"\bsecondary offering\b", r"\bpricing of offering\b", r"\bcuts guidance\b",
    r"\blowers guidance\b", r"\bslashes guidance\b", r"\bmisses estimates\b",
    r"\bmisses eps\b", r"\bmisses revenue\b", r"\bwarns on\b", r"\bdownside\b",
    r"\blawsuit\b", r"\bsec investigation\b", r"\bsubpoena\b", r"\bcfo departs\b",
    r"\bcfo resigns\b", r"\bceo steps down\b", r"\bprobe\b", r"\bdelisting\b"
]

# Fluff commentary patterns that carry 1-star noise
FLUFF_PATTERNS = [
    "why is", "is it too late", "should you buy", "3 reasons to", "forget",
    "better buy", "top stocks to", "millionaire maker", "motley fool",
    "zacks rank", "is now a good time", "could surge", "prediction for",
    "wall street is bullish", "what makes", "heres why"
]

# High-impact Tier-1 Patterns (5.0★ / 4.5★) - Verified actual event releases
TIER1_PATTERNS = [
    (r"\b(fda approval|fda approves|cleared by fda|breakthrough therapy|phase 3|primary endpoint)\b", "FDA Approval", 5.0),
    (r"\b(acquired by|to acquire|to be acquired|acquisition of|merger agreement|buyout offer|takeover)\b", "M&A / Buyout", 5.0),
    (r"\b(beat(s)? (and|&) raise|eps beat|revenue beat|beats on earnings|blowout quarter|raises (fy|full-year|annual|profit)?\s*(guidance|outlook)|record (quarterly|annual) revenue|best day .* after earnings|(soars|jumps|surges|rallies|pops) (after|following|on)\s+(q[1-4]\s+|quarterly\s+)?(earnings|results)|earnings\s+(beat|surprise|crush|blowout|surge)|(beat|beats|beating|top|tops|topping|crush|crushes)\s+(earnings|eps|revenue|estimates|expectations|street))\b", "Earnings Beat & Raise", 5.0),
    (r"\b((after|following|post|on)\s+earnings|(reports|posts|delivers|announces)\s+(fiscal\s+)?(q[1-4]\s+|quarterly\s+|full-year\s+)?(results|earnings|profit|net income|revenue)|(q[1-4]|quarterly|full-year)\s+(earnings|results|profit|revenue)\s+(beat|top|surge|rise|jump|crush|soar)|(fiscal\s+)?q[1-4]\s+earnings(\s+snapshot|\s+release)?|(q[1-4]|quarterly)\s+net\s+income\s+(rises|jumps|surges)|(q[1-4]|quarterly)\s+profit\s+beats|(swings|swinging)\s+to\s+(quarterly\s+)?profit)\b", "Earnings Release", 4.5),
]

# Earnings Preview / Anticipation Patterns (2.0★) - Previews, calendars, and expectations before the event
EARNINGS_PREVIEW_PATTERNS = [
    (r"\b(earnings preview|earnings expectation(s)?|upcoming earnings|to report (q[1-4]|earnings|quarterly|results)|reports earnings on|reports results on|earnings on deck|ahead of earnings|earnings scheduled|undervalued on (cash flow and )?earnings|before earnings|what to expect from.*earnings|earnings calendar|earnings date|sets date for)\b", "Earnings Preview", 2.0),
]

# Tier-2 Patterns (4.0★)
TIER2_PATTERNS = [
    (r"\b(awarded|wins|lands) (\$\d+|multimillion|billion|defense contract|major contract|deal with)\b", "Major Contract", 4.0),
    (r"\b(upgrades to buy|upgraded to overweight|upgraded to outperform|raises price target|price target raised to|initiates with buy)\b", "Analyst Upgrade", 4.0),
    (r"\b(partnership with|strategic alliance with|collaboration with)\b", "Partnership ($)", 3.5),
]

# Tier-3 Patterns (3.0★)
TIER3_PATTERNS = [
    (r"\b(launches|unveils|patent granted|commercial launch|new product|phase 2|phase 1)\b", "Product / Trial Expansion", 3.0),
]

# Sector Sympathy Patterns (2.0★)
SECTOR_SYMPATHY_PATTERNS = [
    (r"\b(rallies with|sympathy move|gains alongside|peers rise|sector gains|chips rally|ev rally)\b", "Sector Sympathy", 2.0),
    (r"\b(added to|inclusion in|joins s&p|joins russell)\b", "Index Inclusion", 2.5),
]

# Common English stop words that match 1-3 letter tickers to avoid false positives
COMMON_TICKER_STOPWORDS = {
    "ON", "AI", "IT", "BE", "GO", "SO", "ALL", "CAN", "FOR", "NOW", "A", "AN",
    "AT", "BY", "IN", "IS", "OR", "TO", "UP", "HE", "ME", "WE", "AM", "AS",
    "DO", "IF", "MY", "NO", "US", "SEE", "OUT", "ARE", "BIG", "TOP", "NEW",
    "DAY", "KEY", "GET", "RUN", "SET", "PAY", "BID", "BUY", "NOT", "WHY", "HOW"
}

# Known aliases for high-volume / mega-cap equities
KNOWN_TICKER_ALIASES: Dict[str, List[str]] = {
    "NVDA": ["nvidia"],
    "AAPL": ["apple"],
    "MSFT": ["microsoft"],
    "AMZN": ["amazon"],
    "GOOGL": ["google", "alphabet"],
    "GOOG": ["google", "alphabet"],
    "META": ["meta", "facebook"],
    "TSLA": ["tesla"],
    "TSM": ["tsmc", "taiwan semi"],
    "SMCI": ["super micro", "supermicro"],
    "AMD": ["amd", "advanced micro"],
    "AVGO": ["broadcom"],
    "ORCL": ["oracle"],
    "PLTR": ["palantir"],
    "NFLX": ["netflix"],
    "BABA": ["alibaba"],
    "DIS": ["disney", "walt disney"],
    "BA": ["boeing"],
    "INTC": ["intel"],
    "QCOM": ["qualcomm"],
    "MU": ["micron"],
    "ARM": ["arm holdings"],
    "LLY": ["eli lilly", "lilly"],
    "NVO": ["novo nordisk"],
    "WBD": ["warner bros", "discovery"],
    "PARA": ["paramount"],
    "CRWD": ["crowdstrike"],
    "MSTR": ["microstrategy"],
    "COIN": ["coinbase"],
}

class CatalystDetector:
    """Classifies and rates market catalysts on a 1.0★ to 5.0★ institutional scale."""

    def __init__(self):
        # ticker -> (category, stars, headline, url, is_positive, date_str)
        self._cache: Dict[str, Tuple[str, float, str, str, bool, str]] = {}

    def _clean_company_name(self, name: str) -> List[str]:
        """Extract clean root company name stems for text matching."""
        if not name:
            return []
        name_clean = re.sub(r"[,.\-–—/\\&]", " ", name).strip()
        pattern = r"\b(incorporated|corporation|corp|inc|limited|ltd|llc|plc|co|company|holdings|holding|group|class [a-z]|cl [a-z]|adr)\b"
        stem = re.sub(pattern, "", name_clean, flags=re.IGNORECASE).strip()
        stems = []
        if len(stem) >= 3:
            stems.append(stem.lower())
            words = stem.split()
            if len(words) > 1 and len(words[0]) >= 4 and words[0].lower() not in {
                "general", "united", "american", "national", "global", "first", "international", "western", "southern", "northern", "eastern"
            }:
                stems.append(words[0].lower())
        return list(set(stems))

    def _is_relevant(self, ticker: str, text: str, company_name: str = "") -> bool:
        """Verify if text specifically references the ticker, its known aliases, or its company name."""
        if not text:
            return False
        sym = ticker.upper().strip()
        text_lower = text.lower()

        # 1. Explicit ticker symbols: $NVDA, (NVDA), :NVDA, NVDA:
        if f"${sym.lower()}" in text_lower or f"({sym.lower()})" in text_lower or f":{sym.lower()}" in text_lower or f"{sym.lower()}:" in text_lower:
            return True
        if f"{sym.lower()}'s" in text_lower or f"{sym.lower()}’s" in text_lower:
            return True

        # 2. Standalone ticker word
        if sym not in COMMON_TICKER_STOPWORDS and len(sym) >= 2:
            if re.search(rf"\b{re.escape(sym)}\b", text, re.IGNORECASE):
                return True
        elif sym in COMMON_TICKER_STOPWORDS:
            # For short common words, require exact case match
            if re.search(rf"\b{re.escape(sym)}\b", text):
                return True

        # 3. Known aliases
        for alias in KNOWN_TICKER_ALIASES.get(sym, []):
            if re.search(rf"\b{re.escape(alias)}\b", text_lower):
                return True

        # 4. Clean company name stems
        for stem in self._clean_company_name(company_name):
            if re.search(rf"\b{re.escape(stem)}\b", text_lower):
                return True

        return False

    def _classify_headline(
        self,
        ticker: str,
        headline: str,
        url: str = "",
        summary: str = "",
        company_name: str = ""
    ) -> Tuple[str, float, str, str, bool]:
        """Classify and score a single headline with strict company relevance checks."""
        clean_hl = headline.strip()
        hl_lower = clean_hl.lower()
        clean_sym = ticker.upper().strip()
        full_text = f"{clean_hl} {summary}".strip()
        is_rel = self._is_relevant(clean_sym, full_text, company_name)

        # 1. Check if headline is explicit fatal negative / dilution for THIS ticker
        for neg_pat in NEGATIVE_PATTERNS:
            if re.search(neg_pat, hl_lower):
                # Direct offering/dilution is an immediate disqualifier if relevant or generic corporate announcement
                if any(w in hl_lower for w in ["offering", "dilution", "secondary offering", "public offering", "pricing of offering", "direct offering"]):
                    if is_rel or any(phrase in hl_lower for phrase in ["company announces", "announces pricing", "prices public", "prices direct", "files for offering", "prices offering"]):
                        return ("Dilution / Negative", 0.0, clean_hl, url, False)
                # Other negative events (e.g. delisting, lawsuit, probe) must specifically mention this ticker
                if is_rel:
                    return ("Dilution / Negative", 0.0, clean_hl, url, False)

        # 2. Check if generic fluff
        if any(fluff in hl_lower for fluff in FLUFF_PATTERNS):
            return ("Generic Commentary", 1.0, clean_hl, url, False)

        # 3. Company-specific High-impact Catalysts (Require verified relevance to ticker)
        if is_rel:
            # Check Earnings Previews / Anticipation First (2.0★)
            for pat, cat_name, stars in EARNINGS_PREVIEW_PATTERNS:
                if re.search(pat, hl_lower):
                    return (cat_name, stars, clean_hl, url, True)

            # Tier 1 (5.0★ / 4.5★)
            for pat, cat_name, stars in TIER1_PATTERNS:
                if re.search(pat, hl_lower):
                    return (cat_name, stars, clean_hl, url, True)

            # Tier 2 (4.0★ / 3.5★)
            for pat, cat_name, stars in TIER2_PATTERNS:
                if re.search(pat, hl_lower):
                    return (cat_name, stars, clean_hl, url, True)

            # Tier 3 (3.0★)
            for pat, cat_name, stars in TIER3_PATTERNS:
                if re.search(pat, hl_lower):
                    return (cat_name, stars, clean_hl, url, True)

        # 4. Sector Sympathy / Index Inclusion (2.0★ - 2.5★)
        for pat, cat_name, stars in SECTOR_SYMPATHY_PATTERNS:
            if re.search(pat, hl_lower):
                return (cat_name, stars, clean_hl, url, True)

        # 5. Company mentioned directly in news momentum (2.5★)
        if is_rel:
            return ("News Momentum", 2.5, clean_hl, url, True)

        # 6. Headline does not mention or relate to this ticker at all -> Discard
        return ("Unrelated", 0.0, clean_hl, url, False)

    def detect_catalyst(self, ticker: str, company_name: str = "", earnings_date: str = "") -> Tuple[str, float, str, str, bool, str]:
        """
        Detect and arbitrate the best catalyst across Yahoo Finance, Finviz, and SEC/Earnings.
        Returns: (category, stars, headline, url, is_positive, date_str)
        """
        clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
        cache_key = f"{clean_sym}_{company_name}_{earnings_date}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        if clean_sym in self._cache and not earnings_date:
            return self._cache[clean_sym]

        # Fast bypass for ETFs and index tracking funds
        known_etfs = {
            "SOXL", "QQQ", "SPY", "SMH", "IWM", "GDXJ", "GLDM", "SILJ", "SLV",
            "COPX", "OIH", "MAGS", "SPGP", "SPMO", "CURE", "AVLV", "IEMG",
            "XLE", "XLF", "XLK", "XLV", "XLY", "XLP", "XLU", "XLI", "XLB", "VNQ", "ARKK", "TQQQ", "SQQQ"
        }
        if clean_sym.upper() in known_etfs:
            res = ("ETF / Macro", 1.0, f"{clean_sym} Index Basket", f"https://finance.yahoo.com/quote/{clean_sym}", True, "Active")
            self._cache[cache_key] = res
            self._cache[clean_sym] = res
            return res

        candidate_catalysts: List[Tuple[str, float, str, str, bool, str]] = []
        now_est = datetime.datetime.now(TZ_EST)
        today_est = now_est.date()
        
        # Calculate strict freshness cutoff:
        # Mon (weekday 0): Friday (3 days ago)
        # Sat/Sun (5, 6): Friday (1-2 days ago)
        # Tue-Fri (1-4): Yesterday (1 day ago)
        if now_est.weekday() == 0:
            cutoff_date = today_est - datetime.timedelta(days=3)
        elif now_est.weekday() in (5, 6):
            cutoff_date = today_est - datetime.timedelta(days=(now_est.weekday() - 4))
        else:
            cutoff_date = today_est - datetime.timedelta(days=1)

        # 1. Check in-memory Earnings Calendar
        has_confirmed_earnings = False
        earn_date_label = ""
        try:
            from sources.earnings_calendar import earnings_cal
            full_earn = earnings_cal.get_earnings_dashboard() if hasattr(earnings_cal, "get_earnings_dashboard") else earnings_cal.get_full_calendar()
            for k in ("today_bmo", "today_amc", "yesterday_amc"):
                for row in full_earn.get(k, []):
                    if row.get("ticker") == clean_sym:
                        has_confirmed_earnings = True
                        earn_date_label = f"{today_est.strftime('%b %d')} (Today)" if "today" in k else (today_est - datetime.timedelta(days=1)).strftime("%b %d")
                        break
                if has_confirmed_earnings:
                    break
        except Exception as e:
            logger.debug(f"Error checking in-memory earnings for {clean_sym}: {e}")

        # Also check passed earnings_date (e.g. "Sep 09 b", "Sep 08 a", "Sep 09 (Today)")
        if earnings_date and earnings_date != "—":
            today_month_day = today_est.strftime("%b %d")
            yest_month_day = (today_est - datetime.timedelta(days=1)).strftime("%b %d")
            if today_month_day in earnings_date or "Today" in earnings_date:
                has_confirmed_earnings = True
                if not earn_date_label:
                    earn_date_label = f"{today_month_day} (Today)"
            elif yest_month_day in earnings_date or "yesterday" in str(earnings_date).lower():
                has_confirmed_earnings = True
                if not earn_date_label:
                    earn_date_label = yest_month_day

        # 2. Check Yahoo Finance News Stream (PR Newswire / BusinessWire / Reuters)
        try:
            yf_ticker = yf.Ticker(clean_sym)
            news_list = yf_ticker.news
            if news_list:
                for item in news_list[:8]:
                    title = item.get("title")
                    link = item.get("link")
                    summary = item.get("summary") or item.get("description") or ""
                    
                    if isinstance(item.get("content"), dict):
                        c_dict = item["content"]
                        title = title or c_dict.get("title")
                        summary = summary or c_dict.get("summary") or c_dict.get("description") or ""
                        link = link or c_dict.get("canonicalUrl", {}).get("url") or c_dict.get("clickThroughUrl", {}).get("url")

                    # Parse publication timestamp
                    pub_dt = None
                    pt = item.get("providerPublishTime")
                    if pt:
                        pub_dt = datetime.datetime.fromtimestamp(pt, tz=datetime.timezone.utc).astimezone(TZ_EST)
                    elif isinstance(item.get("content"), dict):
                        pd_str = item["content"].get("pubDate")
                        if pd_str:
                            try:
                                pub_dt = datetime.datetime.fromisoformat(pd_str.replace("Z", "+00:00")).astimezone(TZ_EST)
                            except Exception:
                                pass

                    if title:
                        scored = self._classify_headline(
                            clean_sym,
                            title,
                            link or f"https://finance.yahoo.com/quote/{clean_sym}",
                            summary=summary,
                            company_name=company_name
                        )
                        # Skip unrelated news items completely
                        if scored[0] == "Unrelated" or (scored[1] == 0.0 and scored[4] is False and scored[0] != "Dilution / Negative"):
                            continue

                        # Only consider headlines published within the freshness window as primary catalysts
                        if pub_dt and pub_dt.date() >= cutoff_date:
                            pub_str = pub_dt.strftime("%b %d")
                            if pub_dt.date() == today_est:
                                pub_str = f"{pub_dt.strftime('%b %d')} (Today)"
                            
                            c_cat, c_stars, c_hl, c_url, c_pos = scored
                            # If company had confirmed earnings today/yesterday and headline discusses earnings or strong performance
                            if has_confirmed_earnings and c_pos:
                                hl_lower = c_hl.lower()
                                if any(w in hl_lower for w in ["earnings", "results", "quarter", "q1", "q2", "q3", "q4", "profit", "net income"]):
                                    if any(w in hl_lower for w in ["beat", "raise", "best day", "surge", "jump", "soar", "top", "rally", "pops"]):
                                        c_cat = "Earnings Beat & Raise"
                                        c_stars = 5.0
                                    else:
                                        c_cat = "Earnings Release"
                                        c_stars = max(c_stars, 4.5)

                            candidate_catalysts.append((c_cat, c_stars, c_hl, c_url, c_pos, pub_str))
        except Exception as e:
            logger.debug(f"Error checking Yahoo news for {clean_sym}: {e}")

        # 3. Check Finviz News Stream (Fallback when Yahoo News lacks Tier-1 events; skip on weekends to prevent 429 rate limits)
        if (now_est.weekday() < 5) and (not candidate_catalysts or not any(c[1] >= 4.0 for c in candidate_catalysts)):
            try:
                resp = resilient_session.get(f"https://finviz.com/quote.ashx?t={clean_sym}", timeout=5)
                if resp and resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    news_table = soup.find("table", id="news-table") or soup.find("table", class_="fullview-news-outer")
                    if news_table:
                        last_seen_date = today_est
                        for tr in news_table.find_all("tr")[:10]:
                            a_tag = tr.find("a")
                            td_date = tr.find("td")
                            if not a_tag:
                                continue
                            f_title = a_tag.text.strip()
                            f_link = a_tag.get("href", "")
                            if f_link.startswith("/"):
                                f_link = f"https://finviz.com{f_link}"
                            
                            d_text = td_date.text.strip() if td_date else ""
                            is_today = "today" in d_text.lower() or len(d_text.split()) == 1
                            is_recent = is_today
                            if not is_today and "-" in d_text:
                                try:
                                    f_d_part = d_text.split()[0]
                                    parsed_d = datetime.datetime.strptime(f_d_part, "%b-%d-%y").date()
                                    last_seen_date = parsed_d
                                    is_recent = parsed_d >= cutoff_date
                                except Exception:
                                    is_recent = False
                            elif not is_today:
                                is_recent = last_seen_date >= cutoff_date

                            if is_recent and f_title:
                                scored = self._classify_headline(
                                    clean_sym,
                                    f_title,
                                    f_link or f"https://finance.yahoo.com/quote/{clean_sym}",
                                    summary="",
                                    company_name=company_name
                                )
                                if scored[0] != "Unrelated" and (scored[1] > 0.0 or scored[0] == "Dilution / Negative"):
                                    c_cat, c_stars, c_hl, c_url, c_pos = scored
                                    if has_confirmed_earnings and c_pos:
                                        hl_lower = c_hl.lower()
                                        if any(w in hl_lower for w in ["earnings", "results", "quarter", "q1", "q2", "q3", "q4", "profit", "net income"]):
                                            if any(w in hl_lower for w in ["beat", "raise", "best day", "surge", "jump", "soar", "top", "rally", "pops"]):
                                                c_cat = "Earnings Beat & Raise"
                                                c_stars = 5.0
                                            else:
                                                c_cat = "Earnings Release"
                                                c_stars = max(c_stars, 4.5)
                                    pub_lbl = f"{today_est.strftime('%b %d')} (Today)" if is_today else today_est.strftime("%b %d")
                                    candidate_catalysts.append((c_cat, c_stars, c_hl, c_url, c_pos, pub_lbl))
            except Exception as e:
                logger.debug(f"Error checking Finviz news for {clean_sym}: {e}")

        # If company had confirmed earnings but no media headline was found or matched earnings, inject official earnings report
        if has_confirmed_earnings:
            has_media_earnings = any("Earnings" in c[0] for c in candidate_catalysts)
            if not has_media_earnings:
                earn_lbl = earn_date_label or f"{today_est.strftime('%b %d')} (Today)"
                candidate_catalysts.append((
                    "Earnings Release",
                    5.0,
                    f"Official Earnings Report filed ({earn_lbl})",
                    f"https://finance.yahoo.com/quote/{clean_sym}",
                    True,
                    earn_lbl
                ))

        # 3. Arbitrate across all fresh catalysts
        if candidate_catalysts:
            # If any is fatal negative, return negative immediately (disqualification)
            negatives = [c for c in candidate_catalysts if not c[4] and c[1] == 0.0 and c[0] == "Dilution / Negative"]
            if negatives:
                selected = negatives[0]
                self._cache[cache_key] = selected
                self._cache[clean_sym] = selected
                return selected

            # Otherwise, pick fresh catalyst with the highest stars (prioritizing real headlines over generic placeholders if stars are equal)
            def _arbitration_rank(c: Tuple[str, float, str, str, bool, str]):
                stars = c[1]
                is_today = 1 if "Today" in c[5] else 0
                is_real_headline = 1 if not c[2].startswith("Official Earnings Report filed") else 0
                return (stars, is_today, is_real_headline)

            candidate_catalysts.sort(key=_arbitration_rank, reverse=True)
            selected = candidate_catalysts[0]
            self._cache[cache_key] = selected
            self._cache[clean_sym] = selected
            return selected

        # 4. Default: If no company-specific news in past 48-72h, stock is moving on Technical / Macro Momentum (1.0 Star)
        selected = ("Technical / Macro", 1.0, f"{clean_sym} Technical / Momentum Movement", f"https://finance.yahoo.com/quote/{clean_sym}", True, "Recent")
        self._cache[cache_key] = selected
        self._cache[clean_sym] = selected
        return selected

    def detect_catalyst_rich(self, ticker: str, company_name: str = "", earnings_date: str = "") -> Dict[str, Any]:
        """Detect catalyst and return unified rich dictionary with News Pulse signals."""
        cat, stars, hl, url, is_pos, dt = self.detect_catalyst(ticker, company_name, earnings_date=earnings_date)
        
        # Determine source type & authority
        source_type = "FINANCIAL_MEDIA"
        url_lower = str(url).lower()
        hl_lower = str(hl).lower()
        if "sec.gov" in url_lower or "10-q" in hl_lower or "10-k" in hl_lower or "8-k" in hl_lower:
            source_type = "SEC_EDGAR"
        elif "businesswire" in url_lower or "prnewswire" in url_lower or "globenewswire" in url_lower:
            source_type = "PRESS_RELEASE"
        elif "reuters" in url_lower:
            source_type = "REUTERS"
        elif "bloomberg" in url_lower:
            source_type = "BLOOMBERG"
        elif "wsj" in url_lower or "wall street journal" in hl_lower:
            source_type = "WSJ"
        elif "Earnings Release" in cat or "Earnings Beat" in cat:
            source_type = "PRESS_RELEASE"

        from sources.news_pulse import news_pulse
        sentiment_score = 0.8 if is_pos and stars >= 3.0 else (0.2 if is_pos else -0.8)
        sig = news_pulse.compute_signal_score(
            relevance=90.0 if stars >= 4.0 else (75.0 if stars >= 2.5 else 40.0),
            novelty=85.0 if "Today" in dt else 60.0,
            authority_or_source=source_type,
            sentiment=sentiment_score
        )
        comp = news_pulse.compute_composite_catalyst_score(
            pattern_stars=stars,
            source=source_type,
            sentiment_score=sentiment_score
        )
        
        driver_type = "PRIMARY_DRIVER" if stars >= 4.0 else ("CONTRIBUTING_FACTOR" if stars >= 2.5 else "COINCIDENTAL")
        
        return {
            "ticker": ticker,
            "category": cat,
            "stars": stars,
            "blended_score": comp["blended_score"],
            "signal_score": sig["composite_score"],
            "authority": sig["authority"],
            "sentiment_score": sentiment_score,
            "source_type": source_type,
            "driver_type": driver_type,
            "headline": hl,
            "url": url,
            "is_positive": is_pos,
            "date_str": dt,
        }

catalyst_detector = CatalystDetector()


