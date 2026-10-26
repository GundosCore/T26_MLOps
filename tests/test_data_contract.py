"""Тесты контракта данных и валидатора (ЛР2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mlops_team1.validate_data import main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "flights_sample.csv"
CONTRACT = ROOT / "data" / "contract.json"

# Порядок столбцов в образце: FlightDate, DepHour, IsWeekend, ArrDelay
DATE, HOUR, WEEKEND, DELAY = 0, 1, 2, 3


def sample_lines() -> list[str]:
    return SAMPLE.read_text(encoding="utf-8").splitlines()


def set_cell(lines: list[str], row: int, col: int, value: str) -> list[str]:
    """Копия строк, где в одной ячейке подставлено другое значение."""
    parts = lines[row].split(",")
    parts[col] = value
    result = list(lines)
    result[row] = ",".join(parts)
    return result


def drop_last_column(lines: list[str]) -> list[str]:
    return [",".join(line.split(",")[:-1]) for line in lines]


def add_extra_column(lines: list[str]) -> list[str]:
    return [lines[0] + ",Extra"] + [line + ",x" for line in lines[1:]]


def run(
    tmp_path: Path, lines: list[str], contract: Path = CONTRACT
) -> tuple[int, Path]:
    """Пишет данные во временный файл и запускает валидатор."""
    data = tmp_path / "data.csv"
    data.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    report = tmp_path / "reports" / "report.json"
    code = main(
        [
            "--data", str(data),
            "--contract", str(contract),
            "--report", str(report),
        ]
    )
    return code, report


def failed_checks(report: Path) -> set[str]:
    content = json.loads(report.read_text(encoding="utf-8"))
    return {c["name"] for c in content["checks"] if not c["passed"]}


# --- Положительные сценарии ------------------------------------------------


def test_sample_passes(tmp_path: Path) -> None:
    code, report = run(tmp_path, sample_lines())
    content = json.loads(report.read_text(encoding="utf-8"))
    assert code == 0
    assert content["passed"] is True
    assert failed_checks(report) == set()
    assert content["rows"] == 24


def test_report_has_required_fields_and_hash(tmp_path: Path) -> None:
    code, report = run(tmp_path, sample_lines())
    content = json.loads(report.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    data_bytes = (tmp_path / "data.csv").read_bytes()
    assert code == 0
    for key in (
        "contract_version", "dataset", "data_file",
        "sha256", "rows", "columns", "passed", "checks",
    ):
        assert key in content
    assert content["contract_version"] == contract["contract_version"]
    assert content["sha256"] == hashlib.sha256(data_bytes).hexdigest()
    assert len(content["sha256"]) == 64


# --- Негативные сценарии: данные нарушают контракт -------------------------

BAD_CASES = [
    pytest.param(
        lambda ls: set_cell(ls, 1, HOUR, "25"), "ranges", id="dephour_25"
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, WEEKEND, "2"),
        "allowed_values",
        id="isweekend_2",
    ),
    pytest.param(
        drop_last_column, "required_columns", id="no_arrdelay_column"
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, DELAY, ""),
        "no_missing_values",
        id="missing_value",
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, HOUR, "5.5"), "types", id="fractional_hour"
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, DELAY, "2000"),
        "ranges",
        id="arrdelay_too_large",
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, DATE, "05.01.2026"),
        "types",
        id="bad_date_format",
    ),
    pytest.param(
        lambda ls: ls + [ls[-1]], "duplicates", id="duplicate_row"
    ),
    pytest.param(
        lambda ls: set_cell(ls, 2, DATE, "2026-01-01"),
        "sorted",
        id="unsorted_dates",
    ),
    pytest.param(add_extra_column, "extra_columns", id="extra_column"),
    pytest.param(lambda ls: ls[:11], "minimum_rows", id="too_few_rows"),
    pytest.param(
        lambda ls: [ls[0], ls[1] + ",99", *ls[2:]],
        "row_length",
        id="extra_cell_in_row",
    ),
    pytest.param(
        lambda ls: set_cell(ls, 1, DATE, "2026-1-5"),
        "types",
        id="date_without_leading_zero",
    ),
]


@pytest.mark.parametrize(("mutate", "expected"), BAD_CASES)
def test_violation_is_detected(tmp_path: Path, mutate, expected: str) -> None:
    code, report = run(tmp_path, mutate(sample_lines()))
    assert code == 1
    assert failed_checks(report) == {expected}
def test_short_row_is_detected(tmp_path: Path) -> None:
    lines = sample_lines()
    lines[1] = ",".join(lines[1].split(",")[:-1])
    code, report = run(tmp_path, lines)
    assert code == 1
    assert "row_length" in failed_checks(report)


# --- Ошибки чтения: код 2, а не «успех» ------------------------------------


def test_broken_contract_json_fails(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    code, _ = run(tmp_path, sample_lines(), contract=broken)
    assert code == 2


def test_unsupported_type_in_contract_fails(tmp_path: Path) -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract["columns"]["DepHour"]["type"] = "float"
    changed = tmp_path / "contract.json"
    changed.write_text(json.dumps(contract), encoding="utf-8")
    code, _ = run(tmp_path, sample_lines(), contract=changed)
    assert code == 2


def test_missing_data_file_fails(tmp_path: Path) -> None:
    code = main(
        [
            "--data", str(tmp_path / "nope.csv"),
            "--contract", str(CONTRACT),
            "--report", str(tmp_path / "report.json"),
        ]
    )
    assert code == 2