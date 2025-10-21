<#
Simple build helper for MontePi3D using PyInstaller.
Run from project root in PowerShell with the venv activated:

    .\.venv\Scripts\Activate.ps1
    .\build_exe.ps1
#>

$pyinstaller = Join-Path -Path ".\.venv\Scripts" -ChildPath "pyinstaller.exe"
if (-not (Test-Path $pyinstaller)) {
    Write-Error "PyInstaller not found in .\.venv\Scripts. Install it with: .\.venv\Scripts\pip.exe install pyinstaller"
    exit 1
}

$spec = "montepi.spec"
$cmd = "$pyinstaller --noconfirm --clean $spec"

Write-Host "Running: $cmd"
Invoke-Expression $cmd

Write-Host "Build finished. See dist\\MontePi3D (or dist\\MontePi3D.exe for onefile)."