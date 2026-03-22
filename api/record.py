import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

def parse_id(path, query):
    qs = urllib.parse.parse_qs(query)
    if "id" in qs: return qs["id"][0]
    parts = [p for p in path.split("/") if p]
    return parts[-1] if len(parts) >= 2 else None

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.end_headers()

    def do_GET(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._ok({"error":"id required"}); return
        try:
            from upstash_redis import Redis
            r = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
            raw = r.get(f"ehr:rec:{rid}")
            if not raw: self._ok({"error":"Not found"}); return
            self._ok(json.loads(raw) if isinstance(raw,str) else raw)
        except Exception as e:
            self._ok({"error":str(e)})

    def do_DELETE(self):
        rid = parse_id(self.path, self._query())
        if not rid: self._ok({"error":"id required"}); return
        try:
            from upstash_redis import Redis
            r = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
            r.delete(f"ehr:rec:{rid}")
            r.zrem("ehr:index", rid)
            self._ok({"status":"deleted"})
        except Exception as e:
            self._ok({"error":str(e)})

    def _query(self):
        return self.path.split("?",1)[1] if "?" in self.path else ""

    def _ok(self, obj):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self,*a): pass
