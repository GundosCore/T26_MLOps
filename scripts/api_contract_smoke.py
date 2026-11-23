"""Проверка контракта /predict по HTTP с сохранением успешного прогона."""

import argparse
import json
import math
import sys
import time
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

CASES = [
    {
        "name": "valid",
        "request_id": "lr7-valid",
        "body": {"dep_hour": 9, "is_weekend": 0},
        "expected_status": 200,
    },
    {
        "name": "hour_out_of_range",
        "request_id": "lr7-hour-out-of-range",
        "body": {"dep_hour": 24, "is_weekend": 0},
        "expected_status": 422,
    },
    {
        "name": "unknown_field",
        "request_id": "lr7-unknown-field",
        "body": {"dep_hour": 9, "is_weekend": 0, "actual_delay": 30},
        "expected_status": 422,
    },
    {
        "name": "wrong_type",
        "request_id": "lr7-wrong-type",
        "body": {"dep_hour": "9", "is_weekend": 0},
        "expected_status": 422,
    },
]
NETWORK_ERRORS = (OSError, HTTPException, ValueError)


def send(method, url, body, headers, *, timeout=3):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, json.load(response)


def wait_until_ready(base_url, timeout):
    if not math.isfinite(timeout) or timeout <= 0:
        raise RuntimeError("readyz: timeout должен быть положительным конечным числом")
    deadline = time.monotonic() + timeout
    reason = "истекло время ожидания"
    while (remaining := deadline - time.monotonic()) > 0:
        try:
            status, _, _ = send("GET", f"{base_url}/readyz", None, {}, timeout=min(3, remaining))
            if status == 200:
                return
            reason = f"status {status}"
        except NETWORK_ERRORS as error:
            reason = str(error)
        time.sleep(max(0, min(0.5, deadline - time.monotonic())))
    raise RuntimeError(f"readyz: сервис не готов за {timeout:g} с ({reason})")


def check_case(case, status, headers, body):
    def fail(reason):
        raise RuntimeError(f"{case['name']}: {reason}")

    expected = case["expected_status"]
    if status != expected:
        fail(f"ожидался status {expected}, получен {status}")
    request_id = next((v for k, v in headers.items() if k.lower() == "x-request-id"), None)
    if request_id != case["request_id"]:
        fail("X-Request-ID в заголовке отличается от отправленного")
    if not isinstance(body, dict) or body.get("request_id") != request_id:
        fail("request_id в теле отличается от заголовка")
    if status == 200:
        if set(body) != {
            "delay_probability",
            "delayed",
            "threshold",
            "model_version",
            "request_id",
        }:
            fail("неверный набор полей ответа")
        for key in ("delay_probability", "threshold"):
            value = body[key]
            if type(value) not in (int, float) or not 0 <= value <= 1:
                fail(f"{key} должен быть числом в [0, 1]")
        if body["delayed"] is not (body["delay_probability"] >= body["threshold"]):
            fail("delayed не соответствует порогу")
        if not isinstance(body["model_version"], str) or not body["model_version"]:
            fail("model_version должен быть непустой строкой")
    elif body.get("error_code") != "validation_error" or not (
        isinstance(body.get("details"), list) and body["details"]
    ):
        fail("ожидались validation_error и непустой список details")
    return request_id


def run_contract_smoke(base_url, timeout):
    base_url = base_url.rstrip("/")
    wait_until_ready(base_url, timeout)
    results = []
    for case in CASES:
        headers = {"Content-Type": "application/json", "X-Request-ID": case["request_id"]}
        try:
            status, response_headers, body = send(
                "POST", f"{base_url}/predict", case["body"], headers
            )
        except NETWORK_ERRORS as error:
            raise RuntimeError(f"{case['name']}: {error}") from error
        request_id = check_case(case, status, response_headers, body)
        results.append(
            {
                "name": case["name"],
                "request": {"method": "POST", "path": "/predict", "body": case["body"]},
                "expected_status": case["expected_status"],
                "actual_status": status,
                "response": body,
                "x_request_id": request_id,
                "passed": True,
            }
        )
    return {"base_url": base_url, "passed": True, "cases": results}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_contract_smoke(args.base_url, args.timeout)
    except RuntimeError as error:
        print(f"CONTRACT SMOKE FAILED: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(rendered.encode("utf-8"))
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
