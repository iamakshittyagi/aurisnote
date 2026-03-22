import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

def get_redis():
    from upstash_redis import Redis
    return Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])

def parse_id(path, query):
    qs = urllib.parse.parse_qs(query)
    if "id" in qs: return qs["id"][0]
    parts = [p for p in path.split("/") if p]
    return parts[-1] if len(parts) >= 2 else None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(); self.end_headers()

    def do_GET(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._ok({"error": "id required"}, 400); return
        try:
            raw = get_redis().get(f"ehr:rec:{rid}")
            if not raw: self._ok({"error": "Not found"}, 404); return
            self._ok(json.loads(raw) if isinstance(raw, str) else raw)
        except Exception as e:
            self._ok({"error": str(e)}, 500)

    def do_DELETE(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._ok({"error": "id required"}, 400); return
        try:
            r = get_redis()
            r.delete(f"ehr:rec:{rid}")
            r.zrem("ehr:index", rid)
            self._ok({"status": "deleted"})
        except Exception as e:
            self._ok({"error": str(e)}, 500)

    def _query(self):
        return self.path.split("?", 1)[1] if "?" in self.path else ""

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