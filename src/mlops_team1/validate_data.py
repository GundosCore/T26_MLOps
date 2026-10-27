"""Валидатор данных по контракту (ЛР2)."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

MAX_EXAMPLES = 5


class ContractError(Exception):
    """Контракт составлен неверно (неизвестный тип или правило)."""


def sha256_of(path: Path) -> str:
    """SHA-256 по байтам файла."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


SPLIT_FRACTIONS = (0.6, 0.8)  # границы train/validation и validation/test
LATE_MINUTES = 15  # опоздание: ArrDelay >= 15


def split_summary(rows: list[dict], contract: dict) -> dict:
    """Границы периодов, размеры, доля опоздавших и проверка порядка времени."""
    columns = contract["columns"]
    time_col = next(
        (n for n, s in columns.items() if s.get("role") == "event_time"), None
    )
    target_col = next(
        (n for n, s in columns.items() if s.get("role") == "target_source"), None
    )
    if time_col is None or target_col is None:
        raise ContractError("contract needs roles event_time and target_source")
    items = sorted(
        (
            parse_value(r[time_col], columns[time_col]),
            parse_value(r[target_col], columns[target_col]),
        )
        for r in rows
    )
    dates = [day for day, _ in items]
    n = len(items)
    cuts = []
    for fraction in SPLIT_FRACTIONS:
        cut = int(n * fraction)
        while 0 < cut < n and dates[cut] == dates[cut - 1]:
            cut += 1  # не режем один день на две части
        cuts.append(cut)
    parts = {
        "train": items[: cuts[0]],
        "validation": items[cuts[0] : cuts[1]],
        "test": items[cuts[1] :],
    }
    info = {}
    for name, part in parts.items():
        late = sum(1 for _, delay in part if delay >= LATE_MINUTES)
        info[name] = {
            "rows": len(part),
            "start": part[0][0].isoformat() if part else None,
            "end": part[-1][0].isoformat() if part else None,
            "positive_rate": round(late / len(part), 3) if part else None,
        }
    ordered = all(parts.values()) and (
        parts["train"][-1][0]
        < parts["validation"][0][0]
        <= parts["validation"][-1][0]
        < parts["test"][0][0]
    )
    return {"parts": info, "time_order_ok": ordered}


def load_contract(path: Path) -> dict:
    """Читает JSON-контракт; битый файл вызывает исключение."""
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def read_table(path: Path) -> tuple[list[str], list[dict]]:
    """Читает CSV: список имён столбцов и список строк-словарей."""
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        rows = list(reader)
    return columns, rows


def make_check(name: str, passed: bool, details: str) -> dict:
    return {"name": name, "passed": passed, "details": details}


def result(name: str, problems: list[str]) -> dict:
    """Собирает результат проверки из списка нарушений."""
    if not problems:
        return make_check(name, True, "ok")
    shown = "; ".join(problems[:MAX_EXAMPLES])
    hidden = len(problems) - MAX_EXAMPLES
    more = f" (+{hidden} more)" if hidden > 0 else ""
    return make_check(
        name, False, f"{len(problems)} violation(s): {shown}{more}"
    )


def is_empty(raw: str | None) -> bool:
    return raw is None or raw.strip() == ""


def parse_value(raw: str, spec: dict):
    """Приводит строку к типу из контракта; ValueError при несоответствии."""
    kind = spec.get("type")
    if kind == "integer":
        return int(raw.strip())
    if kind == "date":
        text = raw.strip()
        parsed = (
            datetime.strptime(text, spec["format"])
            .replace(tzinfo=UTC)
            .date()
        )
        if parsed.strftime(spec["format"]) != text:
            raise ValueError(f"{text!r} does not match {spec['format']}")
        return parsed
    raise ContractError(f"unsupported type: {kind!r}")


def present_columns(columns: list[str], contract: dict) -> dict:
    """Столбцы контракта, которые есть в файле (отсутствующие ловит другая проверка)."""
    return {
        name: spec
        for name, spec in contract["columns"].items()
        if name in columns
    }


def parsed_cells(rows: list[dict], name: str, spec: dict) -> list:
    """Пары (номер строки в файле, значение) для непустых разобранных ячеек."""
    cells = []
    for index, row in enumerate(rows):
        raw = row.get(name)
        if is_empty(raw):
            continue
        try:
            cells.append((index + 2, parse_value(raw, spec)))
        except ValueError:
            continue
    return cells


def check_required_columns(columns: list[str], contract: dict) -> dict:
    missing = sorted(set(contract["columns"]) - set(columns))
    details = "ok" if not missing else f"missing={missing}"
    return make_check("required_columns", not missing, details)


