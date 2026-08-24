"""
Interactive Web Application and REST API Server.
Built with zero external dependencies using Python's native http.server.
Provides live visualization, interactive filtering, AI message inspection, and pipeline controls.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pipeline import OutreachPipeline


pipeline = OutreachPipeline()


class OutreachAppHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler serving static web UI and REST API endpoints.
    """

    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200, "text/plain")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Static UI Route
        if path in ["/", "/index.html"]:
            html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "index.html")
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
        if path == "/api/influencers":
            influencers = pipeline.db.get_all_influencers()
            data = [inf.to_dict() for inf in influencers]
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 3. REST API: System Statistics
        if path == "/api/stats":
            stats = pipeline.db.get_stats()
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        # 4. REST API: Outreach Logs
        if path == "/api/logs":
            logs = pipeline.db.get_outreach_logs()
            data = [log.to_dict() for log in logs]
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 5. REST API: Get Single Message by Influencer ID (/api/message/<id>)
        if path.startswith("/api/message/"):
            inf_id = path.replace("/api/message/", "").strip()
            msg = pipeline.db.get_outreach_message(inf_id)
            if msg:
                self._set_headers(200, "application/json")
                self.wfile.write(json.dumps(msg.to_dict()).encode("utf-8"))
            else:
                self._set_headers(404, "application/json")
                self.wfile.write(json.dumps({"error": "Message not found"}).encode("utf-8"))
            return

        # 6. REST API: Export Dataset CSV
        if path == "/api/export/dataset":
            csv_path = os.path.join(os.path.dirname(__file__), "data", "influencer_dataset.csv")
            pipeline.export_influencer_dataset(csv_path)
            try:
                with open(csv_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", "attachment; filename=influencer_dataset.csv")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Export error: {str(e)}".encode("utf-8"))
            return

        # 7. REST API: Export Tracker CSV
        if path == "/api/export/tracker":
            csv_path = os.path.join(os.path.dirname(__file__), "data", "outreach_tracker.csv")
            pipeline.export_outreach_tracker(csv_path)
            try:
                with open(csv_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", "attachment; filename=outreach_tracker.csv")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(f"Export error: {str(e)}".encode("utf-8"))
            return

        # 404 Fallback
        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/pipeline/run":
            res = pipeline.run_full_pipeline(send_mode="SIMULATED")
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        self._set_headers(404, "application/json")
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run_server(port: int = 8080):
    # Ensure pipeline is initialized with data
    if len(pipeline.db.get_all_influencers()) == 0:
        print("[*] Initializing system data on startup...")
        pipeline.run_full_pipeline()

    server_address = ("", port)
    httpd = HTTPServer(server_address, OutreachAppHandler)
    print("=" * 80)
    print(f"  ⚡ EDXSO AI Micro-Influencer Outreach Dashboard Running at http://localhost:{port}")
    print("=" * 80)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
