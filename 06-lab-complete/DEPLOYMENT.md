# TravelBuddy Production Deployment Guide

## Overview

This guide covers deploying the TravelBuddy LangGraph Agent to production with Docker, Nginx, and Redis.

## Architecture

```
Client → Nginx (SSL/TLS) → FastAPI App → LLM (OpenAI/GitHub PAT)
                            ↓
                          Redis (Sessions)
```

## Prerequisites

- Docker & Docker Compose
- OpenAI API key (or GitHub PAT for Azure OpenAI)
- SSL certificates (self-signed or from CA)
- Minimum 2GB RAM, 2 CPU cores

## Quick Start (Local Docker)

### 1. Configure Environment

```bash
# Copy and edit production config
cp .env.production .env.local

# Edit with your values
nano .env.local
```

Required values:

- `OPENAI_API_KEY` or `GITHUB_PAT`
- `AGENT_API_KEY` (min 32 chars)
- `JWT_SECRET` (min 32 chars)

### 2. Generate Self-Signed SSL Certificate (Development Only)

```bash
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

### 3. Build and Run

```bash
# Build image
docker build -f Dockerfile.prod -t travelbuddy-agent:latest .

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

### 4. Verify Deployment

```bash
# Health check
curl -k https://localhost/health

# Ready check
curl -k https://localhost/ready

# API test
curl -k -X POST https://localhost/ask \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Xin chào"}'
```

## Testing

### Unit & Integration Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run integration tests
cd 06-lab-complete
pytest test_integration.py -v

# Run with coverage
pytest test_integration.py --cov=app
```

### Manual API Testing

```bash
# Start server in development
python -m uvicorn app.main:app --reload

# In another terminal
python test_manual.py
```

## Production Deployment

### AWS ECS

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [account].dkr.ecr.us-east-1.amazonaws.com
docker tag travelbuddy-agent:latest [account].dkr.ecr.us-east-1.amazonaws.com/travelbuddy-agent:latest
docker push [account].dkr.ecr.us-east-1.amazonaws.com/travelbuddy-agent:latest

# Deploy using ECS task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
aws ecs update-service --cluster travelbuddy --service travelbuddy-agent --force-new-deployment
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/your-project/travelbuddy-agent

# Deploy
gcloud run deploy travelbuddy-agent \
  --image gcr.io/your-project/travelbuddy-agent \
  --platform managed \
  --region us-central1 \
  --set-env-vars="OPENAI_API_KEY=sk-...,AGENT_API_KEY=...,JWT_SECRET=..."
```

### Railway / Render

1. Connect repository to Railway/Render
2. Set environment variables in dashboard
3. Deploy (automatic from main branch)

## Monitoring & Maintenance

### Logs

```bash
# View app logs
docker-compose -f docker-compose.prod.yml logs app

# Follow logs
docker-compose -f docker-compose.prod.yml logs -f app

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx
```

### Metrics

```bash
# Get usage metrics
curl -k -H "X-API-Key: your-api-key" https://localhost/metrics
```

### Backup Redis Data

```bash
# Backup
docker exec travelbuddy-redis redis-cli BGSAVE

# Copy backup
docker cp travelbuddy-redis:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

### Scale Horizontally

```bash
# Update docker-compose.yml to add more instances
# Then restart with:
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

## SSL Certificate Management

### Obtain From Let's Encrypt (Production)

```bash
# Using Certbot
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com

# Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

### Auto-Renewal

```bash
# Add to crontab
0 0 1 * * docker exec travelbuddy-nginx nginx -s reload
```

## Security Checklist

- [ ] Change `AGENT_API_KEY` to strong random value
- [ ] Change `JWT_SECRET` to strong random value
- [ ] Use real SSL certificate (not self-signed)
- [ ] Set `DEBUG=false` in production
- [ ] Configure `ALLOWED_ORIGINS` for CORS
- [ ] Set `DAILY_BUDGET_USD` limit per user
- [ ] Enable Redis authentication if exposed
- [ ] Use environment variables, not hardcoded secrets
- [ ] Regularly update dependencies
- [ ] Monitor API usage and costs

## Troubleshooting

### App won't start

```bash
# Check logs
docker-compose logs app

# Check environment variables
docker-compose exec app env | grep OPENAI
```

### Rate limiting not working

```bash
# Check rate limiter state
curl -H "X-API-Key: key" http://localhost:8000/metrics
```

### High memory usage

```bash
# Check Redis memory
docker exec travelbuddy-redis redis-cli INFO memory

# Clear old sessions
docker exec travelbuddy-redis redis-cli FLUSHALL
```

### SSL certificate issues

```bash
# Test certificate
openssl s_client -connect localhost:443

# Reload Nginx
docker exec travelbuddy-nginx nginx -s reload
```

## Performance Tuning

### Uvicorn Settings

```bash
# In docker-compose.yml, adjust workers:
CMD ["python", "-m", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", "8000",
     "--workers", "4"]  # Match CPU cores
```

### Nginx Tuning

```nginx
# In nginx.conf
worker_processes auto;  # Match CPU count
worker_connections 2048;  # Increase for high concurrency
```

### Redis Optimization

```bash
# Monitor Redis performance
docker exec travelbuddy-redis redis-cli --stat

# Adjust memory limit
docker run redis:7-alpine redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Test endpoint: `curl -k https://localhost/health`
3. Verify environment: `docker-compose config`
4. Check GitHub issues

## License

MIT License