def check_extra_columns(columns: list[str], contract: dict) -> dict:
    if contract.get("allow_extra_columns", False):
        return make_check("extra_columns", True, "extra columns allowed")
    extra = sorted(set(columns) - set(contract["columns"]))
    details = "ok" if not extra else f"extra={extra}"
    return make_check("extra_columns", not extra, details)


def check_minimum_rows(rows: list[dict], contract: dict) -> dict:
    minimum = contract["minimum_rows"]
    passed = len(rows) >= minimum
    return make_check(
        "minimum_rows", passed, f"rows={len(rows)}, minimum={minimum}"
    )


def check_row_length(columns: list[str], rows: list[dict]) -> dict:
    problems = []
    for index, row in enumerate(rows):
        line = index + 2
        extra = row.get(None)
        if extra:
            problems.append(f"line {line}: {len(extra)} extra cell(s)")
        if any(row.get(name) is None for name in columns):
            problems.append(f"line {line}: too few cells")
    return result("row_length", problems)


def check_not_null(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    problems = []
    for name, spec in present_columns(columns, contract).items():
        if spec.get("nullable", False):
            continue
        for index, row in enumerate(rows):
            if is_empty(row.get(name)):
                problems.append(f"{name} line {index + 2}")
    return result("no_missing_values", problems)


def check_types(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    problems = []
    for name, spec in present_columns(columns, contract).items():
        for index, row in enumerate(rows):
            raw = row.get(name)
            if is_empty(raw):
                continue
            try:
                parse_value(raw, spec)
            except ValueError:
                problems.append(f"{name} line {index + 2}: {raw!r}")
    return result("types", problems)


def check_ranges(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    problems = []
    for name, spec in present_columns(columns, contract).items():
        low = spec.get("minimum")
        high = spec.get("maximum")
        if low is None and high is None:
            continue
        for line, value in parsed_cells(rows, name, spec):
            too_low = low is not None and value < low
            too_high = high is not None and value > high
            if too_low or too_high:
                problems.append(
                    f"{name} line {line}: {value} not in [{low}, {high}]"
                )
    return result("ranges", problems)


def check_allowed_values(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    problems = []
    for name, spec in present_columns(columns, contract).items():
        allowed = spec.get("allowed_values")
        if allowed is None:
            continue
        for line, value in parsed_cells(rows, name, spec):
            if value not in allowed:
                problems.append(
                    f"{name} line {line}: {value} not in {allowed}"
                )
    return result("allowed_values", problems)


def check_duplicates(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    if contract.get("duplicate_rows") != "forbid":
        return make_check("duplicates", True, "duplicates allowed")
    seen: dict = {}
    problems = []
    for index, row in enumerate(rows):
        key = tuple(row.get(name) for name in columns)
        line = index + 2
        if key in seen:
            problems.append(f"line {line} repeats line {seen[key]}")
        else:
            seen[key] = line
    return result("duplicates", problems)


def check_sorted(
    columns: list[str], rows: list[dict], contract: dict
) -> dict:
    problems = []
    for name, spec in present_columns(columns, contract).items():
        order = spec.get("sorted")
        if order is None:
            continue
        if order != "ascending":
            raise ContractError(f"unsupported sorted value: {order!r}")
        previous = None
        for line, value in parsed_cells(rows, name, spec):
            if previous is not None and value < previous:
                problems.append(
                    f"{name} line {line}: {value} is earlier than {previous}"
                )
            previous = value
    return result("sorted", problems)


def run_checks(
    columns: list[str], rows: list[dict], contract: dict
) -> list[dict]:
    return [
        check_required_columns(columns, contract),
        check_extra_columns(columns, contract),
        check_minimum_rows(rows, contract),
        check_row_length(columns, rows),
        check_not_null(columns, rows, contract),
        check_types(columns, rows, contract),
        check_ranges(columns, rows, contract),
        check_allowed_values(columns, rows, contract),
        check_duplicates(columns, rows, contract),
        check_sorted(columns, rows, contract),
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Проверка данных по контракту")
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        contract = load_contract(args.contract)
        columns, rows = read_table(args.data)
        digest = sha256_of(args.data)
        checks = run_checks(columns, rows, contract)
        passed = all(check["passed"] for check in checks)
        split = split_summary(rows, contract) if passed else None
        report_head = {
            "contract_version": contract["contract_version"],
            "dataset": contract["dataset"],
        }
    except (OSError, ValueError, KeyError, ContractError) as exc:
        # ValueError: битый JSON или неверная кодировка; KeyError: в контракте
        # нет обязательного ключа; ContractError: неподдерживаемое правило
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    report = {
        **report_head,
        "data_file": args.data.as_posix(),
        "sha256": digest,
        "rows": len(rows),
        "columns": columns,
        "passed": passed,
        "checks": checks,
        "split": split,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for check in checks:
        status = "OK  " if check["passed"] else "FAIL"
        print(f"{status} {check['name']}: {check['details']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())