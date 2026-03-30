@echo off
REM Netflix-style Deployment Script for AI Database Assistant (Windows)

echo 🚀 Starting Netflix-style deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create SSL directory
if not exist ssl mkdir ssl

REM Generate self-signed SSL certificate (for demo purposes)
if not exist ssl\cert.pem (
    echo 🔐 Generating SSL certificate...
    openssl req -x509 -newkey rsa:4096 -keyout ssl\key.pem -out ssl\cert.pem -days 365 -nodes -subj "/C=US/ST=California/L=San Francisco/O=AI Database Assistant/CN=localhost"
)

REM Build and start services
echo 🏗️ Building Docker images...
docker-compose build

echo 🔄 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Check service health
echo 🏥 Checking service health...
curl -f http://localhost/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Deployment successful!
    echo 🌐 Application is available at: https://localhost
    echo 🔧 Health check: https://localhost/health
) else (
    echo ❌ Deployment failed. Check logs with: docker-compose logs
)

echo 📊 Service status:
docker-compose ps
