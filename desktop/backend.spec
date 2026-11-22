# PyInstaller build recipe for the local API sidecar.
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

desktop_dir = Path(SPECPATH)
project_root = desktop_dir.parent
package_roots = (
    "apps/api",
    "packages/ai",
    "packages/analyzers",
    "packages/core",
    "packages/providers",
    "packages/reporting",
    "packages/scoring",
)
datas = collect_data_files("libscope.api") + collect_data_files("libscope.ai")
hiddenimports = []
for package in (
    "libscope.ai",
    "libscope.analyzers",
    "libscope.api",
    "libscope.core",
    "libscope.providers",
    "libscope.reporting",
    "libscope.scoring",
):
    hiddenimports.extend(collect_submodules(package))
sys.path[:] = [path for path in sys.path if Path(path).resolve() != project_root]

analysis = Analysis(
    [str(desktop_dir / "backend.py")],
    pathex=[str(project_root / root) for root in package_roots],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "matplotlib",
        "numpy",
        "pandas",
        "PySide6",
        "shiboken6",
        "pytest",
        "scipy",
        "tensorflow",
        "tkinter",
        "zmq",
    ],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="libscope-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
