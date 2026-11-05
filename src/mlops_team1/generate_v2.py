"""Детерминированное синтетическое продолжение учебного образца (данные v2).

Берёт файл v1 и дописывает по одной строке на каждый следующий день.
Один и тот же вход, seed и число дней всегда дают одинаковые байты.
Только стандартная библиотека.
"""

import argparse
import csv
import datetime
import random
import sys
from pathlib import Path

HEADER = ["FlightDate", "DepHour", "IsWeekend", "ArrDelay"]
DATE_FORMAT = "%Y-%m-%d"


def read_base(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0] != HEADER:
        raise ValueError(f"unexpected header in {path}: {rows[:1]}")
    return rows[1:]


def make_rows(last_date: datetime.date, days: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    result = []
    for offset in range(1, days + 1):
        day = last_date + datetime.timedelta(days=offset)
        dep_hour = rng.randint(5, 21)
        arr_delay = rng.randint(4, 45)
        is_weekend = 1 if day.weekday() >= 5 else 0
        result.append([day.strftime(DATE_FORMAT), str(dep_hour), str(is_weekend), str(arr_delay)])
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path, help="CSV версии v1")
    parser.add_argument("--out", required=True, type=Path, help="куда записать v2")
    parser.add_argument("--days", required=True, type=int, help="сколько дней добавить")
    parser.add_argument("--seed", required=True, type=int, help="seed генератора")
    args = parser.parse_args(argv)

    base = read_base(args.base)
    last = (
        datetime.datetime.strptime(base[-1][0], DATE_FORMAT)
        .replace(tzinfo=datetime.UTC)
        .date()
    )
    new_rows = make_rows(last, args.days, args.seed)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(base)
        writer.writerows(new_rows)
    print(f"written {len(base) + len(new_rows)} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
