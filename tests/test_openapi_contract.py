from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mlops_team1.api import API_VERSION, create_app

JSON = "application/json"


@pytest.fixture(scope="module")
def app():
    return create_app(Path("missing.joblib"))


@pytest.fixture(scope="module")
def spec(app):
    return app.openapi()


@pytest.fixture(scope="module")
def schemas(spec):
    return spec["components"]["schemas"]


def ref(name):
    return f"#/components/schemas/{name}"


def response_ref(operation, status):
    content = operation["responses"][status]["content"][JSON]
    return content["schema"]["$ref"]


def test_openapi_json_is_served_and_matches_app(app, spec):
    response = TestClient(app).get("/openapi.json")

    assert response.status_code == 200
    assert response.json() == spec
    assert spec["openapi"].startswith("3.1")


def test_info_block_declares_service_and_version(spec):
    info = spec["info"]

    assert info["title"] == "Flight Delay Predictor"
    assert info["version"] == API_VERSION == "0.3.0"
    assert info["description"]


def test_paths_and_methods_are_exactly_documented(spec):
    documented = {path: set(ops) for path, ops in spec["paths"].items()}

    assert documented == {
        "/healthz": {"get"},
        "/readyz": {"get"},
        "/predict": {"post"},
        "/metrics": {"get"},
    }


def test_predict_request_body_is_required_json(spec):
    body = spec["paths"]["/predict"]["post"]["requestBody"]

    assert body["required"] is True
    assert body["content"][JSON]["schema"]["$ref"] == ref("PredictionRequest")


def test_prediction_request_schema_is_closed_and_complete(schemas):
    schema = schemas["PredictionRequest"]

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"dep_hour", "is_weekend"}
    assert set(schema["properties"]) == {"dep_hour", "is_weekend"}
    assert schema["examples"] == [{"dep_hour": 9, "is_weekend": 0}]


@pytest.mark.parametrize(
    ("field", "minimum", "maximum"),
    [
        pytest.param("dep_hour", 0, 23, id="dep-hour-0-23"),
        pytest.param("is_weekend", 0, 1, id="is-weekend-0-1"),
    ],
)
def test_prediction_request_field_constraints(schemas, field, minimum, maximum):
    prop = schemas["PredictionRequest"]["properties"][field]

    assert prop["type"] == "integer"
    assert prop["minimum"] == minimum
    assert prop["maximum"] == maximum


def test_prediction_response_schema_is_closed_and_typed(schemas):
    schema = schemas["PredictionResponse"]
    types = {name: prop["type"] for name, prop in schema["properties"].items()}

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "delay_probability",
        "delayed",
        "threshold",
        "model_version",
        "request_id",
    }
    assert types == {
        "delay_probability": "number",
        "delayed": "boolean",
        "threshold": "number",
        "model_version": "string",
        "request_id": "string",
    }


def test_prediction_response_bounds_and_min_length(schemas):
    props = schemas["PredictionResponse"]["properties"]

    for name in ("delay_probability", "threshold"):
        assert props[name]["minimum"] == 0, name
        assert props[name]["maximum"] == 1, name
    for name in ("model_version", "request_id"):
        assert props[name]["minLength"] == 1, name


@pytest.mark.parametrize(
    ("status", "schema_name"),
    [
        pytest.param("200", "PredictionResponse", id="predict-200"),
        pytest.param("422", "ErrorResponse", id="predict-422"),
        pytest.param("503", "ErrorResponse", id="predict-503"),
    ],
)
def test_predict_documents_responses(spec, status, schema_name):
    operation = spec["paths"]["/predict"]["post"]

    assert set(operation["responses"]) == {"200", "422", "503"}
    assert response_ref(operation, status) == ref(schema_name)


def test_readyz_documents_200_and_503(spec):
    operation = spec["paths"]["/readyz"]["get"]

    assert set(operation["responses"]) == {"200", "503"}
    assert response_ref(operation, "200") == ref("StatusResponse")
    assert response_ref(operation, "503") == ref("ErrorResponse")


def test_healthz_documents_only_200(spec):
    operation = spec["paths"]["/healthz"]["get"]

    assert set(operation["responses"]) == {"200"}
    assert response_ref(operation, "200") == ref("StatusResponse")


def test_error_response_schema(schemas):
    schema = schemas["ErrorResponse"]
    props = schema["properties"]

    assert set(props) == {"error_code", "message", "request_id", "details"}
    assert set(schema["required"]) == {"error_code", "message", "request_id"}
    for name in ("error_code", "message", "request_id"):
        assert props[name]["type"] == "string", name
    assert props["details"]["type"] == "array"
    assert props["details"]["items"]["$ref"] == ref("ErrorItem")


def test_error_item_schema(schemas):
    schema = schemas["ErrorItem"]
    props = schema["properties"]
    location_types = {option["type"] for option in props["location"]["items"]["anyOf"]}

    assert set(schema["required"]) == {"location", "message", "error_type"}
    assert props["location"]["type"] == "array"
    assert location_types == {"string", "integer"}
    assert props["message"]["type"] == "string"
    assert props["error_type"]["type"] == "string"


def test_status_response_schema(schemas):
    schema = schemas["StatusResponse"]

    assert schema["required"] == ["status"]
    assert schema["properties"]["status"]["type"] == "string"
