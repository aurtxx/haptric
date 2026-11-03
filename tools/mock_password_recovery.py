"""Loopback-only password-recovery mock for safe workflow validation.

This service is synthetic and must never be pointed at a real account or exposed
outside 127.0.0.1. It models generic recovery responses, OTP expiry, one-time
use, request throttling, and verification lockout without contacting the network.
"""

from __future__ import annotations

import argparse
import json
import secrets
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
TEST_ACCOUNT = "tester@example.test"
OTP_TTL_SECONDS = 120
REQUEST_WINDOW_SECONDS = 60
REQUEST_LIMIT = 3
VERIFY_LIMIT = 5
LOCKOUT_SECONDS = 60


class MockState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.issued_at: dict[str, float] = {}
        self.issued_otp: dict[str, str] = {}
        self.issued_session: dict[str, str] = {}
        self.used: set[str] = set()
        self.request_times: dict[tuple[str, str], list[float]] = {}
        self.failed_attempts: dict[str, int] = {}
        self.locked_until: dict[str, float] = {}

    def reset(self) -> None:
        with self.lock:
            self.issued_at.clear()
            self.issued_otp.clear()
            self.issued_session.clear()
            self.used.clear()
            self.request_times.clear()
            self.failed_attempts.clear()
            self.locked_until.clear()


STATE = MockState()


def json_bytes(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "MockRecovery/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep test logs free of request bodies and potential identifiers.
        print("mock", self.command, self.path.split("?", 1)[0], self.address_string())

    def send_json(self, status: int, value: dict) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 4096:
            raise ValueError("body too large")
        raw = self.rfile.read(length)
        value = json.loads(raw or b"{}")
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "service": "loopback-mock"})
            return
        if self.path == "/":
            self.send_json(200, {"service": "mock-password-recovery", "loopback_only": True})
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self.read_json()
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid_json"})
            return

        if self.path == "/__test/reset":
            STATE.reset()
            self.send_json(200, {"status": "reset"})
            return

        if self.path == "/__test/expire":
            email = str(payload.get("email", TEST_ACCOUNT)).lower()
            with STATE.lock:
                STATE.issued_at[email] = time.time() - OTP_TTL_SECONDS - 1
            self.send_json(200, {"status": "expired_fixture"})
            return

        if self.path == "/password-recovery/request":
            self.request_recovery(payload)
            return
        if self.path == "/password-recovery/verify":
            self.verify_otp(payload)
            return
        self.send_json(404, {"error": "not_found"})

    def request_recovery(self, payload: dict) -> None:
        email = str(payload.get("email", "")).strip().lower()
        session_id = self.headers.get("X-Test-Session", "")
        now = time.time()
        key = (self.client_address[0], email)
        challenge_otp = f"{secrets.randbelow(10_000):04d}"
        with STATE.lock:
            recent = [t for t in STATE.request_times.get(key, []) if now - t < REQUEST_WINDOW_SECONDS]
            recent.append(now)
            STATE.request_times[key] = recent
            limited = len(recent) > REQUEST_LIMIT
            if not limited and email == TEST_ACCOUNT:
                STATE.issued_at[email] = now
                STATE.issued_otp[email] = challenge_otp
                STATE.issued_session[email] = session_id
                STATE.used.discard(email)
                # Attempt counters and active lockouts are account-scoped, so
                # requesting another challenge cannot reset the guess budget.
        if limited:
            self.send_json(429, {"status": "rate_limited", "retry_after_seconds": REQUEST_WINDOW_SECONDS})
            return
        # Known and unknown accounts intentionally share the same public response.
        self.send_json(202, {"status": "accepted", "message": "If the account exists, instructions are sent."})

    def verify_otp(self, payload: dict) -> None:
        email = str(payload.get("email", "")).strip().lower()
        otp = str(payload.get("otp", ""))
        session_id = self.headers.get("X-Test-Session", "")
        now = time.time()
        with STATE.lock:
            if STATE.locked_until.get(email, 0) > now:
                self.send_json(423, {"error": "Unable to verify request."})
                return
            issued = STATE.issued_at.get(email)
            if (
                email != TEST_ACCOUNT
                or issued is None
                or session_id != STATE.issued_session.get(email)
            ):
                self.send_json(400, {"error": "Unable to verify request."})
                return
            if email in STATE.used:
                self.send_json(400, {"error": "Unable to verify request."})
                return
            if now - issued > OTP_TTL_SECONDS:
                self.send_json(400, {"error": "Unable to verify request."})
                return
            if otp != STATE.issued_otp.get(email):
                attempts = STATE.failed_attempts.get(email, 0) + 1
                STATE.failed_attempts[email] = attempts
                if attempts >= VERIFY_LIMIT:
                    STATE.locked_until[email] = now + LOCKOUT_SECONDS
                    self.send_json(423, {"error": "Unable to verify request."})
                    return
                self.send_json(401, {"error": "Unable to verify request."})
                return
            STATE.used.add(email)
            self.send_json(200, {"status": "verified", "reset_allowed": True})


