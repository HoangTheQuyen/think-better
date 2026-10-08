# Think Better - one-line installer for Windows (PowerShell 5.1 and 7+)
#
#   irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
#
# Options (environment variables):
#   THINK_BETTER_VERSION    Release to install, e.g. v1.3.0 or 1.3.0 (default: latest)
#   INSTALL_DIR             Where to put the binary (default: %LOCALAPPDATA%\think-better)
#   THINK_BETTER_UNINSTALL  Set to 1 to remove the binary and its user PATH entry instead
#
# Uninstall:
#   $env:THINK_BETTER_UNINSTALL = "1"; irm https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.ps1 | iex
# Skills already installed in a project are removed with
# `think-better uninstall --skill <name>` (run it before removing the binary).
#
# Keep this file ASCII-only: Windows PowerShell 5.1 reads a script without a
# BOM in the ANSI code page, and non-ASCII punctuation then breaks parsing.

# Everything runs inside a script block so that `irm | iex` does not leave
# functions or preference changes behind in the caller's session.
& {

function Install-ThinkBetter {
    $ErrorActionPreference = "Stop"
    if ($PSVersionTable.PSVersion.Major -ge 6 -and -not $IsWindows) {
        throw "install.ps1 is for Windows. On macOS / Linux use: curl -fsSL https://raw.githubusercontent.com/HoangTheQuyen/think-better/main/install.sh | sh"
    }
    $ProgressPreference = "SilentlyContinue"  # Invoke-WebRequest is much faster without the progress bar

    # Windows PowerShell 5.1 on older .NET defaults to TLS 1.0, which GitHub rejects.
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    }
    catch {
        Write-Verbose "Could not enable TLS 1.2: $_"
    }

    $Repo = "HoangTheQuyen/think-better"
    $Binary = "think-better"
    $Version = if ($env:THINK_BETTER_VERSION) { $env:THINK_BETTER_VERSION.Trim() } else { "latest" }
    $InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "think-better" }
    $DestPath = Join-Path $InstallDir "${Binary}.exe"

    if ($env:THINK_BETTER_UNINSTALL -eq "1") {
        if (Test-Path -LiteralPath $DestPath) {
            Remove-Item -LiteralPath $DestPath -Force
            Write-Host "Removed ${DestPath}" -ForegroundColor Green
        }
        else {
            Write-Host "Nothing to remove: ${DestPath} does not exist"
        }
        # Only drop the directory (and its PATH entry) if nothing else lives there,
        # so a shared INSTALL_DIR such as ~\bin keeps working for other tools.
        if ((Test-Path -LiteralPath $InstallDir) -and @(Get-ChildItem -LiteralPath $InstallDir -Force).Count -gt 0) {
            Write-Host "Kept ${InstallDir} (and its PATH entry): it contains other files"
            return
        }
        if (Test-Path -LiteralPath $InstallDir) {
            Remove-Item -LiteralPath $InstallDir -Force
        }
        if (Update-UserPath -Dir $InstallDir -Remove) {
            Write-Host "Removed ${InstallDir} from your user PATH (restart terminal to take effect)" -ForegroundColor Green
        }
        return
    }

    # Accept "1.3.0" as well as "v1.3.0": release tags always start with "v".
    if ($Version -ne "latest") {
        if ($Version -match '^[0-9]') { $Version = "v$Version" }
        if ($Version -notmatch '^v[0-9]') {
            throw "Invalid THINK_BETTER_VERSION '${Version}' (expected e.g. v1.3.0, 1.3.0 or latest)"
        }
    }

    # --- Detect architecture ---
    $Arch = "amd64"
    try {
        if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { $Arch = "arm64" }
    }
    catch {
        # .NET Framework before 4.7.1 has no RuntimeInformation.
        if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64" -or $env:PROCESSOR_ARCHITEW6432 -eq "ARM64") { $Arch = "arm64" }
    }
    $Asset = "${Binary}-windows-${Arch}.exe"
    $BaseUrl = if ($Version -eq "latest") {
        "https://github.com/${Repo}/releases/latest/download"
    }
    else {
        "https://github.com/${Repo}/releases/download/${Version}"
    }

    Write-Host "Think Better Installer" -ForegroundColor Cyan
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
            throw "Download failed. Check that release ${Version} exists for windows/${Arch}. ($($_.Exception.Message))"
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
            Write-Host "   Checksum verified: OK"
        }
        else {
            Write-Host "Warning: checksums.txt not found for this release - skipping verification" -ForegroundColor Yellow
        }

        # --- Install ---
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        Move-Item -Path $TmpFile -Destination $DestPath -Force
        Write-Host "Installed to ${DestPath}" -ForegroundColor Green
    }
    finally {
        Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
    }

    # --- Add to PATH (only once) ---
    if (Update-UserPath -Dir $InstallDir) {
        Write-Host "Added ${InstallDir} to your user PATH (restart terminal to take effect)" -ForegroundColor Green
    }
    else {
        Write-Host "   Already in PATH" -ForegroundColor Gray
    }
    if (-not @($env:PATH -split ';' | Where-Object { $_ -and ($_.TrimEnd('\') -eq $InstallDir.TrimEnd('\')) })) {
        $env:PATH = "${env:PATH};${InstallDir}"
    }

    # --- Verify ---
    Write-Host ""
    & $DestPath version
    if ($LASTEXITCODE -ne 0) { throw "${DestPath} version failed with exit code ${LASTEXITCODE}" }
    Write-Host ""
    Write-Host "Ready! In your project directory, run:" -ForegroundColor Cyan
    Write-Host "   think-better init --ai claude      # or: copilot, antigravity, opencode"
    Write-Host ""
    Write-Host "To uninstall: think-better uninstall --skill <name> (per project), then run this"
    Write-Host "installer again with `$env:THINK_BETTER_UNINSTALL = `"1`"."
}

# Adds (default) or removes $Dir in the user PATH stored in the registry.
# Reads the raw value so entries like %USERPROFILE%\bin stay unexpanded, and
# compares case-insensitively, ignoring a trailing backslash, so running the
# installer again never adds a duplicate. Returns $true if PATH changed.
function Update-UserPath {
    param([string]$Dir, [switch]$Remove)

    $Key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Environment")
    try {
        $Raw = [string]$Key.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $Kind = [Microsoft.Win32.RegistryValueKind]::ExpandString
        if ($Raw) { $Kind = $Key.GetValueKind("Path") }

        $Norm = $Dir.TrimEnd('\')
        $Entries = @($Raw -split ';' | Where-Object { $_ })
        $Others = @($Entries | Where-Object { $_.TrimEnd('\') -ne $Norm })
        $Present = $Others.Count -ne $Entries.Count

        if ($Remove) {
            if (-not $Present) { return $false }
            $New = $Others
        }
        else {
            if ($Present) { return $false }
            $New = $Entries + $Dir
        }
        $Key.SetValue("Path", ($New -join ';'), $Kind)
    }
    finally {
        $Key.Close()
    }

    # Tell running programs (Explorer, new terminals) that the environment changed:
    # SetEnvironmentVariable broadcasts WM_SETTINGCHANGE.
    [Environment]::SetEnvironmentVariable("THINK_BETTER_INSTALLER", "1", "User")
    [Environment]::SetEnvironmentVariable("THINK_BETTER_INSTALLER", $null, "User")
    return $true
}

Install-ThinkBetter

}
