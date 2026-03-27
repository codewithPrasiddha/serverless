from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
import os


def call_gemini(issue: str, category: str, priority: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    prompt = f"""You are a senior IT support technician with 10+ years of enterprise helpdesk experience.
Analyze the issue below and respond using EXACTLY these section headers in this order.
Do not skip any section. Do not add extra headers.

DIAGNOSIS:
[2-3 sentences explaining the root cause and what is technically happening. Be specific.]

RESOLUTION STEPS:
1. [First actionable step with specific commands, paths, or settings where relevant]
2. [Second step]
3. [Third step]
4. [Fourth step if needed]
5. [Fifth step if needed]

PRE-CHECK VERIFICATION:
- [Item to verify before starting]
- [Another item to check]
- [Another item]

ESCALATION:
[One paragraph: when this should be escalated, who to escalate to (L2/L3/vendor/manager), and what information to collect before escalating.]

AGENT REPLY DRAFT:
[Write a professional, empathetic 3-5 sentence message to send directly to the ticket reporter. Do not include a subject line or greeting placeholder. Acknowledge their issue, briefly explain what the team is doing, give one tip they can try right now, and state what happens next. Tone: helpful, clear, not robotic.]

INTERNAL NOTE:
[1-2 sentences for internal documentation only. Technical and factual. Include suspected root cause and first action taken.]

RECOMMENDED ACTION:
[Output exactly one option only: Remote Session / Phone Call / Email Response / Field Visit / Escalate to L2 / Escalate to L3 / Knowledge Base]

ESTIMATED RESOLUTION:
[Output a time range only, e.g.: 15-30 minutes / 1-2 hours / 4-8 hours / Next business day / Under 15 minutes]

---

Priority: {priority}
Issue: {issue}

Auto-detect the category from: Network, Hardware, Software, Account Access, Email & Comms, Other.
Add "CATEGORY: [detected category]" as the very first line of your response."""

    payload = json.dumps({
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "maxOutputTokens": 1500,
            "temperature": 0.3
        }
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read().decode("utf-8"))
            return body["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Gemini API error {e.code}: {error_body}")


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

            result = call_gemini(issue, category, priority)

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
