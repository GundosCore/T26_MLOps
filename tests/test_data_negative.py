"""Проверки отклонения нарушений контракта и принятия граничных значений."""

import pytest

from mlops_team1.validate_data import validate_dataset


@pytest.mark.parametrize(
    ("column", "value", "check_name"),
    [
        ("DepHour", 24, "ranges"),
        ("DepHour", -1, "ranges"),
        ("DepHour", 10.5, "types"),
        ("IsWeekend", 2, "allowed_values"),
        ("ArrDelay", 1441, "ranges"),
        ("FlightDate", "2026-02-30", "types"),
        ("DepHour", "", "no_missing_values"),
    ],
    ids=[
        "dephour-24-above-max",
        "dephour-minus1-below-min",
        "dephour-fractional",
        "isweekend-2",
        "arrdelay-1441-above-max",
        "date-feb-30",
        "dephour-empty",
    ],
)
def test_value_outside_contract_is_rejected(
    valid_frame, csv_factory, contract_path, column, value, check_name
):
    frame = valid_frame.copy()
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    result = validate_dataset(csv_factory(frame), contract_path)
    failed_checks = [check["name"] for check in result["checks"] if check["passed"] is False]
    diagnostic = f"{column}={value!r}; failed checks: {failed_checks}"
    assert result["passed"] is False, f"Invalid value was accepted: {diagnostic}"
    assert check_name in failed_checks, f"Expected {check_name!r} to fail: {diagnostic}"


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("DepHour", 0),
        ("DepHour", 23),
        ("IsWeekend", 1),
        ("ArrDelay", -180),
        ("ArrDelay", 1440),
    ],
    ids=[
        "dephour-0-min",
        "dephour-23-max",
        "isweekend-1",
        "arrdelay-minus180-min",
        "arrdelay-1440-max",
    ],
)
def test_boundary_value_is_accepted(valid_frame, csv_factory, contract_path, column, value):
    frame = valid_frame.copy()
    frame.loc[0, column] = value
    result = validate_dataset(csv_factory(frame), contract_path)
    failed_checks = [check["name"] for check in result["checks"] if check["passed"] is False]
    assert result["passed"] is True, (
        f"Boundary value was rejected: {column}={value!r}; failed checks: {failed_checks}"
    )
