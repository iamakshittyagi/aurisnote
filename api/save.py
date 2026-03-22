import os
import json
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler

def get_redis():
    from upstash_redis import Redis
    return Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._ok({"error": "Invalid JSON"}, 400); return

        if not isinstance(data, dict) or not data.get("patient_name", "").strip():
            self._ok({"error": "patient_name required"}, 400); return

        for field in ("symptoms", "treatment"):
            v = data.get(field)
            if isinstance(v, list):
                data[field] = "; ".join(v)

        try:
            r = get_redis()
            rid = str(uuid.uuid4())
            now = datetime.utcnow()
            data["id"] = rid
            data["date"] = now.strftime("%Y-%m-%d")
            data["created_at"] = now.isoformat()
            r.set(f"ehr:rec:{rid}", json.dumps(data))
            r.zadd("ehr:index", {rid: now.timestamp()})
            self._ok({"status": "saved", "id": rid})
        except Exception as e:
            self._ok({"error": str(e)}, 500)

    def _cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Type", "application/json")

    def _ok(self, obj, status=200):
        self._cors()
        self.send_response(status)
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, *a): pass
