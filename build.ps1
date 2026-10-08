# Think Better - Build Script (Windows)
# Equivalent of `make build` for Windows users

$ErrorActionPreference = "Stop"
Write-Host "=== Think Better Build ===" -ForegroundColor Cyan

go generate ./internal/skills
if ($LASTEXITCODE -ne 0) { Write-Host "go generate failed!" -ForegroundColor Red; exit 1 }

if (-not (Test-Path "bin")) { New-Item -ItemType Directory -Path "bin" -Force | Out-Null }
$env:CGO_ENABLED = "0"
go build -o "bin\think-better.exe" ./cmd/think-better
if ($LASTEXITCODE -ne 0) { Write-Host "Build failed!" -ForegroundColor Red; exit 1 }
Write-Host "Built: bin\think-better.exe" -ForegroundColor Green
