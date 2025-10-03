# Threat Detection System - Demo Startup Script
# Run this script to start all components

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🏠 Threat Detection System Startup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green

# Start Kafka containers
Write-Host ""
Write-Host "Starting Kafka containers..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start Kafka containers" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Kafka containers started" -ForegroundColor Green

# Wait for Kafka to be ready
Write-Host ""
Write-Host "Waiting for Kafka to be ready (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check if .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host ""
    Write-Host "❌ Please edit backend\.env with your API keys before continuing!" -ForegroundColor Red
    Write-Host "   Required: GOOGLE_API_KEY and PINECONE_API_KEY" -ForegroundColor Red
    Write-Host ""
    notepad "backend\.env"
    exit 1
}

# Check if sample_videos directory exists
if (-not (Test-Path "sample_videos")) {
    Write-Host ""
    Write-Host "Creating sample_videos directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "sample_videos"
    Write-Host "⚠️  Please add your video files to sample_videos/ directory" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🚀 Starting Backend Services" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in new window
Write-Host "Starting backend server (new window)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python backend\main.py"

# Wait for backend to start
Write-Host "Waiting for backend to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "🎨 Starting Frontend" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Start frontend in new window
Write-Host "Starting frontend (new window)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "✅ SYSTEM STARTED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  Dashboard:  http://localhost:3000" -ForegroundColor White
Write-Host "  API:        http://localhost:8000" -ForegroundColor White
Write-Host "  Kafka UI:   http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "Waiting 5 seconds before opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Open browser
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Write-Host ""
Write-Host "Stopping services..." -ForegroundColor Yellow
docker-compose down
Write-Host "✅ All services stopped" -ForegroundColor Green