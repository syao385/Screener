"""Economic Calendar module: Extracts real-time US economic events from Finviz & ForexFactory."""

import json
import logging
import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from config import TZ_EST
from sources.fallback_manager import resilient_session

logger = logging.getLogger("economic_calendar")

class EconomicCalendar:
    """Fetches real-time US economic events sorted by Time then Impact (Zero fake/static data)."""

    def _sort_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort events by Time (ascending), then by Impact (High > Medium > Low)."""
        impact_order = {"High": 1, "Medium": 2, "Low": 3}

        def get_sort_key(ev):
            time_str = ev.get("time", "")
            impact = ev.get("impact", "Low")
            try:
                clean_t = time_str.replace(" EST", "").replace(" (Premarket)", "").strip()
                dt = datetime.datetime.strptime(clean_t, "%I:%M %p")
                minutes = dt.hour * 60 + dt.minute
            except Exception:
                minutes = 9999
            return (minutes, impact_order.get(impact, 99))

        events.sort(key=get_sort_key)
        return events

    def get_today_events(self, target_date: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Get today's US economic events sorted by Time then Impact."""
        if target_date is None:
            now_est = datetime.datetime.now(TZ_EST)
            target_date = now_est.date()

        events = []

        # 1. Primary Source: Finviz Economic Calendar (Embedded Real-Time JSON)
        try:
            url = "https://finviz.com/calendar.ashx"
            resp = resilient_session.get(url, timeout=6)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for s in soup.find_all("script"):
                    content = s.string or s.text
                    if content and '"entries":[' in content and "calendarId" in content:
                        data = json.loads(content.strip())
                        all_entries = data.get("data", {}).get("entries", [])
                        for e in all_entries:
                            dt_str = e.get("date", "")
                            if not dt_str:
                                continue
                            
                            ev_date_str = dt_str[:10]
                            try:
                                ev_date = datetime.datetime.strptime(ev_date_str, "%Y-%m-%d").date()
                            except Exception:
                                continue

                            if ev_date == target_date:
                                imp = e.get("importance", 1)
                                imp_label = "High" if imp == 3 else ("Medium" if imp == 2 else "Low")
                                
                                # Format time to EST
                                time_part = dt_str[11:16] if len(dt_str) >= 16 else "00:00"
                                try:
                                    ev_time = datetime.datetime.strptime(time_part, "%H:%M")
                                    time_formatted = ev_time.strftime("%I:%M %p EST").lstrip("0")
                                    is_premarket = ev_time.hour < 9 or (ev_time.hour == 9 and ev_time.minute < 30)
                                except Exception:
                                    time_formatted = f"{time_part} EST"
                                    is_premarket = True

                                forecast = e.get("forecast")
                                prior = e.get("previous")
                                actual = e.get("actual")

                                events.append({
                                    "time": time_formatted,
                                    "title": e.get("event") or "Economic Event",
                                    "event": e.get("event") or "Economic Event",
                                    "impact": imp_label,
                                    "forecast": str(forecast) if forecast is not None else "—",
                                    "prior": str(prior) if prior is not None else "—",
                                    "actual": str(actual) if actual is not None else "—",
                                    "is_premarket": is_premarket,
                                    "source": "Finviz Economic Calendar (finviz.com/calendar.ashx)",
                                })

                if events:
                    sorted_events = self._sort_events(events)
                    logger.info(f"Retrieved {len(sorted_events)} economic events for {target_date} from Finviz.")
                    return sorted_events
        except Exception as e:
            logger.debug(f"Finviz economic calendar parsing error: {e}")

        # 2. Backup Source: ForexFactory XML Feed
        try:
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
            resp = resilient_session.get(url, timeout=5)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "xml")
                for e in soup.find_all("event"):
                    country = e.find("country")
                    if not country or country.text.strip() != "USD":
                        continue

                    date_tag = e.find("date")
                    if not date_tag:
                        continue

                    raw_date_str = date_tag.text.strip()
                    try:
                        ev_date = datetime.datetime.strptime(raw_date_str, "%m-%d-%Y").date()
                    except Exception:
                        continue

                    if ev_date == target_date:
                        impact = e.find("impact").text.strip().capitalize() if e.find("impact") else "Medium"
                        title = e.find("title").text.strip() if e.find("title") else "Macro Release"
                        time_str = e.find("time").text.strip() if e.find("time") else "All Day"
                        forecast = e.find("forecast").text.strip() if e.find("forecast") else "—"
                        previous = e.find("previous").text.strip() if e.find("previous") else "—"
                        is_premarket = "am" in time_str.lower() or time_str.startswith("8:") or time_str.startswith("9:")

                        events.append({
                            "time": f"{time_str} EST",
                            "title": title,
                            "impact": impact,
                            "forecast": forecast if forecast else "—",
                            "prior": previous if previous else "—",
                            "actual": "—",
                            "is_premarket": is_premarket,
                            "source": "ForexFactory XML Calendar",
                        })

                if events:
                    sorted_events = self._sort_events(events)
                    logger.info(f"Retrieved {len(sorted_events)} economic events for {target_date} from ForexFactory.")
                    return sorted_events
        except Exception as e:
            logger.debug(f"ForexFactory calendar parsing error: {e}")

        return self._sort_events(events)

economic_cal = EconomicCalendar()
