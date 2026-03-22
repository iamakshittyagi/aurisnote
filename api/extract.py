import os
import json
import urllib.request
import urllib.error

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = """You are an expert medical AI assistant. Extract structured EHR data from the transcript.
- Return ONLY valid JSON, no explanation, no markdown, no backticks
- symptoms MUST be an array of strings
- treatment MUST be an array of strings
Return EXACTLY: {"patient_name":"","age":"","gender":"","doctor_name":"","diagnosis":"","symptoms":[],"treatment":[],"followup":"","prakriti":"","notes":""}"""

def handler(request):
    if request.method == "OPTIONS":
        from http.server import BaseHTTPRequestHandler
    api_key = os.environ.get("GROQ_API_KEY","")
    if not api_key:
        return {"statusCode":500,"body":json.dumps({"error":"GROQ_API_KEY not set"}),"headers":{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}}
    try:
        body = json.loads(request.body)
    except:
        return {"statusCode":400,"body":json.dumps({"error":"bad json"}),"headers":{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}}
    transcript = (body.get("transcript") or "").strip()
    payload = json.dumps({"model":MODEL,"temperature":0.1,"max_tokens":1024,"messages":[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":f"Transcript:\n{transcript}"}],"response_format":{"type":"json_object"}}).encode()
    req = urllib.request.Request(GROQ_URL,data=payload,headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as resp:
            result = json.loads(resp.read())
        raw = result["choices"][0]["message"]["content"].strip()
        return {"statusCode":200,"body":raw,"headers":{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}}
    except Exception as e:
        return {"statusCode":500,"body":json.dumps({"error":str(e)}),"headers":{"Access-Control-Allow-Origin":"*","Content-Type":"application/json"}}