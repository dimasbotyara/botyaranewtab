"""Pytest setup for botyaranewtab.

`config.py` resolves the data directory at import time, so the env var has to be
set before anything imports `app` — otherwise tests would write into the repo.
"""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOTYARA_DATA_DIR", tempfile.mkdtemp(prefix="botyara-test-"))

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def database():
    from database import init_db

    init_db()
    yield


@pytest.fixture()
def client():
    from app import app

    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client
