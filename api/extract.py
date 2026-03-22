import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
        self.end_headers()

    def do_POST(self):
        key = os.environ.get("GROQ_API_KEY","")
        n = int(self.headers.get("Content-Length",0))
        body = json.loads(self.rfile.read(n) or b"{}")
        t = (body.get("transcript") or "").strip()
        if not t:
            self._ok({"error":"no transcript"}); return
        p = json.dumps({"model":"llama-3.3-70b-versatile","temperature":0.1,"max_tokens":1024,"messages":[{"role":"system","content":"You are a medical AI. Extract EHR fields from the transcript. Return ONLY valid JSON with these exact keys: patient_name, age, gender, doctor_name, diagnosis, symptoms (array of strings), treatment (array of strings), followup, prakriti, notes. No explanation, no markdown."},{"role":"user","content":t}],"response_format":{"type":"json_object"}}).encode()
        req = urllib.request.Request(GROQ_URL,data=p,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","User-Agent":"groq-python/0.9.0","Accept":"application/json"},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                out = json.loads(r.read())
            data = json.loads(out["choices"][0]["message"]["content"])
            def clean(v): return str(v).strip() if v else ""
            def lst(v):
                if isinstance(v,list): return [str(i).strip() for i in v if i]
                if isinstance(v,str): return [x.strip() for x in v.split(",") if x.strip()]
                return []
            result = {
                "patient_name": clean(data.get("patient_name")),
                "age": clean(data.get("age")),
                "gender": clean(data.get("gender")),
                "doctor_name": clean(data.get("doctor_name")),
                "diagnosis": clean(data.get("diagnosis")),
                "symptoms": lst(data.get("symptoms")),
                "treatment": lst(data.get("treatment")),
                "followup": clean(data.get("followup")),
                "prakriti": clean(data.get("prakriti")),
                "notes": clean(data.get("notes")),
            }
            fields = ["patient_name","age","gender","diagnosis","symptoms","treatment"]
            result["confidence"] = round(sum(1 for f in fields if result.get(f))/len(fields),2)
            self._ok(result)
        except urllib.error.HTTPError as e:
            self._ok({"error":f"Groq {e.code}: {e.read().decode()}"})
        except Exception as e:
            self._ok({"error":str(e)})

    def _ok(self,obj):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self,*a):pass