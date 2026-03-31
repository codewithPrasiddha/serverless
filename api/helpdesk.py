from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os

def call_ollama(issue: str, category: str, priority: str) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", "").rstrip("/")
    model    = os.environ.get("OLLAMA_MODEL", "dolphin3")

    if not base_url:
        raise ValueError("OLLAMA_BASE_URL environment variable is not set.")

    prompt = f"""You are a friendly, helpful IT support assistant speaking directly to an end-user.
Analyze the issue below and respond using EXACTLY these section headers in this order.
Do not skip any section. Do not add extra headers.
DIAGNOSIS:
[Provide a very brief, simple explanation intended for a non-technical end-user. Do NOT use complex IT jargon, system paths, or technical acronyms. Be discreet and polite. Keep it to 1-2 short sentences max.]
RESOLUTION STEPS:
1. [First simple, actionable troubleshooting step for the user to try]
2. [Second simple step]
3. [Third simple step]
4. [Fourth step if needed]
PRE-CHECK VERIFICATION:
- N/A
ESCALATION:
N/A
AGENT REPLY DRAFT:
N/A
INTERNAL NOTE:
N/A
RECOMMENDED ACTION:
N/A
ESTIMATED RESOLUTION:
N/A
---
Priority: {priority}
Issue: {issue}
Auto-detect the category from: Network, Hardware, Software, Account Access, Email & Comms, Other.
Add "CATEGORY: [detected category]" as the very first line of your response."""

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 1500
        }
    }).encode("utf-8")

    url = f"{base_url}/api/generate"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            body = json.loads(res.read().decode("utf-8"))
            return body["response"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Ollama API error {e.code}: {error_body}")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            issue    = body.get("text", "").strip()
            category = body.get("category", "General").strip()
            priority = body.get("priority", "Medium").strip()

            if not issue:
                raise ValueError("No issue description provided.")

            result = call_ollama(issue, category, priority)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"result": result}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        pass
