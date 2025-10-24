# MontePi3D — build instructions (Windows)

This document describes how to build a distributable Windows application (EXE) for MontePi3D using PyInstaller.

## Current state

- A working Windows build is included in this repo at `dist\MontePi3D\MontePi3D.exe`. Use that for quick testing.

## Prerequisites

-+- Windows machine with Visual C++ redistributable installed (for VTK DLLs).

- Python venv (we assume `.venv` in project root). Activate it first.
- PyInstaller installed in the venv: `pip install pyinstaller`

## Quick build (one-folder recommended for VTK/pyvista)

1. Activate venv in PowerShell:

   .\.venv\Scripts\Activate.ps1

2. Run the build helper (this runs PyInstaller with the provided spec):

   .\build_exe.ps1

3. After completion, check `dist\MontePi3D` and run `dist\MontePi3D\MontePi3D.exe`.

If the default `dist\MontePi3D` is locked (OneDrive or running executable), build into a temporary dist and copy the folder manually:

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean --distpath .\dist_new --workpath .\build_temp montepi.spec
Copy-Item -LiteralPath .\dist_new\MontePi3D -Destination .\dist -Recurse -Force
```

If you prefer a single-file EXE change the `build_exe.ps1` invocation to use `--onefile` or run PyInstaller directly.

## Common problems and fixes

- Missing DLL / import errors for VTK: rebuild using `--onedir` and inspect the `dist\MontePi3D` folder to find which DLLs are missing. You may need to add `--add-binary` entries or modify `montepi.spec` to include specific VTK binaries.
- Qt platform plugin missing (qwindows.dll): find your PySide6 plugins path and add the `platforms` folder either as data or binary in the spec. Example `--add-binary "C:\path\to\PySide6\plugins\platforms\qwindows.dll;PySide6\plugins\platforms"`.
- PyInstaller warnings: check `build\<name>\warn-<name>.txt` (or `build_temp\<name>`) for modules PyInstaller couldn't find and add them to `hiddenimports` in `montepi.spec`.
- Visual C++ runtime errors on target machine: install Microsoft Visual C++ Redistributable (x64) on the target.

## Tips

- Start with `--onedir` to iterate quickly. Once everything works, try `--onefile` if you need a single EXE.
- If OneDrive is enabled on your project folder, it can cause file-locking problems when PyInstaller tries to remove or replace `dist\MontePi3D`. Either pause OneDrive sync for the repo during builds or build to a different `--distpath` and copy the result.
- Use a virtual machine or clean Windows VM to validate the built package.
- If you need help including extra data or DLLs, run the EXE from command-line to capture stdout/stderr (remove `--windowed` temporarily to see console output).
