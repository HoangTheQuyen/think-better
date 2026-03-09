# Think Better — One-liner installer for Windows
# Usage: irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

$Repo = "HoangTheQuyen/think-better"
$Binary = "think-better"

# --- Detect architecture ---
$Arch = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "amd64" }

$Asset = "${Binary}-windows-${Arch}.exe"
$InstallDir = Join-Path $env:LOCALAPPDATA "think-better"

Write-Host "🧠 Think Better Installer" -ForegroundColor Cyan
Write-Host "   Platform: windows/${Arch}"

# --- Download ---
$Url = "https://github.com/${Repo}/releases/latest/download/${Asset}"
Write-Host "   Downloading: ${Url}"

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
$DestPath = Join-Path $InstallDir "${Binary}.exe"

try {
    Invoke-WebRequest -Uri $Url -OutFile $DestPath -UseBasicParsing
}
catch {
    Write-Host "❌ Download failed. Make sure there is a release at:" -ForegroundColor Red
    Write-Host "   $Url" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Installed to ${DestPath}" -ForegroundColor Green

# --- Add to PATH ---
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$InstallDir", "User")
    $env:PATH = "$env:PATH;$InstallDir"
    Write-Host "✅ Added to PATH (restart terminal to take effect)" -ForegroundColor Green
}
else {
    Write-Host "   Already in PATH" -ForegroundColor Gray
}

# --- Verify ---
Write-Host ""
& $DestPath version
Write-Host ""
Write-Host "🚀 Ready! Run: think-better init --ai claude" -ForegroundColor Cyan
