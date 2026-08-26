import subprocess
import time
import json
import urllib.request
import urllib.error
import socket
import hashlib
import base64
import struct

# Simple WS client in standard library
def ws_connect(url):
    # url: ws://127.0.0.1:9222/devtools/page/...
    parts = url.replace("ws://", "").split("/", 1)
    host_port = parts[0].split(":")
    host = host_port[0]
    port = int(host_port[1])
    path = "/" + parts[1]
    
    s = socket.create_connection((host, port))
    key = base64.b64encode(b"0123456789abcdef").decode('utf-8')
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n\r\n"
    )
    s.sendall(req.encode('utf-8'))
    resp = s.recv(4096)
    return s

def ws_send(s, msg):
    payload = msg.encode('utf-8')
    length = len(payload)
    # Masked frame from client
    header = bytearray([0x81])
    mask = b"\x12\x34\x56\x78"
    if length <= 125:
        header.append(0x80 | length)
    elif length <= 65535:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    
    masked_payload = bytearray(length)
    for i in range(length):
        masked_payload[i] = payload[i] ^ mask[i % 4]
    
    s.sendall(header + mask + masked_payload)

def ws_recv(s):
    # simple recv frame
    s.settimeout(3.0)
    data = s.recv(65536)
    if not data:
        return None
    # unmask / parse text
    if len(data) < 2:
        return None
    payload_len = data[1] & 0x7F
    offset = 2
    if payload_len == 126:
        payload_len = struct.unpack("!H", data[2:4])[0]
        offset = 4
    elif payload_len == 127:
        payload_len = struct.unpack("!Q", data[2:10])[0]
        offset = 10
    return data[offset:offset+payload_len].decode('utf-8', errors='ignore')

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
    ws_url = tabs[0].get("webSocketDebuggerUrl")
    
    s = ws_connect(ws_url)
    # Enable Console & Runtime
    ws_send(s, json.dumps({"id": 1, "method": "Console.enable"}))
    ws_send(s, json.dumps({"id": 2, "method": "Runtime.enable"}))
    ws_send(s, json.dumps({"id": 3, "method": "Page.enable"}))
    
    # Listen for 3 seconds
    for _ in range(10):
        try:
            msg = ws_recv(s)
            if msg:
                obj = json.loads(msg)
                method = obj.get("method", "")
                if "console" in method.lower() or "exception" in method.lower():
                    print("CDP EVENT:", json.dumps(obj, indent=2))
        except Exception as e:
            break
            
    # Also evaluate an expression in Runtime
    ws_send(s, json.dumps({
        "id": 10,
        "method": "Runtime.evaluate",
        "params": {
            "expression": "(() => { return { typeof_switchMainView: typeof switchMainView, tableStates: typeof tableStates, dayTableRows: document.querySelectorAll('#day-table tbody tr').length, errors: window.__errors || [] }; })()",
            "returnByValue": True
        }
    }))
    time.sleep(1)
    msg = ws_recv(s)
    if msg:
        print("EVAL RESULT:", msg)

finally:
    proc.terminate()
