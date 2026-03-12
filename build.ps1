# Think Better - Build Script (Windows)
# Equivalent of `make build` for Windows users

Write-Host "=== Think Better Build ===" -ForegroundColor Cyan

# Step 1: Prepare embedded skills
Write-Host "Preparing embedded skills..." -ForegroundColor Yellow
$skillsDir = "internal\skills\skills"
if (Test-Path $skillsDir) { Remove-Item -Recurse -Force $skillsDir }
New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
Copy-Item -Recurse ".agents\skills\make-decision" "$skillsDir\make-decision"
Copy-Item -Recurse ".agents\skills\problem-solving-pro" "$skillsDir\problem-solving-pro"
# Clean __pycache__
Get-ChildItem -Path $skillsDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Done: skills ready for embedding" -ForegroundColor Green

# Step 1b: Prepare embedded workflows
Write-Host "Preparing embedded workflows..." -ForegroundColor Yellow
$workflowsDir = "internal\skills\workflows"
if (Test-Path $workflowsDir) { Remove-Item -Recurse -Force $workflowsDir }
New-Item -ItemType Directory -Path $workflowsDir -Force | Out-Null
Copy-Item ".agents\workflows\*.md" "$workflowsDir\"
Write-Host "Done: workflows ready for embedding" -ForegroundColor Green

# Step 2: Build
Write-Host "Building..." -ForegroundColor Yellow
$binDir = "bin"
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
$env:CGO_ENABLED = "0"
go build -o "$binDir\think-better.exe" ./cmd/make-decision
if ($LASTEXITCODE -eq 0) {
    Write-Host "Built: $binDir\think-better.exe" -ForegroundColor Green
}
else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
