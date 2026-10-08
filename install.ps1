# Think Better — one-line installer for Windows
#
#   irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
#
# Options (environment variables):
#   THINK_BETTER_VERSION  Release tag to install, e.g. v1.0.3 (default: latest)
#   INSTALL_DIR           Where to put the binary (default: %LOCALAPPDATA%\think-better)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # Invoke-WebRequest is much faster without the progress bar

$Repo = "HoangTheQuyen/think-better"
$Binary = "think-better"
$Version = if ($env:THINK_BETTER_VERSION) { $env:THINK_BETTER_VERSION } else { "latest" }
$InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "think-better" }

# --- Detect architecture ---
$Arch = if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "amd64" }
$Asset = "${Binary}-windows-${Arch}.exe"
$BaseUrl = if ($Version -eq "latest") {
    "https://github.com/${Repo}/releases/latest/download"
} else {
    "https://github.com/${Repo}/releases/download/${Version}"
}

Write-Host "🧠 Think Better Installer" -ForegroundColor Cyan
Write-Host "   Platform: windows/${Arch}"
Write-Host "   Version:  ${Version}"

# --- Download ---
$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ("think-better-" + [System.Guid]::NewGuid())
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null
$TmpFile = Join-Path $TmpDir "${Binary}.exe"

try {
    Write-Host "   Downloading: ${BaseUrl}/${Asset}"
    try {
        Invoke-WebRequest -Uri "${BaseUrl}/${Asset}" -OutFile $TmpFile -UseBasicParsing
    }
    catch {
        throw "Download failed. Check that release ${Version} exists for windows/${Arch}."
    }

    # --- Verify checksum ---
    $ChecksumFile = Join-Path $TmpDir "checksums.txt"
    $HaveChecksums = $true
    try { Invoke-WebRequest -Uri "${BaseUrl}/checksums.txt" -OutFile $ChecksumFile -UseBasicParsing }
    catch { $HaveChecksums = $false }

    if ($HaveChecksums) {
        $Line = Get-Content $ChecksumFile | Where-Object { (($_ -split '\s+')[1] -replace '^\*', '') -eq $Asset } | Select-Object -First 1
        if (-not $Line) {
            throw "No checksum for ${Asset} in checksums.txt"
        }
        $Expected = ($Line -split '\s+')[0].ToLower()
        $Actual = (Get-FileHash -Algorithm SHA256 $TmpFile).Hash.ToLower()
        if ($Expected -ne $Actual) {
            throw "Checksum mismatch for ${Asset} (expected ${Expected}, got ${Actual})"
        }
        Write-Host "   Checksum verified ✓"
    }
    else {
        Write-Host "⚠️  checksums.txt not found for this release — skipping verification" -ForegroundColor Yellow
    }

    # --- Install ---
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    $DestPath = Join-Path $InstallDir "${Binary}.exe"
    Move-Item -Path $TmpFile -Destination $DestPath -Force
    Write-Host "✅ Installed to ${DestPath}" -ForegroundColor Green
}
finally {
    Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
}

# --- Add to PATH ---
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if (($UserPath -split ';') -notcontains $InstallDir) {
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
Write-Host "🚀 Ready! In your project directory, run:" -ForegroundColor Cyan
Write-Host "   think-better init --ai claude      # or: copilot, antigravity, opencode"
