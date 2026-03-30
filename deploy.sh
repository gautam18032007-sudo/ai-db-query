#!/bin/bash

# Netflix-style Deployment Script for AI Database Assistant

echo "🚀 Starting Netflix-style deployment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create SSL directory
mkdir -p ssl

# Generate self-signed SSL certificate (for demo purposes)
if [ ! -f ssl/cert.pem ]; then
    echo "🔐 Generating SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
        -subj "/C=US/ST=California/L=San Francisco/O=AI Database Assistant/CN=localhost"
fi

# Build and start services
echo "🏗️ Building Docker images..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "🌐 Application is available at: https://localhost"
    echo "🔧 Health check: https://localhost/health"
else
    echo "❌ Deployment failed. Check logs with: docker-compose logs"
fi

echo "📊 Service status:"
docker-compose ps
