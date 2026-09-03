#Requires -Version 5.1
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

$iss = Join-Path $rootDir "packaging\windows\studyapp.iss"
$exe = Join-Path $rootDir "dist\StudyApp\StudyApp.exe"
$icon = Join-Path $rootDir "assets\icon.ico"

if (-not (Test-Path $exe)) {
    Write-Host "Building StudyApp.exe first..."
    & python tools/build_release.py --windows
    if ($LASTEXITCODE -ne 0) { throw "Failed to build StudyApp.exe" }
}

if (-not (Test-Path $icon)) {
    & python tools/make_icon.py
}

function Find-ISCC {
    $candidates = @(
        (Get-Command iscc -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $candidates) {
        if ($path -and (Test-Path $path)) { return $path }
    }
    return $null
}

$iscc = Find-ISCC
if (-not $iscc) {
    Write-Host "Inno Setup is not installed. Installing with winget..."
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw @"
לא נמצא Inno Setup ולא נמצא winget.

התקינו Inno Setup 6 מ:
https://jrsoftware.org/isdl.php

ואז הריצו שוב:
powershell -File scripts\build_installer.ps1
"@
    }
    & winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
    $iscc = Find-ISCC
    if (-not $iscc) {
        throw "Inno Setup installed, but ISCC.exe was not found. Close this window, open a new terminal, and run the script again."
    }
}

Write-Host "Compiling installer with $iscc"
$py = Join-Path $rootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$ver = & $py -c "from core.config import VERSION; print(VERSION)"
& $iscc "/DAppVersion=$ver" $iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed" }

$searchDirs = @(
    (Join-Path $rootDir "dist"),
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "dist")
)
$setup = $null
foreach ($dir in $searchDirs) {
    if (Test-Path $dir) {
        $found = Get-ChildItem $dir -Filter "StudyApp-*-setup.exe" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($found) { $setup = $found; break }
    }
}

if (-not $setup) { throw "Setup exe was not created in dist/" }

$projectDist = Join-Path $rootDir "dist"
if (-not (Test-Path $projectDist)) { New-Item -ItemType Directory -Path $projectDist | Out-Null }
$projectCopy = Join-Path $projectDist $setup.Name
if ($setup.FullName -ne $projectCopy) {
    Copy-Item $setup.FullName $projectCopy -Force
    $setup = Get-Item $projectCopy
}

$desktop = [Environment]::GetFolderPath("Desktop")
if (Test-Path $desktop) {
    Copy-Item $setup.FullName (Join-Path $desktop $setup.Name) -Force
    Write-Host "Copied $($setup.Name) to Desktop"
}

Write-Host "OK  $($setup.FullName)  ($([math]::Round($setup.Length / 1MB, 1)) MB)"
Write-Host "This is the file to send to users: double-click to install."
