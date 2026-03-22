import os
import json
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        try:
            from upstash_redis import Redis
            r = Redis(url=os.environ["KV_REST_API_URL"], token=os.environ["KV_REST_API_TOKEN"])
            rid = str(uuid.uuid4())
            now = datetime.utcnow()
            data = {"id":rid,"patient_name":"test","date":now.strftime("%Y-%m-%d")}
            r.set(f"ehr:rec:{rid}", json.dumps(data))
            r.zadd("ehr:index", {rid: now.timestamp()})
            self.wfile.write(json.dumps({"status":"saved","id":rid}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error":str(e),"type":type(e).__name__}).encode())
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self,*a):pass
