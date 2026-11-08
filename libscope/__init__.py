"""
LibScope: Open-Source Software Intelligence Platform. Beyond Downloads.
"""
from pathlib import Path

__version__ = "0.1.0"

_root = Path(__file__).resolve().parent.parent
_monorepo_roots = [
    _root / "packages" / "core",
    _root / "packages" / "providers",
    _root / "packages" / "analyzers",
    _root / "packages" / "scoring",
    _root / "packages" / "reporting",
    _root / "packages" / "ai",
    _root / "apps" / "api",
    _root / "apps" / "cli",
]

for _mr in _monorepo_roots:
    _pkg_dir = _mr / "libscope"
    if _pkg_dir.is_dir() and str(_pkg_dir) not in __path__:
        __path__.append(str(_pkg_dir))

