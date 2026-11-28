"""Экспорт схемы OpenAPI без загрузки модели."""

import argparse
import json
from pathlib import Path

from mlops_team1.api import API_VERSION, create_app


def render_openapi() -> str:
    schema = create_app(Path("missing.joblib")).openapi()
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(render_openapi().encode("utf-8"))
    print(f"OpenAPI {API_VERSION} записан в {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
