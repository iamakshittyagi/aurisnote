import os
import json
import cgi
import io
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

DEEPGRAM_URL = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&detect_language=true&punctuate=true"

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def do_POST(self):
        api_key = os.environ.get("DEEPGRAM_API_KEY","")
        if not api_key:
            self._ok({"error":"DEEPGRAM_API_KEY not set"}); return
        content_type = self.headers.get("Content-Type","")
        length = int(self.headers.get("Content-Length",0))
        raw_body = self.rfile.read(length)
        try:
            form = cgi.FieldStorage(
                fp=io.BytesIO(raw_body),
                environ={"REQUEST_METHOD":"POST","CONTENT_TYPE":content_type,"CONTENT_LENGTH":str(length)},
                keep_blank_values=True,
            )
            audio_field = form["audio"]
            audio_bytes = audio_field.file.read()
            audio_ctype = audio_field.type or "audio/webm"
        except Exception as e:
            self._ok({"error":"No audio: "+str(e)}); return
        try:
            req = urllib.request.Request(
                DEEPGRAM_URL, data=audio_bytes,
                headers={"Authorization":"Token "+api_key,"Content-Type":audio_ctype},
                method="POST"
            )
            with urllib.request.urlopen(req,timeout=60) as resp:
                dg = json.loads(resp.read())
            transcript = dg.get("results",{}).get("channels",[{}])[0].get("alternatives",[{}])[0].get("transcript","")
            detected = dg.get("results",{}).get("channels",[{}])[0].get("detected_language","unknown")
            self._ok({"text":transcript,"language":detected})
        except urllib.error.HTTPError as e:
            self._ok({"error":"Deepgram "+str(e.code)+": "+e.read().decode()})
        except Exception as e:
            self._ok({"error":str(e)})

    def _ok(self, obj):
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self,*a): pass
