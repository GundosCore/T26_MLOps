import uuid

import pytest
from fastapi.testclient import TestClient

from mlops_team1.api import create_app


@pytest.fixture
def client(trained_model_path):
    with TestClient(create_app(trained_model_path)) as test_client:
        yield test_client


@pytest.fixture
def client_without_model(tmp_path):
    with TestClient(create_app(tmp_path / "missing.joblib")) as test_client:
        yield test_client


@pytest.mark.parametrize(
    ("dep_hour", "is_weekend"),
    [
        pytest.param(0, 0, id="min-hour-weekday"),
        pytest.param(23, 1, id="max-hour-weekend"),
        pytest.param(0, 1, id="min-hour-weekend"),
        pytest.param(23, 0, id="max-hour-weekday"),
    ],
)
def test_boundary_values_are_accepted(client, dep_hour, is_weekend):
    response = client.post(
        "/predict",
        json={"dep_hour": dep_hour, "is_weekend": is_weekend},
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    ("payload", "location"),
    [
        pytest.param(
            {"dep_hour": True, "is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-bool",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": False},
            ["body", "is_weekend"],
            id="weekend-bool",
        ),
        pytest.param(
            {"dep_hour": 9.0, "is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-float-whole",
        ),
        pytest.param(
            {"dep_hour": 9.5, "is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-float-frac",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": 0.0},
            ["body", "is_weekend"],
            id="weekend-float",
        ),
        pytest.param(
            {"dep_hour": None, "is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-null",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": "0"},
            ["body", "is_weekend"],
            id="weekend-string",
        ),
        pytest.param(
            {"dep_hour": 9},
            ["body", "is_weekend"],
            id="weekend-missing",
        ),
        pytest.param(
            {"is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-missing",
        ),
        pytest.param(
            {},
            ["body", "dep_hour"],
            id="empty-object",
        ),
        pytest.param(
            {"dep_hour": -1, "is_weekend": 0},
            ["body", "dep_hour"],
            id="hour-below-min",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": -1},
            ["body", "is_weekend"],
            id="weekend-below-min",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": 0, "actual_delay": 30},
            ["body", "actual_delay"],
            id="future-actual-delay",
        ),
        pytest.param(
            {"dep_hour": 9, "is_weekend": 0, "ArrDelay": 30},
            ["body", "ArrDelay"],
            id="future-arr-delay",
        ),
    ],
)
def test_invalid_request_is_422_with_location(client, payload, location):
    response = client.post("/predict", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "validation_error"
    assert body["details"]
    assert body["details"][0]["location"] == location
    assert isinstance(body["details"][0]["error_type"], str)
    assert body["details"][0]["error_type"]


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"{broken", id="malformed-json"),
        pytest.param(b"[]", id="json-array"),
        pytest.param(b'"text"', id="json-string"),
        pytest.param(b"", id="empty-body"),
    ],
)
def test_non_object_body_is_422(client, content):
    response = client.post(
        "/predict",
        content=content,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


def test_all_errors_of_one_request_are_reported(client):
    response = client.post(
        "/predict",
        json={"dep_hour": 99, "is_weekend": 5, "ArrDelay": 1},
    )

    assert response.status_code == 422
    locations = {tuple(item["location"]) for item in response.json()["details"]}
    assert locations == {
        ("body", "dep_hour"),
        ("body", "is_weekend"),
        ("body", "ArrDelay"),
    }


def test_success_response_invariants_for_every_input(client):
    expected_keys = {
        "delay_probability",
        "delayed",
        "threshold",
        "model_version",
        "request_id",
    }

    for dep_hour in range(24):
        for is_weekend in (0, 1):
            request_id = f"case-{dep_hour}-{is_weekend}"
            response = client.post(
                "/predict",
                json={"dep_hour": dep_hour, "is_weekend": is_weekend},
                headers={"X-Request-ID": request_id},
            )

            message = f"dep_hour={dep_hour}, is_weekend={is_weekend}"
            assert response.status_code == 200, message

            body = response.json()
            assert set(body) == expected_keys, message
            assert isinstance(body["delay_probability"], float), message
            assert 0 <= body["delay_probability"] <= 1, message
            assert isinstance(body["delayed"], bool), message
            assert body["threshold"] == 0.5, message
            assert body["delayed"] == (body["delay_probability"] >= body["threshold"]), message
            assert body["model_version"] == "0.2.0", message
            assert body["request_id"] == request_id, message


def test_response_does_not_leak_internals(client, trained_model_path):
    response = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
    )

    assert response.status_code == 200
    for forbidden in (
        str(trained_model_path),
        "joblib",
        "Traceback",
        "RandomForest",
    ):
        assert forbidden not in response.text


@pytest.mark.parametrize(
    ("method", "path", "expected_status"),
    [
        pytest.param("GET", "/no-such-endpoint", 404, id="unknown-404"),
        pytest.param("GET", "/predict", 405, id="predict-405"),
        pytest.param("POST", "/healthz", 405, id="healthz-405"),
    ],
)
def test_routing_errors_use_error_response(client, method, path, expected_status):
    response = client.request(
        method,
        path,
        headers={"X-Request-ID": "routing-case"},
    )

    assert response.status_code == expected_status
    body = response.json()
    assert set(body) == {"error_code", "message", "request_id", "details"}
    assert body["error_code"] == "http_error"
    assert body["request_id"] == "routing-case"
    assert response.headers["X-Request-ID"] == "routing-case"
    assert "Traceback" not in response.text


def test_422_body_has_exact_error_schema(client):
    response = client.post(
        "/predict",
        json={"dep_hour": 9, "is_weekend": 0, "actual_delay": 30},
    )

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error_code", "message", "request_id", "details"}
    assert all(set(item) == {"location", "message", "error_type"} for item in body["details"])
    assert "Traceback" not in response.text
    assert ".py" not in response.text


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("/readyz", id="readyz"),
        pytest.param("/predict", id="predict"),
    ],
)
def test_503_body_has_exact_error_schema(client_without_model, path):
    response = client_without_model.request(
        "GET" if path == "/readyz" else "POST",
        path,
        json={"dep_hour": 10, "is_weekend": 0} if path == "/predict" else None,
        headers={"X-Request-ID": "no-model-case"},
    )

    assert response.status_code == 503
    body = response.json()
    assert set(body) == {"error_code", "message", "request_id", "details"}
    assert body["error_code"] == "not_ready"
    assert body["details"] == []
    assert body["request_id"] == "no-model-case"
    assert response.headers["X-Request-ID"] == "no-model-case"


def test_invalid_request_without_model_is_422_not_503(client_without_model):
    response = client_without_model.post(
        "/predict",
        json={"dep_hour": 24, "is_weekend": 0},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "validation_error"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        pytest.param(
            "POST",
            "/predict",
            {"dep_hour": 10, "is_weekend": 0},
            id="predict-200",
        ),
        pytest.param(
            "POST",
            "/predict",
            {"dep_hour": 24, "is_weekend": 0},
            id="predict-422",
        ),
        pytest.param("GET", "/healthz", None, id="healthz-200"),
        pytest.param("GET", "/readyz", None, id="readyz-200"),
        pytest.param("GET", "/metrics", None, id="metrics-200"),
        pytest.param("GET", "/openapi.json", None, id="openapi-200"),
        pytest.param("GET", "/no-such-endpoint", None, id="unknown-404"),
    ],
)
def test_request_id_is_echoed_in_header(client, method, path, payload):
    response = client.request(
        method,
        path,
        json=payload,
        headers={"X-Request-ID": "student-case-1"},
    )

    assert response.headers["X-Request-ID"] == "student-case-1"


