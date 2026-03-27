from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import os


def call_claude(issue: str, category: str, priority: str) -> str:
    system_prompt = """You are a senior IT support technician with 10+ years experience in enterprise helpdesk environments. 
You provide structured, professional IT support responses.

Always respond in this exact format with these exact section headers:

DIAGNOSIS:
[2-3 sentences explaining the root cause and what is likely happening technically]

RESOLUTION STEPS:
1. [First step]
2. [Second step]
3. [Third step]
4. [Fourth step if needed]
5. [Fifth step if needed]

PRE-CHECK VERIFICATION:
- [Thing to verify before starting]
- [Another thing to check]
- [Another item]

ESCALATION:
[One paragraph: when to escalate this ticket, who to escalate to, and what information to gather before escalating]

Keep steps clear, concise and actionable. Use real technical commands or settings paths where relevant (e.g. Device Manager, ipconfig /release, etc). Be specific to the category and priority level provided."""

    user_message = f"Category: {category}\nPriority: {priority}\n\nIssue: {issue}"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as res:
        body = json.loads(res.read().decode("utf-8"))
        return body["content"][0]["text"]


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

            result = call_claude(issue, category, priority)

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
