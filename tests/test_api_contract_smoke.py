"""Контракт CLI, транспорта и отчёта ЛР7."""

import importlib.util
import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn

from mlops_team1.api import create_app


def load_script(name):
    path = Path(__file__).resolve().parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = load_script("api_contract_smoke")
export = load_script("export_openapi")
SCENARIOS = [
    ("valid", "lr7-valid", {"dep_hour": 9, "is_weekend": 0}, 200),
    ("hour_out_of_range", "lr7-hour-out-of-range", {"dep_hour": 24, "is_weekend": 0}, 422),
    (
        "unknown_field",
        "lr7-unknown-field",
        {"dep_hour": 9, "is_weekend": 0, "actual_delay": 30},
        422,
    ),
    ("wrong_type", "lr7-wrong-type", {"dep_hour": "9", "is_weekend": 0}, 422),
]


def transport(*, target="valid", status=None, header_id=None, changes=None):
    def send(method, url, body, headers, **kwargs):
        if url == "http://example/readyz":
            assert method == "GET"
            return 200, {}, {"status": "ready"}
        assert (method, url) == ("POST", "http://example/predict")
        name, request_id, payload, expected = next(
            s for s in SCENARIOS if s[1] == headers["X-Request-ID"]
        )
        assert body == payload
        response = {"request_id": request_id}
        if name == "valid":
            response.update(delay_probability=0.7, threshold=0.5, delayed=True, model_version="v1")
        else:
            response.update(error_code="validation_error", details=[{"location": ["body"]}])
        if name == target:
            response.update(changes or {})
            return status or expected, {"x-request-id": header_id or request_id}, response
        return expected, {"x-request-id": request_id}, response

    return send


def test_cases_cover_the_four_required_scenarios():
    assert [
        (c["name"], c["request_id"], c["body"], c["expected_status"]) for c in smoke.CASES
    ] == SCENARIOS


def test_report_has_four_passed_cases_with_all_fields(monkeypatch):
    monkeypatch.setattr(smoke, "send", transport())
    report = smoke.run_contract_smoke("http://example/", 1)
    assert set(report) == {"base_url", "passed", "cases"}
    assert report["base_url"] == "http://example"
    assert report["passed"] is True
    for case, (name, request_id, payload, status) in zip(report["cases"], SCENARIOS, strict=True):
        assert case["name"] == name
        assert case["passed"] is True
        assert case["request"] == {"method": "POST", "path": "/predict", "body": payload}
        assert case["actual_status"] == case["expected_status"] == status
        assert case["x_request_id"] == case["response"]["request_id"] == request_id


@pytest.mark.parametrize(
    ("name", "status"),
    [
        pytest.param("valid", 500, id="valid-returns-500"),
        pytest.param("unknown_field", 200, id="unknown-field-accepted"),
        pytest.param("wrong_type", 200, id="wrong-type-accepted"),
        pytest.param("hour_out_of_range", 200, id="hour-24-accepted"),
    ],
)
def test_wrong_status_fails_and_names_the_case(monkeypatch, name, status):
    monkeypatch.setattr(smoke, "send", transport(target=name, status=status))
    with pytest.raises(RuntimeError, match=name):
        smoke.run_contract_smoke("http://example", 1)


def test_request_id_mismatch_in_header_fails(monkeypatch):
    monkeypatch.setattr(
        smoke, "send", transport(header_id="other", changes={"request_id": "other"})
    )
    with pytest.raises(RuntimeError, match="valid:.*X-Request-ID"):
        smoke.run_contract_smoke("http://example", 1)


def test_request_id_mismatch_in_body_fails(monkeypatch):
    monkeypatch.setattr(smoke, "send", transport(changes={"request_id": "other"}))
    with pytest.raises(RuntimeError, match="valid:.*request_id"):
        smoke.run_contract_smoke("http://example", 1)


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"delay_probability": 1.5}, id="probability-above-1"),
        pytest.param({"delayed": False}, id="delayed-inconsistent"),
        pytest.param({"extra": 0}, id="extra-key"),
    ],
)
def test_invalid_success_body_fails(monkeypatch, changes):
    monkeypatch.setattr(smoke, "send", transport(changes=changes))
    with pytest.raises(RuntimeError, match="valid:"):
        smoke.run_contract_smoke("http://example", 1)


def test_main_returns_1_and_writes_no_report_on_failure(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(smoke, "send", transport(target="unknown_field", status=200))
    path = tmp_path / "report.json"
    assert smoke.main(["--base-url", "http://example", "--output", str(path)]) == 1
    assert "CONTRACT SMOKE FAILED: unknown_field:" in capsys.readouterr().err
    assert not path.exists()


def test_smoke_passes_against_real_http_server(trained_model_path, tmp_path, capsys):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        config = uvicorn.Config(create_app(trained_model_path), log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while thread.is_alive() and not server.started and time.monotonic() < deadline:
                time.sleep(0.02)
            assert server.started
            path = tmp_path / "report.json"
            assert (
                smoke.main(["--base-url", f"http://127.0.0.1:{port}", "--output", str(path)]) == 0
            )
            raw = path.read_bytes()
            assert raw.endswith(b"\n") and b"\r" not in raw
            assert raw.decode("utf-8") == capsys.readouterr().out
            cases = json.loads(raw)["cases"]
            assert [c["actual_status"] for c in cases] == [200, 422, 422, 422]
            assert [c["x_request_id"] for c in cases] == [s[1] for s in SCENARIOS]
        finally:
            server.should_exit = True
            thread.join(timeout=10)
        assert not thread.is_alive()


def test_smoke_fails_when_service_is_not_reachable(tmp_path, capsys):
    path = tmp_path / "report.json"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        url = f"http://127.0.0.1:{sock.getsockname()[1]}"
        assert smoke.main(["--base-url", url, "--timeout", "1", "--output", str(path)]) == 1
    assert "CONTRACT SMOKE FAILED: readyz:" in capsys.readouterr().err
    assert not path.exists()


def test_render_openapi_is_deterministic_lf_json():
    rendered = export.render_openapi()
    assert rendered == export.render_openapi()
    assert rendered.endswith("\n") and "\r" not in rendered
    assert json.loads(rendered)["info"]["version"] == "0.3.0"


def test_export_main_writes_the_rendered_schema(tmp_path):
    path = tmp_path / "nested" / "openapi.json"
    assert export.main(["--output", str(path)]) == 0
    assert path.read_bytes() == export.render_openapi().encode("utf-8")