def test_request_id_in_body_matches_header_for_200_and_422(client):
    for payload, expected_status in (
        ({"dep_hour": 10, "is_weekend": 0}, 200),
        ({}, 422),
    ):
        response = client.post(
            "/predict",
            json=payload,
            headers={"X-Request-ID": "body-header-case"},
        )

        assert response.status_code == expected_status
        assert response.json()["request_id"] == "body-header-case"
        assert response.headers["X-Request-ID"] == "body-header-case"


def test_request_id_is_generated_and_unique_when_absent(client):
    first = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
    )
    second = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
    )

    first_id = first.headers["X-Request-ID"]
    second_id = second.headers["X-Request-ID"]

    assert first_id != second_id
    assert str(uuid.UUID(first_id)) == first_id
    assert str(uuid.UUID(second_id)) == second_id
    assert first.json()["request_id"] == first_id
    assert second.json()["request_id"] == second_id


@pytest.mark.parametrize(
    "request_id",
    [
        pytest.param("", id="empty"),
        pytest.param("has space", id="space"),
        pytest.param("line\nbreak", id="newline"),
        pytest.param("semi;colon", id="semicolon"),
        pytest.param("a/b", id="slash"),
        pytest.param("x" * 129, id="too-long"),
    ],
)
def test_unsafe_request_id_is_replaced_by_uuid(client, request_id):
    response = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    returned_id = response.headers["X-Request-ID"]
    assert returned_id != request_id
    assert str(uuid.UUID(returned_id)) == returned_id
    assert response.json()["request_id"] == returned_id


