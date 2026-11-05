"""Тесты генератора синтетического продолжения (данные v2)."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from mlops_team1.generate_v2 import main as generate
from mlops_team1.validate_data import main as validate

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "tests" / "fixtures" / "flights_sample_v1.csv"
CONTRACT = ROOT / "data" / "contract.json"
SEED, DAYS = 2026, 16


def make(tmp_path: Path, name: str, seed: int = SEED, days: int = DAYS) -> Path:
    out = tmp_path / name
    code = generate(
        ["--base", str(V1), "--out", str(out), "--days", str(days), "--seed", str(seed)]
    )
    assert code == 0
    return out


def test_same_seed_gives_same_bytes(tmp_path: Path) -> None:
    first = make(tmp_path, "a.csv").read_bytes()
    second = make(tmp_path, "b.csv").read_bytes()
    assert first == second


def test_different_seed_gives_different_rows(tmp_path: Path) -> None:
    assert make(tmp_path, "a.csv").read_bytes() != make(tmp_path, "c.csv", seed=1).read_bytes()


def test_v1_is_kept_as_prefix_and_rows_added(tmp_path: Path) -> None:
    v1_lines = V1.read_text(encoding="utf-8").splitlines()
    v2_lines = make(tmp_path, "a.csv").read_text(encoding="utf-8").splitlines()
    assert v2_lines[: len(v1_lines)] == v1_lines
    assert len(v2_lines) - len(v1_lines) == DAYS


def test_new_rows_continue_dates_and_weekends(tmp_path: Path) -> None:
    lines = make(tmp_path, "a.csv").read_text(encoding="utf-8").splitlines()[1:]
    dates = [datetime.date.fromisoformat(line.split(",")[0]) for line in lines]
    assert dates == sorted(set(dates))
    assert dates[24] == datetime.date(2026, 1, 29)
    for line in lines[24:]:
        day, _, weekend, _ = line.split(",")
        assert int(weekend) == (1 if datetime.date.fromisoformat(day).weekday() >= 5 else 0)


def test_output_has_lf_only(tmp_path: Path) -> None:
    assert b"\r" not in make(tmp_path, "a.csv").read_bytes()


def test_v2_passes_contract(tmp_path: Path) -> None:
    data = make(tmp_path, "a.csv")
    report = tmp_path / "report.json"
    code = validate(
        ["--data", str(data), "--contract", str(CONTRACT), "--report", str(report)]
    )
    content = json.loads(report.read_text(encoding="utf-8"))
    assert code == 0
    assert content["passed"] is True
    assert content["rows"] == 24 + DAYS
    assert content["sha256"] == hashlib.sha256(data.read_bytes()).hexdigest()
