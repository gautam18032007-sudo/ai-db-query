# AI Database Assistant - Netflix-Style Deployment

## 🚀 Production-Ready Deployment

This repository includes everything needed to deploy the AI Database Assistant in a Netflix-style microservices architecture.

## 📦 Deployment Options

### Option 1: Docker Compose (Local/Development)
```bash
# Windows
./deploy.bat

# Linux/Mac
./deploy.sh
```

### Option 2: Kubernetes (Cloud Production)
```bash
# Apply to Kubernetes cluster
kubectl apply -f k8s-deployment.yaml
```

### Option 3: Cloud Platforms
- **AWS ECS**: Use `docker-compose.yml` with ECS integration
- **Google Cloud Run**: Build with `Dockerfile` and deploy to Cloud Run
- **Azure Container Instances**: Use ACI with Docker Compose
- **DigitalOcean App Platform**: Direct deployment from GitHub

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│  AI Assistant   │────│   PostgreSQL    │
│   (SSL/TLS)     │    │   (Flask App)   │    │   (Database)    │
│   Port: 80/443  │    │   Port: 5000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables
- `DB_HOST`: Database host
- `DB_PORT`: Database port (5432)
- `DB_NAME`: Database name (aidb)
- `DB_USER`: Database user (postgres)
- `DB_PASSWORD`: Database password
- `ANTHROPIC_API_KEY`: Claude API key

### Features
- ✅ **Load Balancing** (3 replicas)
- ✅ **SSL/TLS Encryption**
- ✅ **Health Checks**
- ✅ **Auto-scaling Ready**
- ✅ **Database Persistence**
- ✅ **Zero-downtime Deployment**

## 🌐 Access URLs

After deployment:
- **Application**: `https://localhost`
- **Health Check**: `https://localhost/health`
- **API Endpoint**: `https://localhost/chat`

## 📊 Monitoring & Scaling

### Health Checks
- Liveness probe: `/health`
- Readiness probe: `/health`
- Custom metrics available

### Scaling
```bash
# Scale to 5 replicas
kubectl scale deployment ai-db-assistant --replicas=5
```

## 🔒 Security

- SSL/TLS encryption
- Environment variable secrets
- Non-root container user
- Resource limits
- Network policies

## 🚀 Quick Start

1. **Install Docker & Docker Compose**
2. **Clone repository**
3. **Run deployment script**
4. **Access at https://localhost**

## 📝 Production Notes

- Replace self-signed certificates with proper SSL certs
- Use managed database service (AWS RDS, Cloud SQL)
- Configure proper logging and monitoring
- Set up CI/CD pipeline
- Configure backup strategies
