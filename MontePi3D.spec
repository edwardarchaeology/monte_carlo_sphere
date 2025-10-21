# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ui\\main_window.ui', 'ui'), ('assets', 'assets')],
    hiddenimports=['simulation', 'view3d', 'view2d', 'theme', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_qt5', 'matplotlib.backends.backend_agg', 'matplotlib.backends.backend_tkagg', 'pyvistaqt', 'pyvista'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib.tests', 'pytest', '_pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MontePi3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MontePi3D',
)
