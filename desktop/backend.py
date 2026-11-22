"""Run the local LibScope API sidecar used by the desktop application."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if not getattr(sys, "frozen", False):
    for relative_path in (
        ".",
        "packages/core",
        "packages/providers",
        "packages/analyzers",
        "packages/scoring",
        "packages/reporting",
        "packages/ai",
        "apps/api",
    ):
        sys.path.insert(0, str(ROOT / relative_path))

data_directory = os.environ.get("LIBSCOPE_DESKTOP_DATA_DIR")
if data_directory:
    from sqlalchemy.engine import URL

    data_path = Path(data_directory).expanduser().resolve()
    data_path.mkdir(parents=True, exist_ok=True)
    os.environ["LIBSCOPE_DATABASE_URL"] = URL.create(
        "sqlite",
        database=str(data_path / "libscope.db"),
    ).render_as_string(hide_password=False)


def main():
    import uvicorn
    from libscope.api.main import app

    uvicorn.run(
        app,
        host=os.environ.get("LIBSCOPE_HOST", "127.0.0.1"),
        port=int(os.environ.get("LIBSCOPE_PORT", "48193")),
        log_level=os.environ.get("LIBSCOPE_LOG_LEVEL", "INFO").lower(),
    )


if __name__ == "__main__":
    main()
