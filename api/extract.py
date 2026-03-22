import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = '{"patient_name":"","age":"","gender":"","doctor_name":"","diagnosis":"","symptoms":[],"treatment":[],"followup":"","prakriti":"","notes":""}'

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
        self.end_headers()

    def do_POST(self):
        api_key = os.environ.get("GROQ_API_KEY","")
        length = int(self.headers.get("Content-Length",0))
        body = json.loads(self.rfile.read(length) or b"{}")
        transcript = (body.get("transcript") or "").strip()
        payload = json.dumps({"model":MODEL,"temperature":0.1,"max_tokens":1024,"messages":[{"role":"system","content":"Extract EHR fields from transcript. Return ONLY JSON: "+SYSTEM_PROMPT},{"role":"user","content":transcript}],"response_format":{"type":"json_object"}}).encode()
        req = urllib.request.Request(GROQ_URL,data=payload,headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                result = json.loads(r.read())
            data = json.loads(result["choices"][0]["message"]["content"])
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","*")
            self.end_headers()
            self.wfile.write(json.dumps({"error":str(e)}).encode())

    def log_message(self,*a): pass