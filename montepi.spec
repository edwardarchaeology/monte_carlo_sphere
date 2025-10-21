# montepi.spec
# PyInstaller spec for MontePi3D
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

try:
    project_root = os.path.abspath(os.path.dirname(__file__))
except NameError:
    project_root = os.path.abspath('.')

datas = []
# include UI and assets folders
datas += [(os.path.join(project_root, 'ui', 'main_window.ui'), 'ui')]
datas += [(os.path.join(project_root, 'assets'), 'assets')]

# Conservative hiddenimports (avoid collecting entire large packages up-front)
hiddenimports = [
    'pyvista',
    'pyvistaqt',
    'vtkmodules',
    'vtkmodules.util.numpy_support',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qt5',
]

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    console=False,
    icon=os.path.join(project_root, 'assets', 'app.ico') if os.path.exists(os.path.join(project_root, 'assets', 'app.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MontePi3D',
)
