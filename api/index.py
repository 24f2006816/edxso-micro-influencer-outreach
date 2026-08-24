"""
Vercel Serverless Function Handler for Micro-Influencer Outreach System.
Integrates with Vercel Python Runtime (@vercel/python) using BaseHTTPRequestHandler.
Uses /tmp for SQLite database storage to support serverless lambda execution.
"""

import os
import sys
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Add root project directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pipeline import OutreachPipeline

# In serverless environments like Vercel, the filesystem is read-only except /tmp
db_path = "/tmp/outreach_system.db" if os.environ.get("VERCEL") else os.path.join(root_dir, "data", "outreach_system.db")
pipeline = OutreachPipeline(db_path=db_path)

# Auto-seed database in serverless if newly created
try:
    if len(pipeline.db.get_all_influencers()) == 0:
        pipeline.run_full_pipeline()
except Exception as e:
    print(f"Init pipeline error: {e}", file=sys.stderr)


class handler(BaseHTTPRequestHandler):
    """
    Vercel Serverless Function Entrypoint.
    """

    def _set_headers(self, status_code=200, content_type="application/json", extra_headers=None):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200, "text/plain")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Serve HTML Web UI
        if path in ["/", "/index.html", "/api", "/api/"]:
            html_file = os.path.join(root_dir, "web", "index.html")
            try:
                with open(html_file, "rb") as f:
                    content = f.read()
                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Error loading UI: {str(e)}".encode("utf-8"))
            return

        # 2. REST API: Influencers List
        if path in ["/api/influencers", "/influencers"]:
            influencers = pipeline.db.get_all_influencers()
            data = [inf.to_dict() for inf in influencers]
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 3. REST API: System Statistics
        if path in ["/api/stats", "/stats"]:
            stats = pipeline.db.get_stats()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        # 4. REST API: Outreach Logs
        if path in ["/api/logs", "/logs"]:
            logs = pipeline.db.get_outreach_logs()
            data = [log.to_dict() for log in logs]
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 5. REST API: Single Message by Influencer ID
        if "/message/" in path:
            inf_id = path.split("/message/")[-1].strip()
            msg = pipeline.db.get_outreach_message(inf_id)
            if msg:
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(msg.to_dict()).encode("utf-8"))
            else:
                self._set_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Message not found"}).encode("utf-8"))
            return

        # 6. REST API: Export Dataset CSV
        if path in ["/api/export/dataset", "/export/dataset"]:
            csv_path = os.path.join(root_dir, "data", "influencer_dataset.csv")
            try:
                pipeline.export_influencer_dataset(csv_path)
                with open(csv_path, "rb") as f:
                    content = f.read()
                self._set_headers(
                    200,
                    "text/csv",
                    {"Content-Disposition": "attachment; filename=influencer_dataset.csv"}
                )
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Export error: {str(e)}".encode("utf-8"))
            return

        # 7. REST API: Export Tracker CSV
        if path in ["/api/export/tracker", "/export/tracker"]:
            csv_path = os.path.join(root_dir, "data", "outreach_tracker.csv")
            try:
                pipeline.export_outreach_tracker(csv_path)
                with open(csv_path, "rb") as f:
                    content = f.read()
                self._set_headers(
                    200,
                    "text/csv",
                    {"Content-Disposition": "attachment; filename=outreach_tracker.csv"}
                )
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Export error: {str(e)}".encode("utf-8"))
            return

        # Fallback to serving index.html or 404
        html_file = os.path.join(root_dir, "web", "index.html")
        if os.path.exists(html_file):
            with open(html_file, "rb") as f:
                content = f.read()
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(content)
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/api/pipeline/run", "/pipeline/run"]:
            try:
                res = pipeline.run_full_pipeline(send_mode="SIMULATED")
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self._set_headers(500, "application/json")
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))