def test_request_id_of_max_length_is_kept(client):
    request_id = "x" * 128
    response = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id


def test_model_is_loaded_once_per_process(monkeypatch, trained_model_path):
    import mlops_team1.api as api_module

    original_load_bundle = api_module.load_bundle
    calls = []

    def counted_load_bundle(path):
        calls.append(path)
        return original_load_bundle(path)

    monkeypatch.setattr(api_module, "load_bundle", counted_load_bundle)

    with TestClient(create_app(trained_model_path)) as test_client:
        for _ in range(3):
            response = test_client.post(
                "/predict",
                json={"dep_hour": 10, "is_weekend": 0},
            )
            assert response.status_code == 200

    assert len(calls) == 1


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"", id="empty-file"),
        pytest.param(b"not a model", id="garbage"),
    ],
)
def test_corrupt_model_stops_startup(tmp_path, content):
    model_path = tmp_path / "corrupt.joblib"
    model_path.write_bytes(content)

    with pytest.raises(ValueError), TestClient(create_app(model_path)):
        pass


def test_healthz_and_readyz_do_not_run_prediction(monkeypatch, tmp_path):
    import mlops_team1.api as api_module

    class PredictionMustNotRun:
        def predict_proba(self, _features):
            raise AssertionError("predict_proba must not be called")

    model_path = tmp_path / "model.joblib"
    model_path.write_bytes(b"placeholder")

    monkeypatch.setattr(
        api_module,
        "load_bundle",
        lambda _path: {
            "model": PredictionMustNotRun(),
            "features": ["DepHour", "IsWeekend"],
            "version": "0.2.0",
        },
    )

    with TestClient(create_app(model_path)) as test_client:
        assert test_client.get("/healthz").status_code == 200
        assert test_client.get("/readyz").status_code == 200


def test_service_endpoints_work_without_model(client_without_model):
    assert client_without_model.get("/healthz").status_code == 200
    assert client_without_model.get("/metrics").status_code == 200
    assert client_without_model.get("/openapi.json").status_code == 200
    assert client_without_model.get("/docs").status_code == 200


def test_metrics_and_docs_content_types(client):
    response = client.post(
        "/predict",
        json={"dep_hour": 10, "is_weekend": 0},
    )
    assert response.status_code == 200

    metrics = client.get("/metrics")
    docs = client.get("/docs")

    assert metrics.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in metrics.text
    assert docs.headers["content-type"].startswith("text/html")
    assert "swagger" in docs.text.lower()
