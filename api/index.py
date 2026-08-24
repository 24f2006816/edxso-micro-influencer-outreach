import os
import sys

# Make the project root importable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from http.server import BaseHTTPRequestHandler

from app import OutreachAppHandler


class handler(OutreachAppHandler):
    """
    Vercel entrypoint.

    Vercel's Python runtime supports BaseHTTPRequestHandler-style
    serverless functions. The existing application handler is reused
    so the dashboard and API endpoints remain unchanged.
    """

    pass
