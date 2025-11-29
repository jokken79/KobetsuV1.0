@echo off
REM ============================================
REM UNS Kobetsu Keiyakusho - Windows Startup Script
REM ============================================

echo.
echo ==========================================
echo   UNS Kobetsu Keiyakusho System
echo   Individual Contract Management
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [INFO] Creating .env file from .env.example...
    copy .env.example .env
    echo [WARNING] Please edit .env file with your settings before continuing.
    echo.
    pause
)

REM Parse command line arguments
set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=up"

if /i "%ACTION%"=="up" goto :up
if /i "%ACTION%"=="down" goto :down
if /i "%ACTION%"=="restart" goto :restart
if /i "%ACTION%"=="logs" goto :logs
if /i "%ACTION%"=="build" goto :build
if /i "%ACTION%"=="clean" goto :clean
if /i "%ACTION%"=="migrate" goto :migrate
if /i "%ACTION%"=="status" goto :status

echo Usage: start.bat [up^|down^|restart^|logs^|build^|clean^|migrate^|status]
goto :eof

:up
echo [INFO] Starting all services...
docker-compose up -d
echo.
echo [SUCCESS] Services started!
echo.
echo Access points:
echo   - Frontend:  http://localhost:3010
echo   - Backend:   http://localhost:8010
echo   - API Docs:  http://localhost:8010/docs
echo   - Adminer:   http://localhost:8090
echo.
goto :eof

:down
echo [INFO] Stopping all services...
docker-compose down
echo [SUCCESS] Services stopped.
goto :eof

:restart
echo [INFO] Restarting all services...
docker-compose down
docker-compose up -d
echo [SUCCESS] Services restarted.
goto :eof

:logs
echo [INFO] Showing logs (Ctrl+C to exit)...
docker-compose logs -f
goto :eof

:build
echo [INFO] Rebuilding all containers...
docker-compose build --no-cache
docker-compose up -d
echo [SUCCESS] Containers rebuilt and started.
goto :eof

:clean
echo [WARNING] This will remove all containers, volumes, and images for this project.
set /p confirm="Are you sure? (y/N): "
if /i not "%confirm%"=="y" goto :eof
docker-compose down -v --rmi local
echo [SUCCESS] Cleanup complete.
goto :eof

:migrate
echo [INFO] Running database migrations...
docker-compose exec kobetsu-backend alembic upgrade head
echo [SUCCESS] Migrations complete.
goto :eof

:status
echo [INFO] Service status:
echo.
docker-compose ps
goto :eof
