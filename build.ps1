# Think Better - Build Script (Windows)
# Equivalent of `make build` for Windows users: same version, commit and
# build date in the binary (override with $env:VERSION, $env:COMMIT, $env:BUILD_DATE).

$ErrorActionPreference = "Stop"

# Output of a git command, or $Default when git is missing or fails.
function Get-GitValue([string]$Default, [string[]]$GitArgs) {
    try {
        $out = & git @GitArgs 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return "$out".Trim() }
    } catch { }
    return $Default
}

$version = if ($env:VERSION) { $env:VERSION } else { Get-GitValue "dev" @("describe", "--tags", "--always", "--dirty") }
$commit = if ($env:COMMIT) { $env:COMMIT } else { Get-GitValue "unknown" @("rev-parse", "--short", "HEAD") }
# Commit date rather than the current time, so rebuilding a commit gives the same binary.
$buildDate = if ($env:BUILD_DATE) { $env:BUILD_DATE } else { Get-GitValue "unknown" @("log", "-1", "--format=%cs") }

Write-Host "=== Think Better Build ($version) ===" -ForegroundColor Cyan

go generate ./internal/skills
if ($LASTEXITCODE -ne 0) { Write-Host "go generate failed!" -ForegroundColor Red; exit 1 }

if (-not (Test-Path "bin")) { New-Item -ItemType Directory -Path "bin" -Force | Out-Null }
$env:CGO_ENABLED = "0"
go build -ldflags "-s -w -X main.version=$version -X main.commit=$commit -X main.buildDate=$buildDate" -o "bin\think-better.exe" ./cmd/think-better
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed!" -ForegroundColor Red; exit 1 }
Write-Host "Built: bin\think-better.exe" -ForegroundColor Green
