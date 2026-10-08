import re
import tomllib
from pathlib import Path

from mlops_team1 import __version__, ping


def test_ping_returns_clean_nonempty_string():
    result = ping()
    assert isinstance(result, str)
    assert result != ""
    assert result == result.strip()

def test_version_follows_semver_format():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)

def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as f:
        declared = tomllib.load(f)["project"]["version"]
    assert __version__ == declared