def run_server(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"Mock password recovery listening on http://{HOST}:{server.server_port}")
    print("Synthetic only; no external network calls are made.")
    return server


def call(
    port: int,
    path: str,
    payload: dict,
    session_id: str | None = None,
) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if session_id is not None:
        headers["X-Test-Session"] = session_id
    request = Request(
        f"http://{HOST}:{port}{path}",
        data=json_bytes(payload),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read())
    except URLError as exc:
        if getattr(exc, "code", None) is not None:
            return exc.code, json.loads(exc.read())
        raise


def self_test() -> None:
    server = run_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    try:
        STATE.reset()
        session = secrets.token_urlsafe(18)
        known = call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)
        unknown = call(port, "/password-recovery/request", {"email": "unknown@example.test"}, session)
        assert known == unknown, "enumeration response differs"
        assert known[0] == 202
        otp = STATE.issued_otp[TEST_ACCOUNT]
        wrong = f"{(int(otp) + 1) % 10_000:04d}"
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": wrong}, session)[0] == 401
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session)[0] == 200
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session)[0] == 400
        STATE.reset()
        session = secrets.token_urlsafe(18)
        call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)
        otp = STATE.issued_otp[TEST_ACCOUNT]
        call(port, "/__test/expire", {"email": TEST_ACCOUNT})
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session)[0] == 400
        STATE.reset()
        session = secrets.token_urlsafe(18)
        for _ in range(REQUEST_LIMIT):
            assert call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)[0] == 202
        assert call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)[0] == 429
        STATE.reset()
        session_a = secrets.token_urlsafe(18)
        session_b = secrets.token_urlsafe(18)
        call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session_a)
        otp = STATE.issued_otp[TEST_ACCOUNT]
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session_b)[0] == 400
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session_a)[0] == 200
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": otp}, session_a)[0] == 400
        STATE.reset()
        session = secrets.token_urlsafe(18)
        call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)
        otp = STATE.issued_otp[TEST_ACCOUNT]
        wrong = f"{(int(otp) + 1) % 10_000:04d}"
        for _ in range(VERIFY_LIMIT - 1):
            assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": wrong}, session)[0] == 401
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": wrong}, session)[0] == 423
        assert call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session)[0] == 202
        assert STATE.failed_attempts[TEST_ACCOUNT] == VERIFY_LIMIT
        assert STATE.locked_until[TEST_ACCOUNT] > time.time()
        assert call(port, "/password-recovery/verify", {"email": TEST_ACCOUNT, "otp": wrong}, session)[0] == 423
        print("SELF_TEST_OK")
    finally:
        server.shutdown()
        server.server_close()


def assessment_log(case: str, attempt: str, status: int, body: dict) -> None:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    message = str(body.get("error", body.get("status", "ok")))
    print(f"{timestamp} case={case} attempt={attempt} status={status} message={message}")


