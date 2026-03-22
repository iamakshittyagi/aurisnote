import os
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.end_headers()

    def do_GET(self):
        try:
            from upstash_redis import Redis
            r = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
            ids = r.zrange("ehr:index", 0, 199, rev=True)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            records = []
            for rid in ids:
                raw = r.get(f"ehr:rec:{rid}")
                if raw:
                    rec = json.loads(raw) if isinstance(raw,str) else raw
                    rec["is_today"] = rec.get("date") == today
                    records.append(rec)
            self._ok(records)
        except Exception as e:
            self._ok({"error":str(e)})

    def _ok(self, obj):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self,*a): pass
