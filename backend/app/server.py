import argparse
import json
from contextlib import closing
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.app import fake_publisher, store


DEFAULT_DB_PATH = ".localpilot-dev/backend.sqlite"


class JsonHandler(BaseHTTPRequestHandler):
    db_path = DEFAULT_DB_PATH

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        self.route_request("GET")

    def do_POST(self):
        self.route_request("POST")

    def do_PATCH(self):
        self.route_request("PATCH")

    def route_request(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if method == "GET" and path == "/api/v1/health":
                self.send_json({"status": "ok", "service": "localpilot-backend"})
                return
            if method == "GET" and path == "/api/v1/workflow":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.get_workflow(conn))
                return
            if method == "GET" and path == "/api/v1/debug/publish-jobs":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"status": "ok", "publishJobs": store.list_debug_publish_jobs(conn)})
                return
            if method == "POST" and path == "/api/v1/campaigns":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"campaign": store.create_campaign(conn, self.read_json())}, status=201)
                return
            approval_action = self.match_approval_action(path)
            if approval_action and method == "POST" and approval_action["action"] == "publish":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(fake_publisher.queue_fake_publish(conn, approval_action["approval_id"]), status=201)
                return
            publish_job = self.match_publish_job(path)
            if publish_job and method == "GET" and publish_job["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json({"job": store.get_serialized_publish_job(conn, publish_job["job_id"])})
                return
            if publish_job and method == "POST" and publish_job["action"] == "retry":
                body = self.read_json()
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(
                        fake_publisher.retry_fake_publish(
                            conn,
                            publish_job["job_id"],
                            diagnostics_fixture=body.get("diagnosticsFixture"),
                        ),
                        status=201,
                    )
                return
            draft_action = self.match_draft_action(path)
            if draft_action and method == "PATCH" and draft_action["action"] is None:
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.update_draft(conn, draft_action["draft_id"], self.read_json()))
                return
            if draft_action and method == "POST" and draft_action["action"] == "approve":
                with closing(store.connect(self.db_path)) as conn:
                    self.send_json(store.approve_draft(conn, draft_action["draft_id"], self.read_json()), status=201)
                return

            self.send_error_json(404, "Route not found.")
        except store.StoreError as exc:
            self.send_error_json(exc.status, exc.message)
        except json.JSONDecodeError:
            self.send_error_json(400, "Request body must be valid JSON.")
        except Exception:
            self.send_error_json(500, "Unexpected backend error.")

    def match_draft_action(self, path):
        parts = path.split("/")
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "drafts"]:
            return {"draft_id": parts[4], "action": None}
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "drafts"]:
            return {"draft_id": parts[4], "action": parts[5]}
        return None

    def match_approval_action(self, path):
        parts = path.split("/")
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "approvals"]:
            return {"approval_id": parts[4], "action": parts[5]}
        return None

    def match_publish_job(self, path):
        parts = path.split("/")
        if len(parts) == 5 and parts[:4] == ["", "api", "v1", "publish-jobs"]:
            return {"job_id": parts[4], "action": None}
        if len(parts) == 6 and parts[:4] == ["", "api", "v1", "publish-jobs"]:
            return {"job_id": parts[4], "action": parts[5]}
        return None

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_json(self, payload, status=200):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, message):
        phrase = HTTPStatus(status).phrase if status in HTTPStatus._value2member_map_ else "Error"
        self.send_json({"error": {"status": status, "message": message, "code": phrase}}, status=status)


def create_app(host="127.0.0.1", port=8787, db_path=DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    store.ensure_database(db_path)

    class BoundHandler(JsonHandler):
        pass

    BoundHandler.db_path = db_path
    return ThreadingHTTPServer((host, port), BoundHandler)


def run(host="127.0.0.1", port=8787, db_path=DEFAULT_DB_PATH):
    server = create_app(host=host, port=port, db_path=db_path)
    print(f"LocalPilot backend listening at http://{host}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run LocalPilot backend API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    run(host=args.host, port=args.port, db_path=args.db)


if __name__ == "__main__":
    main()
