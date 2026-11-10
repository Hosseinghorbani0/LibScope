"""Use disposable local state for every test run."""
import os
import tempfile
from pathlib import Path

import pytest

_test_database_dir = tempfile.TemporaryDirectory(prefix="libscope-tests-")
_test_database = Path(_test_database_dir.name) / "libscope.db"

os.environ["LIBSCOPE_DATABASE_URL"] = f"sqlite:///{_test_database.as_posix()}"
os.environ["LIBSCOPE_ENVIRONMENT"] = "development"
os.environ.pop("LIBSCOPE_API_KEY", None)


@pytest.fixture(scope="session", autouse=True)
def dispose_test_database():
    yield
    from libscope.core import database

    if database._engine is not None:
        database._engine.dispose()
    _test_database_dir.cleanup()

