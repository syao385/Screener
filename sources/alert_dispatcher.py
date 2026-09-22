"""Multi-Channel Alert & Webhook Dispatcher (Skill 10 & 12 Phase 3).
Dispatches high-conviction signals, stop breaches, and macro circuit breakers to:
  1. Telegram Bot Webhook API (HTML formatted messages)
  2. Windows Native Desktop Toast Notifications
  3. System Audio Bells / Terminal Chimes
"""

import os
import sys
import logging
import subprocess
import requests
from typing import Dict, Any, Optional
from pathlib import Path

# Load config
try:
    from config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_NOTIFICATION_LEVEL,
        ENABLE_DESKTOP_NOTIFICATIONS,
        ENABLE_AUDIO_CHIMES,
    )
except ImportError:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
    TELEGRAM_NOTIFICATION_LEVEL = "ALL"
    ENABLE_DESKTOP_NOTIFICATIONS = True
    ENABLE_AUDIO_CHIMES = True

logger = logging.getLogger("alert_dispatcher")


class AlertDispatcher:
    """Institutional real-time alert engine connecting signals to live traders."""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.notification_level = TELEGRAM_NOTIFICATION_LEVEL.upper()
        self.enable_desktop = ENABLE_DESKTOP_NOTIFICATIONS
        self.enable_audio = ENABLE_AUDIO_CHIMES

    def configure_telegram(self, bot_token: str, chat_id: str):
        """Dynamically update Telegram credentials."""
        self.bot_token = bot_token.strip()
        self.chat_id = chat_id.strip()
        logger.info("Telegram credentials updated successfully.")

    def is_telegram_configured(self) -> bool:
        """Check if Telegram bot token and chat ID are present."""
        return bool(self.bot_token and self.chat_id and ":" in self.bot_token)

    def send_telegram(self, message_html: str, disable_web_preview: bool = True) -> bool:
        """
        Send an HTML-formatted message to the designated Telegram chat/channel.
        Returns True on success, False on failure.
        """
        if not self.is_telegram_configured():
            logger.debug("Telegram alert skipped: Bot token or Chat ID not configured.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_preview,
        }

        try:
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                logger.info("Telegram alert dispatched successfully.")
                return True
            else:
                logger.warning(f"Telegram API returned {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to transmit Telegram alert: {e}")
            return False

    def send_desktop_toast(self, title: str, body: str):
        """Trigger Windows native desktop toast notification via PowerShell."""
        if not self.enable_desktop:
            return

        clean_title = title.replace('"', '`"').replace("'", "’")
        clean_body = body.replace('"', '`"').replace("'", "’")

        # Windows PowerShell Toast Notification script (zero extra pip packages required)
        ps_script = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{clean_title}")) > $null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{clean_body}")) > $null
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Institutional Screener")
        $notification = [Windows.UI.Notifications.ToastNotification]::new($template)
        $notifier.Show($notification)
        """

        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.debug(f"Desktop notification fallback triggered: {e}")

    def play_sound(self, frequency: int = 880, duration_ms: int = 250):
        """Play short audio beep via console / powershell."""
        if not self.enable_audio:
            return
        try:
            if sys.platform == "win32":
                import winsound
                winsound.Beep(frequency, duration_ms)
            else:
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            pass

    def dispatch(
        self,
        title: str,
        message: str,
        urgency: str = "NORMAL",
        telegram_html: Optional[str] = None,
        sound: bool = True,
    ) -> Dict[str, Any]:
        """
        Unified dispatch method sending to all configured channels.
        urgency: 'CRITICAL', 'WARNING', 'OPPORTUNITY', 'INFO', 'NORMAL'
        """
        results = {"desktop": False, "sound": False, "telegram": False}

        # 1. Desktop Notification
        try:
            self.send_desktop_toast(title, message)
            results["desktop"] = True
        except Exception as e:
            logger.debug(f"Desktop dispatch error: {e}")

        # 2. Audio Chime
        if sound and self.enable_audio:
            freq = 1200 if urgency == "CRITICAL" else 880
            dur = 400 if urgency == "CRITICAL" else 200
            self.play_sound(frequency=freq, duration_ms=dur)
            results["sound"] = True

        # 3. Telegram Webhook
        if self.notification_level != "OFF":
            if self.notification_level == "URGENT_ONLY" and urgency not in ["CRITICAL", "WARNING"]:
                pass
            else:
                html_body = telegram_html or f"<b>{title}</b>\n\n{message}"
                results["telegram"] = self.send_telegram(html_body)

        return results

    # =========================================================================
    # Specialized Institutional Alert Builders
    # =========================================================================

    def alert_hard_stop_breach(self, symbol: str, current_price: float, stop_price: float, shares: int, loss_dollar: float):
        """Fires immediate critical alert when a protective stop is breached."""
        title = f"🚨 HARD STOP TRIGGERED: {symbol}"
        msg = f"{symbol} breached protective stop at ${stop_price:.2f} (Current: ${current_price:.2f}). EXIT {shares} shares immediately."
        
        tg_html = (
            f"🚨 <b>HARD STOP TRIGGERED: {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Action:</b> IMMEDIATE EXIT\n"
            f"• <b>Current Price:</b> <code>${current_price:.2f}</code>\n"
            f"• <b>Stop Level:</b> <code>${stop_price:.2f}</code>\n"
            f"• <b>Position Size:</b> {shares} shares\n"
            f"• <b>Est Loss:</b> -${abs(loss_dollar):,.2f}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Execution Desk: Please submit exit order in Fidelity ATP immediately.</i>"
        )
        return self.dispatch(title, msg, urgency="CRITICAL", telegram_html=tg_html)

    def alert_sector_invalidation(self, symbol: str, sector: str, flow_score: int, flow_action: str):
        """Fires alert when parent sector ETF deteriorates into distribution."""
        title = f"⚠️ SECTOR INVALIDATION: {symbol}"
        msg = f"{symbol} parent sector ({sector}) deteriorated to {flow_action} (Flow: {flow_score}/100). Recommended 50% trim."

        tg_html = (
            f"⚠️ <b>SECTOR FLOW INVALIDATION: {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Sector:</b> {sector} (Flow: {flow_score}/100)\n"
            f"• <b>Trigger:</b> Institutional Distribution Flow\n"
            f"• <b>Recommendation:</b> Pre-emptive 50% Position Trim\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Protect capital before individual stock breakdown confirms.</i>"
        )
        return self.dispatch(title, msg, urgency="WARNING", telegram_html=tg_html)

    def alert_breakout_trigger(self, symbol: str, entry_price: float, stop_price: float, rvol: float, shares: int, setup_name: str):
        """Fires when high-conviction screener setup clears pivot with volume surge."""
        title = f"🚀 BREAKOUT TRIGGER: {symbol}"
        msg = f"{symbol} {setup_name} pivot cleared at ${entry_price:.2f} with RVOL {rvol:.2f}x! Sized: {shares} shares (Stop ${stop_price:.2f})."

        tg_html = (
            f"🚀 <b>BREAKOUT TRIGGER: {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>Setup:</b> {setup_name}\n"
            f"• <b>Entry Pivot:</b> <code>${entry_price:.2f}</code>\n"
            f"• <b>Volume Surge (RVOL):</b> <code>{rvol:.2f}x</code>\n"
            f"• <b>Calculated Sizing:</b> <b>{shares} shares</b>\n"
            f"• <b>Protective Stop:</b> <code>${stop_price:.2f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Order staged in Fidelity Trade Execution Desk.</i>"
        )
        return self.dispatch(title, msg, urgency="OPPORTUNITY", telegram_html=tg_html)

    def alert_macro_circuit_breaker(self, reason: str, details: str):
        """Fires when macro overlay indicates red flags (cancel buy orders)."""
        title = "🔴🔴🔴 MACRO CIRCUIT BREAKER"
        msg = f"CRITICAL: Cancel all new buy orders. Reason: {reason}"

        tg_html = (
            f"🔴🔴🔴 <b>MACRO CIRCUIT BREAKER: BUY HALT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Status:</b> CANCEL ALL NEW BUY ORDERS\n"
            f"<b>Primary Cause:</b> {reason}\n"
            f"<b>Details:</b> {details}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Capital preservation rule enforced (Oil/Yield/Geopolitics).</i>"
        )
        return self.dispatch(title, msg, urgency="CRITICAL", telegram_html=tg_html)


# Global singleton instance
alert_dispatcher = AlertDispatcher()
