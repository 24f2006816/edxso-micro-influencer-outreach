import os
import sys
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Vercel's filesystem is read-only except for /tmp.
# Copy the bundled database to /tmp on cold start.
source_db = os.path.join(ROOT, "data", "outreach_system.db")
tmp_db = os.path.join(tempfile.gettempdir(), "outreach_system.db")

if os.path.exists(source_db) and not os.path.exists(tmp_db):
    shutil.copy2(source_db, tmp_db)

# Override the database location before importing the application.
os.environ["EDXSO_DB_PATH"] = tmp_db

from pipeline import OutreachPipeline
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

pipeline = OutreachPipeline(db_path=tmp_db)


class handler(BaseHTTPRequestHandler):

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

        if path in ["/", "/index.html"]:
            html_file = os.path.join(ROOT, "web", "index.html")

            try:
                with open(html_file, "rb") as f:
                    content = f.read()

                self._set_headers(200, "text/html; charset=utf-8")
                self.wfile.write(content)

            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(
                    f"Error loading UI: {str(e)}".encode("utf-8")
                )

            return

        if path == "/api/influencers":
            data = [
                inf.to_dict()
                for inf in pipeline.db.get_all_influencers()
            ]

            self._set_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path == "/api/stats":
            stats = pipeline.db.get_stats()

            self._set_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8"))
            return

        if path == "/api/logs":
            data = [
                log.to_dict()
                for log in pipeline.db.get_outreach_logs()
            ]

            self._set_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path.startswith("/api/message/"):
            inf_id = path.replace("/api/message/", "").strip()

            msg = pipeline.db.get_outreach_message(inf_id)

            if msg:
                self._set_headers()
                self.wfile.write(
                    json.dumps(msg.to_dict()).encode("utf-8")
                )
            else:
                self._set_headers(404)
                self.wfile.write(
                    json.dumps({"error": "Message not found"}).encode("utf-8")
                )

            return

        if path == "/api/export/dataset":
            csv_path = os.path.join(
                tempfile.gettempdir(),
                "influencer_dataset.csv"
            )

            pipeline.export_influencer_dataset(csv_path)

            try:
                with open(csv_path, "rb") as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header(
                    "Content-Disposition",
                    "attachment; filename=influencer_dataset.csv"
                )
                self.end_headers()
                self.wfile.write(content)

            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(
                    f"Export error: {str(e)}".encode("utf-8")
                )

            return

        if path == "/api/export/tracker":
            csv_path = os.path.join(
                tempfile.gettempdir(),
                "outreach_tracker.csv"
            )

            pipeline.export_outreach_tracker(csv_path)

            try:
                with open(csv_path, "rb") as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header(
                    "Content-Disposition",
                    "attachment; filename=outreach_tracker.csv"
                )
                self.end_headers()
                self.wfile.write(content)

            except Exception as e:
                self._set_headers(500, "text/plain")
                self.wfile.write(
                    f"Export error: {str(e)}".encode("utf-8")
                )

            return

        self._set_headers(404)
        self.wfile.write(
            json.dumps({"error": "Endpoint not found"}).encode("utf-8")
        )

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/pipeline/run":
            try:
                result = pipeline.run_full_pipeline(
                    send_mode="SIMULATED"
                )

                self._set_headers()
                self.wfile.write(
                    json.dumps(result).encode("utf-8")
                )

            except Exception as e:
                self._set_headers(500)
                self.wfile.write(
                    json.dumps({
                        "status": "error",
                        "error": str(e)
                    }).encode("utf-8")
                )

            return

        self._set_headers(404)
        self.wfile.write(
            json.dumps({"error": "Endpoint not found"}).encode("utf-8")
        )

    def log_message(self, format, *args):
        sys.stderr.write(
            f"[{self.log_date_time_string()}] "
            f"{format % args}\n"
        )
