from __future__ import annotations

import base64
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from requests.auth import HTTPBasicAuth

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "seedrfetch"))

from core.downloader import Downloader


def wait_for_job(downloader: Downloader, job_id: str, *states: str):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = downloader.get(job_id)
        if job and job.state in states:
            return job
        time.sleep(0.01)
    raise AssertionError("job did not reach %s" % (states,))


class Backend:
    def __init__(self, url: str) -> None:
        self.url = url

    def download_file_request(self, _file_id: int):
        return self.url, HTTPBasicAuth("user@example.com", "secret")

    def download_folder_request(self, _folder_id: int):
        return self.url, HTTPBasicAuth("user@example.com", "secret")


def test_basic_auth_is_scoped_to_seedr_api_hop_and_stripped_on_cdn_redirect(tmp_path: Path) -> None:
    seen = {"rest_auth": "", "cdn_auth": ""}
    expected = "Basic " + base64.b64encode(b"user@example.com:secret").decode("ascii")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/rest/file/7":
                seen["rest_auth"] = self.headers.get("Authorization", "")
                self.send_response(302)
                self.send_header("Location", "http://127.0.0.1:%d/cdn/file" % self.server.server_port)
                self.end_headers()
                return
            if self.path == "/cdn/file":
                seen["cdn_auth"] = self.headers.get("Authorization", "")
                self.send_response(200)
                self.send_header("Content-Length", "4")
                self.end_headers()
                self.wfile.write(b"data")
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, _format: str, *_args) -> None:
            return

    server = ThreadingHTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = "http://localhost:%d/rest/file/7" % server.server_port
        downloader = Downloader(Backend(url), max_workers=1)

        job_id = downloader.submit_file(7, "scoped.bin", tmp_path, "scoped.bin")
        job = wait_for_job(downloader, job_id, "completed")

        assert job.state == "completed"
        assert (tmp_path / "scoped.bin").read_bytes() == b"data"
        assert seen["rest_auth"] == expected
        assert seen["cdn_auth"] == ""
    finally:
        server.shutdown()
        server.server_close()
