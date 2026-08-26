import subprocess
import time
import json
import urllib.request
import urllib.error

# Launch Edge with remote debugging
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
proc = subprocess.Popen([
    edge_path,
    "--headless",
    "--remote-debugging-port=9222",
    "--disable-gpu",
    "file:///C:/Users/jfan/Documents/Screener/latest_report.html"
])

time.sleep(2)

try:
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    tabs = json.loads(req.read().decode('utf-8'))
    print("Edge tabs:", tabs)
    ws_url = tabs[0].get("webSocketDebuggerUrl")
    print("WebSocket URL:", ws_url)
finally:
    proc.terminate()
