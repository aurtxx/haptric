"""Non-destructive contract checks for the local examination platform.

These tests intentionally do not target EZExam or any external service. Set
QA_API_BASE_URL to a local disposable deployment to activate the health check.
Future endpoint checks should use synthetic fixtures and never log credentials,
cookies, tokens, answer keys or private student data.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


LOCAL_API = os.getenv("QA_API_BASE_URL", "").rstrip("/")


def _safe_get(path: str) -> tuple[int, str]:
    """GET a local health/metadata endpoint without printing response details."""

    if not LOCAL_API:
        pytest.skip("Set QA_API_BASE_URL to a local disposable service to run integration checks")
    request = Request(f"{LOCAL_API}{path}", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=5) as response:  # noqa: S310 - URL is explicit local test config
            body = response.read(4096).decode("utf-8", errors="replace")
            return response.status, body
    except HTTPError as exc:
        # Keep body out of test output: it may contain implementation details.
        return exc.code, ""
    except URLError as exc:
        pytest.fail(f"Configured local QA service is unreachable: {exc.reason}")


def test_local_health_contract() -> None:
    """A local deployment must expose a non-secret health response."""

    status, body = _safe_get("/api/health/")
    assert status == 200, "local health endpoint did not return HTTP 200"
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        pytest.fail("health response was not JSON")
    assert payload.get("status") in {"ok", "healthy"}
    assert not any(key.lower() in {"token", "secret", "password", "cookie"} for key in payload)


@pytest.mark.skip(reason="Requires seeded local tenant fixtures and approved API contract")
def test_cross_tenant_object_access_is_denied() -> None:
    """Placeholder: implement with two disposable tenants, never real records."""

    raise AssertionError("Implement after tenant-scoped API fixtures are available")


@pytest.mark.skip(reason="Requires an approved local attempt fixture and API contract")
def test_submission_is_idempotent_and_server_timed() -> None:
    """Placeholder: replay one synthetic submission and assert one receipt."""

    raise AssertionError("Implement after attempt/submission endpoints are available")


@pytest.mark.skip(reason="Requires sync outbox endpoint and two disposable local nodes")
def test_sync_replay_does_not_duplicate_events() -> None:
    """Placeholder: replay one synthetic outbox event and inspect audit count."""

    raise AssertionError("Implement after sync contract is available")
