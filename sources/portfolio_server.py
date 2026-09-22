"""Institutional Local Portfolio Sync & REST API Server (Port 8050).

Provides instant bi-directional persistence between the browser dashboard and:
1. data/portfolio.json (File on disk)
2. data/portfolio_monitor.db (SQLite database)

Enables zero-friction real-time portfolio management:
- POST /api/portfolio/sync: Full portfolio state persistence
- POST /api/portfolio/add: Add or update position
- POST /api/portfolio/delete: Remove position
- GET /api/portfolio: Read active live portfolio
- GET /api/status: Heartbeat and connection verification
"""

import os
import sys
import json
import socket
import logging
import datetime
import subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sources.portfolio_manager import portfolio_mgr
from sources.portfolio_monitor_engine import PortfolioMonitorEngine

logger = logging.getLogger("portfolio_server")
PORT = 8050
HOST = "127.0.0.1"


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class PortfolioAPIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/status":
            self._send_json(200, {
                "status": "online",
                "service": "Institutional Portfolio Sync Server",
                "timestamp": datetime.datetime.now().isoformat()
            })
            return

        if path == "/api/portfolio":
            try:
                data = portfolio_mgr.load_portfolio()
                self._send_json(200, {"success": True, "portfolio": data})
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})
            return

        # Static file serving for latest_report.html
        report_file = BASE_DIR / "latest_report.html"
        if (path in ["/", "/latest_report.html", "/report"]) and report_file.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            with open(report_file, "rb") as f:
                self.wfile.write(f.read())
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_body)
        except Exception:
            payload = {}

        if path == "/api/portfolio/sync":
            try:
                if not payload or "positions" not in payload:
                    self._send_json(400, {"success": False, "error": "Invalid portfolio payload"})
                    return

                # 1. Save directly to data/portfolio.json
                saved = portfolio_mgr.save_portfolio(payload)
                
                # 2. Sync to data/portfolio_monitor.db
                try:
                    monitor = PortfolioMonitorEngine()
                    monitor.sync_and_evaluate(payload)
                except Exception as ex:
                    logger.warning(f"Portfolio monitor db sync warning: {ex}")

                self._send_json(200, {
                    "success": saved,
                    "message": "Successfully persisted to data/portfolio.json & portfolio_monitor.db",
                    "positions_count": len(payload.get("positions", [])),
                    "total_nav": payload.get("total_nav")
                })
            except Exception as e:
                logger.error(f"Error in /api/portfolio/sync: {e}", exc_info=True)
                self._send_json(500, {"success": False, "error": str(e)})
            return

        if path == "/api/portfolio/delete":
            try:
                sym = (payload.get("symbol") or "").upper().strip()
                if not sym:
                    self._send_json(400, {"success": False, "error": "Missing symbol"})
                    return

                res = portfolio_mgr.delete_position(sym)
                try:
                    monitor = PortfolioMonitorEngine()
                    monitor.sync_and_evaluate(res)
                except Exception:
                    pass

                self._send_json(200, {
                    "success": True,
                    "message": f"Successfully deleted {sym} from data/portfolio.json",
                    "positions_count": len(res.get("positions", []))
                })
            except Exception as e:
                logger.error(f"Error in /api/portfolio/delete: {e}", exc_info=True)
                self._send_json(500, {"success": False, "error": str(e)})
            return

        if path == "/api/portfolio/add":
            try:
                pos = payload.get("position") or payload
                sym = (pos.get("symbol") or "").upper().strip()
                if not sym:
                    self._send_json(400, {"success": False, "error": "Missing symbol in position"})
                    return

                res = portfolio_mgr.add_or_update_position(pos)
                try:
                    monitor = PortfolioMonitorEngine()
                    monitor.sync_and_evaluate(res)
                except Exception:
                    pass

                self._send_json(200, {
                    "success": True,
                    "message": f"Successfully saved {sym} to data/portfolio.json",
                    "positions_count": len(res.get("positions", []))
                })
            except Exception as e:
                logger.error(f"Error in /api/portfolio/add: {e}", exc_info=True)
                self._send_json(500, {"success": False, "error": str(e)})
            return

        self._send_json(404, {"error": "API route not found"})

    def log_message(self, format, *args):
        # Mute standard noisy HTTP access logs
        return


def is_server_running(host: str = HOST, port: int = PORT) -> bool:
    """Check if the portfolio sync server is already responding on port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def ensure_server_running(host: str = HOST, port: int = PORT) -> bool:
    """Start the portfolio sync server in background if not already running."""
    if is_server_running(host, port):
        return True
    try:
        script_path = str(Path(__file__).resolve())
        # Spawn detached process on Windows without popup console window
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

        subprocess.Popen(
            [sys.executable, script_path, "--serve"],
            cwd=str(BASE_DIR),
            creationflags=creationflags,
            close_fds=True
        )
        return True
    except Exception as e:
        logger.warning(f"Could not spawn background portfolio sync server: {e}")
        return False


def run_server(host: str = HOST, port: int = PORT):
    server = ThreadedHTTPServer((host, port), PortfolioAPIHandler)
    logger.info(f"⚡ Institutional Portfolio Sync Server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Portfolio Sync Server shutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run_server()
