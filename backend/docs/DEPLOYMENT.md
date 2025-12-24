# ZimPrep Backend - Production Deployment Guide

## Quick Links
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

---

## Docker Deployment

### Build Production Image

```bash
# Build image
docker build -t zimprep-backend:latest -f Dockerfile.prod .

# Tag for registry
docker tag zimprep-backend:latest your-registry.com/zimprep-backend:latest

# Push to registry
docker push your-registry.com/zimprep-backend:latest
```

### Run with Docker Compose

```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale app=4
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Secrets created for sensitive data

### Create Secrets

```bash
# Create JWT secret
kubectl create secret generic zimprep-jwt \
  --from-literal=secret=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create OpenAI API key
kubectl create secret generic zimprep-openai \
  --from-literal=api-key=sk-your-key-here

# Create MongoDB connection string
kubectl create secret generic zimprep-mongodb \
  --from-literal=uri=mongodb://user:pass@mongo:27017/zimprep
```

### Deploy Application

```bash
# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n zimprep
kubectl get svc -n zimprep

# View logs
kubectl logs -f deployment/zimprep-backend -n zimprep
```

### Health Checks

Kubernetes will use:
- **Liveness Probe:** `GET /health` (ensures container is alive)
- **Readiness Probe:** `GET /readiness` (ensures app is ready for traffic)
- **Startup Probe:** `GET /health` (initial startup check)

---

## Environment Configuration

### Required Environment Variables

```bash
# Application
ENV=production
AUDIT_MODE=false

# Database
DATABASE_URL=postgresql://user:pass@db:5432/zimprep
MONGODB_URI=mongodb://user:pass@mongo:27017/zimprep?authSource=admin
REDIS_URL=redis://redis:6379/0

# Authentication
JWT_SECRET=<generate-with-secrets.token_urlsafe-32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# AI
OPENAI_API_KEY=sk-your-key
AI_TIMEOUT_SECONDS=30

# Observability
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_WINDOW_SECONDS=3600
```

### Generate Secure JWT Secret

```python
import secrets
print(secrets.token_urlsafe(32))
# Use this output for JWT_SECRET
```

---

## Monitoring Setup

### Prometheus Metrics

The `/metrics` endpoint exposes Prometheus-compatible metrics:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'zimprep-backend'
    static_configs:
      - targets: ['zimprep-backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard

Import the provided dashboard:
1. Go to Grafana → Dashboards → Import
2. Upload `monitoring/grafana-dashboard.json`
3. Select Prometheus data source
4. Save

### Alerts

Configure alerts for:
- High error rate (>5%)
- Response time >1s (p95)
- Health check failures
- High memory usage (>80%)
- DB connection failures

---

## Load Balancing

### Nginx Configuration

```nginx
upstream zimprep_backend {
    least_conn;
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
    server backend4:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.zimprep.com;

    location / {
        proxy_pass http://zimprep_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://zimprep_backend/health;
        access_log off;
    }
}
```

---

## Database Setup

### MongoDB Production Configuration

```javascript
// Create production user
use admin
db.createUser({
  user: "zimprep_prod",
  pwd: "<secure-password>",
  roles: [
    { role: "readWrite", db: "zimprep" },
    { role: "dbAdmin", db: "zimprep" }
  ]
})

// Enable authentication
// In mongod.conf:
security:
  authorization: enabled

// Create indexes for performance
use zimprep
db.exam_results.createIndex({ trace_id: 1 }, { unique: true })
db.exam_results.createIndex({ user_id: 1 })
db.audit_events.createIndex({ trace_id: 1 })
db.audit_events.createIndex({ timestamp: 1 })
```

### Backup Schedule

```bash
# Daily backup script
0 2 * * * mongodump --uri="mongodb://..." --out=/backups/$(date +\%Y\%m\%d)

# Retention: Keep 30 days
find /backups/* -mtime +30 -exec rm -rf {} \;
```

---

## Troubleshooting

### Server Won't Start

**Check logs:**
```bash
docker logs zimprep-backend
kubectl logs deployment/zimprep-backend -n zimprep
```

**Common issues:**
1. Missing environment variables → Check config
2. MongoDB connection failed → Verify MONGODB_URI and network
3. Port already in use → Change port or stop conflicting service

### High Memory Usage

**Diagnosis:**
```bash
# Docker
docker stats zimprep-backend

# Kubernetes
kubectl top pods -n zimprep
```

**Solutions:**
1. Increase memory limit in deployment
2. Check for memory leaks (review logs)
3. Scale horizontally (add more pods)

### Slow Response Times

**Check metrics:**
```bash
curl http://localhost:8000/metrics | grep http_request_duration
```

**Solutions:**
1. Add database indexes
2. Enable Redis caching
3. Scale horizontally
4. Check AI API latency

### MongoDB Connection Issues

**Test connection:**
```bash
mongosh "$MONGODB_URI"
```

**Common fixes:**
1. Check firewall rules
2. Verify credentials
3. Check authSource in connection string
4. Ensure MongoDB is running

---

## Scaling Guidelines

### Horizontal Scaling

Recommended configuration:
- **Development:** 1-2 instances
- **Staging:** 2-4 instances
- **Production:** 4-8+ instances (based on load)

### Resource Requirements

**Per instance:**
- CPU: 1-2 cores
- Memory: 2-4 GB
- Disk: 10 GB (for logs)

**Database:**
- MongoDB: 4+ GB RAM, SSD storage
- Redis: 1-2 GB RAM
- PostgreSQL (if used): 4+ GB RAM

### Auto-scaling

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: zimprep-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: zimprep-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Security Checklist

Before production deployment:

- [ ] JWT_SECRET is strong and unique
- [ ] All secrets stored in secret manager (not env files)
- [ ] HTTPS/TLS enabled
- [ ] MongoDB authentication enabled
- [ ] Redis password set
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Security headers added (nginx/ingress)
- [ ] Audit mode tested
- [ ] Penetration testing completed

---

## Rollback Procedure

If issues occur after deployment:

```bash
# Kubernetes
kubectl rollout undo deployment/zimprep-backend -n zimprep

# Docker Compose
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Verify rollback
curl http://localhost:8000/health
```

---

## Support

For production issues:
1. Check logs first
2. Review monitoring dashboards
3. Consult troubleshooting guide
4. Check GitHub issues
5. Contact maintainers

**Emergency contacts:** [Add your team contacts here]
