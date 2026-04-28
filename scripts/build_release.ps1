param(
    [switch]$SkipInstaller
)

# Build onefile app + single-file Inno Setup installer (Windows).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Remove-TreeInsideRoot {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
    $targetFull = [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath))
    $rootPrefix = $rootFull + '\'
    if ($targetFull -eq $rootFull -or -not $targetFull.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside the repository root: $targetFull"
    }
    Remove-Item -LiteralPath $targetFull -Recurse -Force -ErrorAction SilentlyContinue
}

function Get-PythonCommand {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return @($python.Source)
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & $py.Source -3 --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @($py.Source, "-3")
            }
        } catch {
            # Keep probing quiet; the final error below explains the required setup.
        }
    }

    throw "Python 3 was not found. Install Python 3 and ensure either 'python' or 'py -3' works before building."
}

function Get-RegexValue {
    param(
        [Parameter(Mandatory = $true)][string]$Text,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $match = [regex]::Match($Text, $Pattern)
    if (!$match.Success) {
        throw "Could not read $Label."
    }
    return $match.Groups[1].Value
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

$Python = @(Get-PythonCommand)
$PythonExe = $Python[0]
$PythonArgs = if ($Python.Count -gt 1) { $Python[1..($Python.Count - 1)] } else { @() }
$BuildVenv = Join-Path $Root ".venv-build"
$BuildPython = Join-Path $BuildVenv "Scripts\python.exe"
$Iss = Join-Path $Root "installer\NetworkManagerPro.iss"

$CoreVersion = Get-RegexValue -Text (Get-Content -Raw (Join-Path $Root "core.py")) -Pattern 'APP_VERSION\s*=\s*"([^"]+)"' -Label "core APP_VERSION"
$ProjectVersion = Get-RegexValue -Text (Get-Content -Raw (Join-Path $Root "pyproject.toml")) -Pattern 'version\s*=\s*"([^"]+)"' -Label "pyproject version"
$InstallerVersion = Get-RegexValue -Text (Get-Content -Raw $Iss) -Pattern '#define\s+MyAppVersion\s+"([^"]+)"' -Label "installer version"
if ($CoreVersion -ne $ProjectVersion -or $CoreVersion -ne $InstallerVersion) {
    throw "Version mismatch: core=$CoreVersion pyproject=$ProjectVersion installer=$InstallerVersion"
}

Write-Host "Cleaning old build artifacts..." -ForegroundColor Cyan
Remove-TreeInsideRoot "build"
Remove-TreeInsideRoot "dist"
Remove-TreeInsideRoot "installer\output"

if (!(Test-Path $BuildPython)) {
    Write-Host "Creating isolated build environment..." -ForegroundColor Cyan
    Invoke-Native "Create build virtual environment" { & $PythonExe @PythonArgs -m venv $BuildVenv }
}

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
Invoke-Native "Upgrade pip" { & $BuildPython -m pip install --upgrade pip --retries 5 --timeout 60 -q }
Invoke-Native "Install runtime dependencies" { & $BuildPython -m pip install -r requirements.txt --only-binary=:all: --retries 5 --timeout 60 -q }
Invoke-Native "Install PyInstaller" { & $BuildPython -m pip install pyinstaller --retries 5 --timeout 60 -q }

Write-Host "Generating icons..." -ForegroundColor Cyan
Invoke-Native "Generate icons" { & $BuildPython scripts\make_icons.py }

Write-Host "Running PyInstaller..." -ForegroundColor Cyan
Invoke-Native "PyInstaller build" { & $BuildPython -m PyInstaller --noconfirm main.spec }

$Exe = Join-Path $Root "dist\NetworkManagerPro.exe"
if (!(Test-Path $Exe)) {
    throw "Expected build output missing: $Exe"
}

$candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($SkipInstaller) {
    Write-Host "Skipping installer because -SkipInstaller was supplied." -ForegroundColor Yellow
    Write-Host "Build output: dist\NetworkManagerPro.exe" -ForegroundColor Green
} elseif ($iscc) {
    Write-Host "Building installer with Inno Setup..." -ForegroundColor Cyan
    Invoke-Native "Inno Setup build" { & $iscc $Iss }
    $Installer = Join-Path $Root "installer\output\NetworkManagerPro-Setup-$CoreVersion.exe"
    if (!(Test-Path $Installer)) {
        throw "Expected installer output missing: $Installer"
    }
    Write-Host "Done. Installer: $Installer" -ForegroundColor Green
} else {
    throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isdl.php, or run scripts\build_release.ps1 -SkipInstaller for a development-only onefile exe."
}
