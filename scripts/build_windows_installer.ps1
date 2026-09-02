$ErrorActionPreference = "Stop"

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "Python is required and was not found on PATH."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

$requirementsPath = Join-Path $rootDir "requirements.txt"
if (Test-Path $requirementsPath) {
    & python -m pip install -r $requirementsPath
}

& python tools/build_release.py
if ($LASTEXITCODE -ne 0) {
    throw "StudyApp build failed."
}

Write-Host "Packages are in dist/ and on the Desktop (Windows zip + Linux portable tar.gz)."
