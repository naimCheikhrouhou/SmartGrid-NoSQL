
# 1. Navigate to the project directory
Set-Location $PSScriptRoot

Write-Host "Starting Smart Grid environment..." -ForegroundColor Cyan

# 2. Start Docker services
docker compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Compose failed!" -ForegroundColor Red
    exit 1
}

# 3. Create virtual environment if it doesn't exist
if (!(Test-Path ".\venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# 4. Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

Write-Host "Smart Grid environment is ready!" -ForegroundColor Green