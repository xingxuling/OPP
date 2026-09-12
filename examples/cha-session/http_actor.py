"""Loopback REST actor backed by JMESPath, exporting its native OpenAPI document."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys
import jmespath


def schema(field):
    return {"type": "object", "properties": {field: {"type": "array", "items": {"type": "integer"}}},
            "required": [field], "additionalProperties": False}


DOCUMENT = {"openapi": "3.1.0", "info": {"title": "JMESPath sorter", "version": "1"},
    "paths": {"/sort": {"post": {"operationId": "sort_sequence", "requestBody": {
        "required": True, "content": {"application/json": {"schema": schema("values")}}},
        "responses": {"200": {"description": "Sorted numbers", "content": {
            "application/json": {"schema": schema("ordered")}}}}}}}}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def respond(self, code, payload):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.respond(200, DOCUMENT) if self.path == "/openapi.json" else self.respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/sort":
            self.respond(404, {"error": "not found"})
            return
        if self.server.reject_calls:
            self.respond(503, {"error": "operator-injected-unavailable"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if not 0 < length <= 65536:
                raise ValueError("length")
            request = json.loads(self.rfile.read(length))
            self.respond(200, {"ordered": jmespath.search("sort(values)", request)})
        except Exception:
            self.respond(400, {"error": "invalid input"})


if __name__ == "__main__":
    # Each actor is started on an OS-assigned loopback port by the local operator.
    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.reject_calls = "--reject-calls" in sys.argv
    print(json.dumps({"port": server.server_port}), flush=True)
    server.serve_forever()
