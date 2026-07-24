# Faresta Code Windows PowerShell Installer
# Usage: iwr -Uri "https://raw.githubusercontent.com/panelddos/faresta-code/main/install.ps1" | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$REPO = "https://github.com/panelddos/faresta-code.git"
$INSTALL_DIR = "$env:USERPROFILE\.faresta"
$BIN_DIR = "$env:USERPROFILE\.local\bin"

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     Faresta Code Installer v0.6.0   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command "python3" -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "✖ Python 3.10+ is required but not found." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation."
    exit 1
}

# Check Python version
$pyVersion = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
$versionParts = $pyVersion -split '\.'
$pyMajor = [int]$versionParts[0]
$pyMinor = [int]$versionParts[1]

if ($pyMajor -lt 3 -or ($pyMajor -eq 3 -and $pyMinor -lt 10)) {
    Write-Host "✖ Python 3.10+ required, found $pyVersion" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python $pyVersion" -ForegroundColor Green

# Check git
$git = Get-Command "git" -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "✖ Git is required but not found." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ git" -ForegroundColor Green

# Create bin dir
New-Item -ItemType Directory -Force -Path $BIN_DIR | Out-Null

# Clone or update
if (Test-Path "$INSTALL_DIR\.git") {
    Write-Host "Updating existing installation..."
    Push-Location $INSTALL_DIR
    try {
        & git pull --ff-only 2>$null
    } catch {
        Write-Host "⚠ Could not pull updates, using existing" -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "Cloning Faresta Code from GitHub..."
    if (Test-Path $INSTALL_DIR) {
        Remove-Item -Recurse -Force $INSTALL_DIR
    }
    & git clone --depth 1 $REPO $INSTALL_DIR
}

Write-Host ""

# Create virtualenv
$VENV_DIR = "$INSTALL_DIR\venv"
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "Creating Python virtual environment..."
    & $python.Source -m venv $VENV_DIR
}

# Install dependencies
Write-Host "Installing dependencies (this may take a minute)..."
$pip = "$VENV_DIR\Scripts\pip.exe"
if (-not (Test-Path $pip)) {
    $pip = "$VENV_DIR\Scripts\pip3.exe"
}
& $pip install --quiet --upgrade pip setuptools wheel 2>$null
& $pip install --quiet -e $INSTALL_DIR 2>$null

Write-Host ""

# Create wrapper script
$WRAPPER = "$BIN_DIR\faresta.cmd"
@"
@echo off
"$VENV_DIR\Scripts\faresta.exe" %*
"@ | Out-File -FilePath $WRAPPER -Encoding ascii

# Also create PowerShell wrapper
$PS_WRAPPER = "$BIN_DIR\faresta.ps1"
@"
`$VENV_DIR = "$VENV_DIR"
& "`$VENV_DIR\Scripts\faresta.exe" @args
"@ | Out-File -FilePath $PS_WRAPPER -Encoding utf8

Write-Host "✓ Installed to $INSTALL_DIR" -ForegroundColor Green
Write-Host "✓ Wrapper at  $WRAPPER" -ForegroundColor Green

# PATH check
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$BIN_DIR*") {
    Write-Host ""
    Write-Host "⚠ $BIN_DIR is NOT in your PATH" -ForegroundColor Yellow
    Write-Host "  Add it manually:"
    Write-Host "  [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';$BIN_DIR', 'User')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Or for this session only:"
    Write-Host "  `$env:Path += ';$BIN_DIR'" -ForegroundColor Yellow
} else {
    Write-Host "✓ $BIN_DIR is in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Faresta Code installed!             ║" -ForegroundColor Cyan
Write-Host "║                                      ║" -ForegroundColor Cyan
Write-Host "║  1. Set API key                      ║" -ForegroundColor Cyan
Write-Host "║     `$env:OPENAI_API_KEY='sk-...'     ║" -ForegroundColor Cyan
Write-Host "║                                      ║" -ForegroundColor Cyan
Write-Host "║  2. Start chatting                   ║" -ForegroundColor Cyan
Write-Host "║     faresta chat                      ║" -ForegroundColor Cyan
Write-Host "║                                      ║" -ForegroundColor Cyan
Write-Host "║  3. See all commands                  ║" -ForegroundColor Cyan
Write-Host "║     faresta --help                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Selamat coding!" -ForegroundColor Cyan
