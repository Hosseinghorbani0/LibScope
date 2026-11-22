from pathlib import Path

from libscope.core.database import _normalize_sqlite_url
from sqlalchemy.engine import URL, make_url


def test_normalize_sqlite_url_preserves_encoded_user_data_paths(tmp_path: Path):
    database_path = tmp_path / "LibScope Data #1%" / "libscope.db"
    original_url = URL.create("sqlite", database=str(database_path)).render_as_string(
        hide_password=False
    )

    normalized_url = _normalize_sqlite_url(original_url)

    assert make_url(normalized_url).database == str(database_path.resolve())
    assert database_path.parent.is_dir()