def assessment() -> None:
    """Run an explicitly synthetic test against an ephemeral loopback server."""
    server = run_server(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_port
    print("Assessment environment: synthetic loopback only (127.0.0.1, ephemeral port).")
    print(f"Policy: VERIFY_LIMIT={VERIFY_LIMIT}, lockout={LOCKOUT_SECONDS}s, TTL={OTP_TTL_SECONDS}s.")
    print("OTP values, session identifiers, payloads, and cookies are not printed or logged.")
    try:
        STATE.reset()
        session = secrets.token_urlsafe(18)
        request_status, request_body = call(
            port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session
        )
        assessment_log("lockout", "challenge", request_status, request_body)
        with STATE.lock:
            otp = STATE.issued_otp[TEST_ACCOUNT]
        assert len(otp) == 4 and otp.isdigit()
        for attempt in range(1, 21):
            wrong = f"{(int(otp) + attempt) % 10_000:04d}"
            if wrong == otp:
                raise AssertionError("generated invalid fixture matched challenge")
            status, body = call(
                port,
                "/password-recovery/verify",
                {"email": TEST_ACCOUNT, "otp": wrong},
                session,
            )
            assessment_log("lockout", str(attempt), status, body)
        with STATE.lock:
            failures = STATE.failed_attempts[TEST_ACCOUNT]
            locked = STATE.locked_until.get(TEST_ACCOUNT, 0) > time.time()
        print(f"lockout summary: server_counted_failures={failures} active_lockout={locked}")
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            session,
        )
        assessment_log("valid_after_20", "1", status, body)
        with STATE.lock:
            STATE.locked_until[TEST_ACCOUNT] = time.time() - 1
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            session,
        )
        assessment_log("valid_after_cooldown_fixture", "1", status, body)

        STATE.reset()
        session_a = secrets.token_urlsafe(18)
        session_b = secrets.token_urlsafe(18)
        status, body = call(
            port, "/password-recovery/request", {"email": TEST_ACCOUNT}, session_a
        )
        assessment_log("binding_replay", "challenge", status, body)
        with STATE.lock:
            otp = STATE.issued_otp[TEST_ACCOUNT]
            bound_session = STATE.issued_session[TEST_ACCOUNT]
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            session_b,
        )
        assessment_log("wrong_session", "1", status, body)
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            session_a,
        )
        assessment_log("correct_bound_session", "1", status, body)
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            session_a,
        )
        assessment_log("replay", "1", status, body)
        print(f"session binding summary: challenge_bound={bound_session == session_a}")

        STATE.reset()
        expiry_session = secrets.token_urlsafe(18)
        status, body = call(
            port,
            "/password-recovery/request",
            {"email": TEST_ACCOUNT},
            expiry_session,
        )
        assessment_log("expiration", "challenge", status, body)
        with STATE.lock:
            otp = STATE.issued_otp[TEST_ACCOUNT]
        status, body = call(port, "/__test/expire", {"email": TEST_ACCOUNT})
        assessment_log("expiration_fixture", "local-only", status, body)
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": otp},
            expiry_session,
        )
        assessment_log("expired_challenge", "1", status, body)

        STATE.reset()
        request_session = secrets.token_urlsafe(18)
        for attempt in range(1, REQUEST_LIMIT + 2):
            status, body = call(
                port,
                "/password-recovery/request",
                {"email": TEST_ACCOUNT},
                request_session,
            )
            assessment_log("request_rate_limit", str(attempt), status, body)

        STATE.reset()
        reissue_session = secrets.token_urlsafe(18)
        call(port, "/password-recovery/request", {"email": TEST_ACCOUNT}, reissue_session)
        with STATE.lock:
            otp = STATE.issued_otp[TEST_ACCOUNT]
        wrong = f"{(int(otp) + 1) % 10_000:04d}"
        for attempt in range(1, VERIFY_LIMIT + 1):
            status, body = call(
                port,
                "/password-recovery/verify",
                {"email": TEST_ACCOUNT, "otp": wrong},
                reissue_session,
            )
            assessment_log("pre_reissue_lockout", str(attempt), status, body)
        status, body = call(
            port, "/password-recovery/request", {"email": TEST_ACCOUNT}, reissue_session
        )
        assessment_log("reissue_after_lockout", "1", status, body)
        with STATE.lock:
            attempts_after_reissue = STATE.failed_attempts.get(TEST_ACCOUNT, 0)
            lockout_after_reissue = STATE.locked_until.get(TEST_ACCOUNT, 0) > time.time()
            otp = STATE.issued_otp[TEST_ACCOUNT]
        wrong = f"{(int(otp) + 1) % 10_000:04d}"
        status, body = call(
            port,
            "/password-recovery/verify",
            {"email": TEST_ACCOUNT, "otp": wrong},
            reissue_session,
        )
        assessment_log("post_reissue_wrong", "1", status, body)
        print(
            "reissue summary: "
            f"server_count_after_reissue={attempts_after_reissue} "
            f"lockout_active_after_reissue={lockout_after_reissue}"
        )

        print("ASSESSMENT_COMPLETE; no external host contacted.")
    finally:
        server.shutdown()
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Loopback-only password recovery mock")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--assessment", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.assessment:
        assessment()
        return
    run_server(args.port).serve_forever()


if __name__ == "__main__":
    main()
