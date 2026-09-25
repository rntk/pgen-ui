import http.server
import json
import mimetypes
import os
import socketserver
import urllib.parse
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from .config import AppConfig
from .services import PromptService
from .repository import InvalidFilenameError, ItemNotFoundError


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class PromptRequestHandler(http.server.BaseHTTPRequestHandler):
    config: AppConfig
    service: PromptService

    server_version = "PromptBuilder/1.0"

    def _send_json(self, status: int, data: Any) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, message: str) -> None:
        self._send_json(status, {"error": message, "status": status})

    def _read_json_body(self) -> Dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        except Exception as e:
            raise ValueError(f"Malformed JSON body: {str(e)}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        q = query.get("q", [None])[0]

        # API: Prompts list
        if path == "/api/prompts":
            items = self.service.list_prompts(query=q)
            self._send_json(200, {"items": items, "count": len(items)})
            return

        # API: Single Prompt
        if path.startswith("/api/prompts/"):
            filename = urllib.parse.unquote(path[len("/api/prompts/"):])
            item = self.service.get_prompt(filename)
            if item:
                self._send_json(200, item)
            else:
                self._send_error(404, f"Prompt '{filename}' not found")
            return

        # API: Appendices list
        if path == "/api/appendices":
            items = self.service.list_appendices(query=q)
            self._send_json(200, {"items": items, "count": len(items)})
            return

        # API: Single Appendix
        if path.startswith("/api/appendices/"):
            filename = urllib.parse.unquote(path[len("/api/appendices/"):])
            item = self.service.get_appendix(filename)
            if item:
                self._send_json(200, item)
            else:
                self._send_error(404, f"Appendix '{filename}' not found")
            return

        # API: Health check
        if path == "/api/health":
            self._send_json(200, {"status": "ok", "app": "prompt_builder"})
            return

        # Static files
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            body = self._read_json_body()
        except ValueError as e:
            self._send_error(400, str(e))
            return

        try:
            if path == "/api/prompts":
                filename = body.get("filename")
                content = body.get("content", "")
                if not filename:
                    self._send_error(400, "Field 'filename' is required")
                    return
                saved = self.service.save_prompt(filename, content)
                self._send_json(201, saved)
                return

            if path == "/api/appendices":
                filename = body.get("filename")
                content = body.get("content", "")
                if not filename:
                    self._send_error(400, "Field 'filename' is required")
                    return
                saved = self.service.save_appendix(filename, content)
                self._send_json(201, saved)
                return

            if path == "/api/compose":
                base_content = body.get("base", "")
                appendices = body.get("appendices", [])
                separator = body.get("separator", "\n\n---\n\n")
                result = self.service.compose_prompt(base_content, appendices, separator)
                self._send_json(200, {"composed": result})
                return

            self._send_error(404, "Endpoint not found")

        except InvalidFilenameError as e:
            self._send_error(400, str(e))
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")

    def do_DELETE(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        try:
            if path.startswith("/api/prompts/"):
                filename = urllib.parse.unquote(path[len("/api/prompts/"):])
                deleted = self.service.delete_prompt(filename)
                if deleted:
                    self._send_json(200, {"message": f"Prompt '{filename}' deleted", "success": True})
                else:
                    self._send_error(404, f"Prompt '{filename}' not found")
                return

            if path.startswith("/api/appendices/"):
                filename = urllib.parse.unquote(path[len("/api/appendices/"):])
                deleted = self.service.delete_appendix(filename)
                if deleted:
                    self._send_json(200, {"message": f"Appendix '{filename}' deleted", "success": True})
                else:
                    self._send_error(404, f"Appendix '{filename}' not found")
                return

            self._send_error(404, "Endpoint not found")

        except InvalidFilenameError as e:
            self._send_error(400, str(e))
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")

    def _serve_static(self, path: str) -> None:
        # Default index
        if path in ("", "/"):
            path = "/index.html"

        # Sanitize static path
        clean_rel = path.lstrip("/")
        if clean_rel.startswith("static/"):
            clean_rel = clean_rel[len("static/"):]

        file_path = (self.config.static_dir / clean_rel).resolve()

        # Prevent directory traversal
        if not str(file_path).startswith(str(self.config.static_dir)):
            self._send_error(403, "Forbidden")
            return

        if not file_path.exists() or not file_path.is_file():
            self._send_error(404, f"Static asset '{clean_rel}' not found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8" if "text" in mime_type or "javascript" in mime_type else mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_error(500, f"Error reading file: {str(e)}")

    def log_message(self, format: str, *args: Any) -> None:
        # Custom logging format
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}")


def create_server(config: AppConfig, service: PromptService) -> ThreadedHTTPServer:
    handler = PromptRequestHandler
    handler.config = config
    handler.service = service
    return ThreadedHTTPServer((config.host, config.port), handler)
