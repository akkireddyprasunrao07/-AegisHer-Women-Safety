import datetime
import json
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HELPLINES = [
    {"code": "112", "name": "National Emergency Response (ERSS)", "category": "Emergency", "verified": True},
    {"code": "100", "name": "Police Control Room", "category": "Police", "verified": True},
    {"code": "108", "name": "Ambulance & Medical Emergency", "category": "Medical", "verified": True},
    {"code": "181", "name": "Women Helpline (24x7)", "category": "Women Safety", "verified": True},
    {"code": "1091", "name": "Women Police Helpline", "category": "Police", "verified": True},
    {"code": "NIST-SEC", "name": "Campus Security & Safe Escort", "category": "Campus / Local", "verified": True},
]


class SafetyEngine:
    def __init__(self):
        self.lock = threading.Lock()
        self.online = True
        self.active_sos = None
        self.breadcrumbs = []
        self.offline_queue = []
        self.audit_log = []
        self.checkin = {"active": False, "remaining": 0, "stop_flag": False}
        self._seed_initial_state()

    def _now(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _log(self, step: str, detail: str, channel: str = "SYSTEM"):
        self.audit_log.insert(
            0,
            {
                "id": str(uuid.uuid4())[:8],
                "time": self._now(),
                "step": step,
                "detail": detail,
                "channel": channel,
            },
        )

    def _seed_initial_state(self):
        base_lat, base_lng = 19.1972, 84.8891  # Berhampur / Ganjam area
        self.breadcrumbs = [
            {"lat": base_lat, "lng": base_lng, "time": self._now(), "battery": 84, "synced": True},
            {"lat": base_lat + 0.0012, "lng": base_lng + 0.0009, "time": self._now(), "battery": 83, "synced": True},
        ]
        self._log("READY", "Platform initialized with AES-256 session & trusted contacts.", "PRIVACY")

    def trigger_sos(self, mode: str = "STANDARD", lat: float | None = None, lng: float | None = None, battery: int = 78):
        with self.lock:
            last = self.breadcrumbs[-1] if self.breadcrumbs else {"lat": 19.1972, "lng": 84.8891}
            cur_lat = lat if lat is not None else round(last["lat"] + 0.0007, 6)
            cur_lng = lng if lng is not None else round(last["lng"] + 0.0006, 6)

            sos_id = f"SOS-{str(uuid.uuid4())[:6].upper()}"
            self.active_sos = {
                "id": sos_id,
                "mode": mode,  # "STANDARD" or "SILENT"
                "status": "ACTIVE",
                "started_at": self._now(),
                "lat": cur_lat,
                "lng": cur_lng,
                "battery": battery,
                "audio_clip_sec": 12,
                "escalated_112": True,
            }

            point = {
                "lat": cur_lat,
                "lng": cur_lng,
                "time": self._now(),
                "battery": battery,
                "synced": self.online,
            }
            self.breadcrumbs.append(point)

            trigger_label = "Silent Auto-Escalate SOS" if mode == "SILENT" else "One-Tap SOS"
            self._log("01 TRIGGER", f"{trigger_label} ({sos_id}) activated.", "APP")
            self._log(
                "02 CONTEXT",
                f"Captured GPS ({cur_lat}, {cur_lng}), battery {battery}%, 12s ambient audio note.",
                "SENSOR",
            )

            if self.online:
                self._log("03 BROADCAST", "Dispatched FCM push, SMS fallback & expiring live link to contacts.", "ALERT")
                self._log("04 ESCALATE", "Structured payload logged for ERSS 112 / Police 100 dispatch handoff.", "112/100")
            else:
                self.offline_queue.append(point)
                self._log("OFFLINE QUEUE", "Network dead zone detected; GPS & SOS payload cached locally.", "OFFLINE")

            return dict(self.active_sos)

    def resolve_sos(self, action: str = "RESOLVED"):
        with self.lock:
            if not self.active_sos:
                return None
            sos_id = self.active_sos["id"]
            self.active_sos["status"] = action
            self._log("CLOSED", f"{sos_id} marked as {action} with biometric/PIN confirmation.", "UX")
            resolved = dict(self.active_sos)
            self.active_sos = None
            return resolved

    def add_ping(self, lat: float, lng: float, battery: int):
        with self.lock:
            point = {
                "lat": round(lat, 6),
                "lng": round(lng, 6),
                "time": self._now(),
                "battery": battery,
                "synced": self.online,
            }
            self.breadcrumbs.append(point)
            if self.active_sos:
                self.active_sos["lat"] = point["lat"]
                self.active_sos["lng"] = point["lng"]
                self.active_sos["battery"] = battery

            if self.online:
                self._log("LIVE PING", f"Synced location ({point['lat']}, {point['lng']}) | Bat {battery}%.", "REALTIME")
            else:
                self.offline_queue.append(point)
                self._log("CACHED PING", f"Queued offline point ({point['lat']}, {point['lng']}).", "OFFLINE")
            return point

    def set_connectivity(self, online: bool):
        with self.lock:
            self.online = online
            if online:
                flushed = len(self.offline_queue)
                for p in self.offline_queue:
                    p["synced"] = True
                self.offline_queue.clear()
                if flushed > 0:
                    self._log("OFFLINE SYNC", f"Connectivity restored: flushed {flushed} queued location ping(s).", "SYNC")
                else:
                    self._log("ONLINE", "Network connection active.", "REALTIME")
            else:
                self._log("DEAD ZONE", "Simulated network drop; local caching enabled.", "OFFLINE")

    def start_checkin(self, seconds: int = 8):
        with self.lock:
            self.checkin["stop_flag"] = True
        time.sleep(0.05)

        def _worker():
            with self.lock:
                self.checkin = {"active": True, "remaining": seconds, "stop_flag": False}
                self._log("CHECK-IN", f"Started {seconds}s timed commute check-in.", "PROACTIVE")

            while True:
                with self.lock:
                    if self.checkin["stop_flag"] or not self.checkin["active"]:
                        return
                    rem = self.checkin["remaining"]
                    if rem <= 0:
                        self.checkin["active"] = False
                        break
                    self.checkin["remaining"] = rem - 1
                time.sleep(1)

            self._log("CHECK-IN EXPIRED", "No safe confirmation received; auto-escalating SOS.", "PROACTIVE")
            self.trigger_sos(mode="SILENT")

        threading.Thread(target=_worker, daemon=True).start()

    def confirm_checkin_safe(self):
        with self.lock:
            if self.checkin["active"]:
                self.checkin["active"] = False
                self.checkin["stop_flag"] = True
                self._log("CHECK-IN SAFE", "User confirmed safe arrival; timer cancelled.", "PROACTIVE")

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "online": self.online,
                "active_sos": self.active_sos,
                "breadcrumbs": self.breadcrumbs[-25:],
                "offline_queued_count": len(self.offline_queue),
                "audit_log": self.audit_log[:30],
                "checkin": dict(self.checkin),
                "helplines": HELPLINES,
            }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Women Safety Assistance Platform — Responder & Audit View</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }
    .grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; max-width: 1200px; margin: 0 auto; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; }
    h1, h2 { margin-top: 0; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .on { background: #14532d; color: #86efac; }
    .off { background: #7f1d1d; color: #fca5a5; }
    .sos-box { background: #450a0a; border: 1px solid #ef4444; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
    .safe-box { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 14px; margin-bottom: 14px; }
    button { background: #2563eb; color: white; border: none; padding: 8px 14px; border-radius: 8px; cursor: pointer; font-weight: 600; margin-right: 8px; margin-bottom: 8px; }
    button.danger { background: #dc2626; }
    button.warn { background: #d97706; }
    button.ok { background: #16a34a; }
    .log-item { border-bottom: 1px solid #334155; padding: 8px 0; font-size: 13px; }
    .step { color: #38bdf8; font-weight: 700; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 6px; border-bottom: 1px solid #334155; }
  </style>
</head>
<body>
  <div class="grid">
    <div>
      <div class="card">
        <h1>Women Safety Assistance — Live Responder View</h1>
        <p>
          Connectivity: <span id="netBadge" class="badge on">ONLINE</span>
          &nbsp;|&nbsp; Offline Queued Pings: <strong id="qCount">0</strong>
        </p>
        <div>
          <button class="danger" onclick="api('/api/sos', {mode:'STANDARD'})">Trigger One-Tap SOS</button>
          <button class="warn" onclick="api('/api/sos', {mode:'SILENT'})">Trigger Silent Escalation</button>
          <button class="ok" onclick="api('/api/resolve', {action:'RESOLVED'})">Mark Resolved</button>
          <button onclick="toggleNet()">Toggle Dead Zone</button>
          <button onclick="api('/api/checkin/start', {seconds:8})">Start 8s Check-In</button>
          <button class="ok" onclick="api('/api/checkin/safe', {})">Confirm Safe</button>
        </div>
        <div id="sosPanel" class="safe-box">No active SOS alert.</div>
        <h2>Recent GPS Breadcrumbs</h2>
        <table>
          <thead><tr><th>Time</th><th>Latitude</th><th>Longitude</th><th>Bat</th><th>Synced</th></tr></thead>
          <tbody id="crumbs"></tbody>
        </table>
      </div>
    </div>
    <div>
      <div class="card">
        <h2>Escalation & Audit Trail</h2>
        <div id="logs"></div>
      </div>
    </div>
  </div>
  <script>
    let isOnline = true;
    async function api(path, body) {
      await fetch(path, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) });
      refresh();
    }
    function toggleNet() {
      api('/api/connectivity', { online: !isOnline });
    }
    async function refresh() {
      const res = await fetch('/api/state');
      const d = await res.json();
      isOnline = d.online;
      const badge = document.getElementById('netBadge');
      badge.textContent = d.online ? 'ONLINE' : 'DEAD ZONE (OFFLINE)';
      badge.className = 'badge ' + (d.online ? 'on' : 'off');
      document.getElementById('qCount').textContent = d.offline_queued_count;

      const sosPanel = document.getElementById('sosPanel');
      if (d.active_sos) {
        sosPanel.className = 'sos-box';
        sosPanel.innerHTML = `<strong>ACTIVE ${d.active_sos.mode} SOS (${d.active_sos.id})</strong><br/>
          Started: ${d.active_sos.started_at} | GPS: ${d.active_sos.lat}, ${d.active_sos.lng} | Battery: ${d.active_sos.battery}%<br/>
          112/100 Escalation Payload: Logged | Audio Note: ${d.active_sos.audio_clip_sec}s captured`;
      } else {
        sosPanel.className = 'safe-box';
        sosPanel.textContent = d.checkin.active
          ? `Timed Check-In Active: ${d.checkin.remaining}s remaining before auto-escalation.`
          : 'No active SOS alert. Ready for instant or silent trigger.';
      }

      document.getElementById('crumbs').innerHTML = [...d.breadcrumbs].reverse().slice(0, 8).map(p =>
        `<tr><td>${p.time}</td><td>${p.lat}</td><td>${p.lng}</td><td>${p.battery}%</td><td>${p.synced ? 'Yes' : 'Queued'}</td></tr>`
      ).join('');

      document.getElementById('logs').innerHTML = d.audit_log.map(l =>
        `<div class="log-item"><span class="step">[${l.time}] ${l.step}</span> (${l.channel}) — ${l.detail}</div>`
      ).join('');
    }
    refresh();
    setInterval(refresh, 1500);
  </script>
</body>
</html>
"""


def make_handler(engine: SafetyEngine):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: int = 200):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/state":
                self._send_json(engine.snapshot())
                return
            html = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            data = self._read_json()
            if parsed.path == "/api/sos":
                self._send_json(engine.trigger_sos(mode=data.get("mode", "STANDARD")))
            elif parsed.path == "/api/resolve":
                self._send_json({"resolved": engine.resolve_sos(data.get("action", "RESOLVED"))})
            elif parsed.path == "/api/ping":
                self._send_json(
                    engine.add_ping(
                        float(data.get("lat", 19.198)),
                        float(data.get("lng", 84.890)),
                        int(data.get("battery", 75)),
                    )
                )
            elif parsed.path == "/api/connectivity":
                engine.set_connectivity(bool(data.get("online", True)))
                self._send_json({"online": engine.online})
            elif parsed.path == "/api/checkin/start":
                engine.start_checkin(int(data.get("seconds", 8)))
                self._send_json({"status": "started"})
            elif parsed.path == "/api/checkin/safe":
                engine.confirm_checkin_safe()
                self._send_json({"status": "safe"})
            else:
                self._send_json({"error": "Not found"}, 404)

        def log_message(self, format, *args):
            return  # Keep terminal clean for interactive CLI

    return Handler


def cli_loop(engine: SafetyEngine):
    print("\n--- Women Safety Assistance Prototype (CLI + Live Dashboard) ---")
    print("Dashboard URL: http://127.0.0.1:8080")
    print("Commands: sos | silent | ping | offline | online | checkin | safe | helplines | resolve | quit\n")
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            cmd = "quit"

        if cmd == "sos":
            res = engine.trigger_sos("STANDARD")
            print(f"Triggered {res['id']} at ({res['lat']}, {res['lng']})")
        elif cmd == "silent":
            res = engine.trigger_sos("SILENT")
            print(f"Silent escalation {res['id']} sent to trusted circle & 112 audit log.")
        elif cmd == "ping":
            last = engine.breadcrumbs[-1]
            p = engine.add_ping(last["lat"] + 0.0005, last["lng"] + 0.0004, max(10, last["battery"] - 1))
            print(f"Location update: ({p['lat']}, {p['lng']}) | synced={p['synced']}")
        elif cmd == "offline":
            engine.set_connectivity(False)
            print("Network set to DEAD ZONE (offline queueing enabled).")
        elif cmd == "online":
            engine.set_connectivity(True)
            print("Network set to ONLINE (queued points flushed).")
        elif cmd == "checkin":
            engine.start_checkin(8)
            print("Started 8s timed check-in (type 'safe' before 8s to cancel).")
        elif cmd == "safe":
            engine.confirm_checkin_safe()
            print("Check-in confirmed safe.")
        elif cmd == "helplines":
            for h in HELPLINES:
                print(f"  [{h['code']}] {h['name']} ({h['category']})")
        elif cmd == "resolve":
            res = engine.resolve_sos("RESOLVED")
            print("Resolved:", res["id"] if res else "No active SOS")
        elif cmd == "quit":
            print("Shutting down prototype.")
            break
        elif cmd:
            print("Unknown command. Try: sos, silent, ping, offline, online, checkin, safe, helplines, resolve, quit")


if __name__ == "__main__":
    safety_engine = SafetyEngine()
    server = ThreadingHTTPServer(("127.0.0.1", 8080), make_handler(safety_engine))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    cli_loop(safety_engine)
    server.shutdown()
