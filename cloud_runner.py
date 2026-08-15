"""
Cloud Compatible 24/7 Channel Broadcaster with Healthcheck Endpoint.
Runs continuous Telegram channel broadcaster in background and listens on PORT (default 8080).
"""
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from main import main as run_broadcaster

logger = logging.getLogger("CloudRunner")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - 24/7 FlashJob Channel Broadcaster is Active")

    def log_message(self, format, *args):
        pass  # Quiet health check logs


def run_healthcheck_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Healthcheck server listening on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    # Start healthcheck server in background thread
    health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
    health_thread.start()

    # Start main channel broadcaster daemon
    run_broadcaster()
