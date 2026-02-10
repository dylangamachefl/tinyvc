# Docker Deployment Guide

This guide explains how to run tinyvc using Docker for containerized deployment.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
FRED_API_KEY=your_fred_api_key
GEMINI_API_KEY=your_gemini_api_key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
RECIPIENT_EMAIL=your_email@gmail.com
```

### 2. Build and Run

**Run the pipeline once:**

```bash
docker-compose up tinyvc
```

**Run in detached mode:**

```bash
docker-compose up -d tinyvc
```

**View logs:**

```bash
docker-compose logs -f tinyvc
```

## Docker Commands

### Build Image

```bash
docker build -t tinyvc:latest .
```

### Run Pipeline Manually

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  tinyvc:latest
```

### Development Mode

Run with source code mounted for hot-reload:

```bash
docker-compose up tinyvc
```

All code changes are reflected immediately (no rebuild needed).

## Docker Compose Services

### Main Pipeline (`tinyvc`)

Runs the weekly pipeline with persistent data storage.

```bash
docker-compose up tinyvc
```

### Testing (`test`)

Run the test suite in an isolated container:

```bash
docker-compose --profile testing up test
```

### Interactive Shell (`shell`)

Debug or explore the environment interactively:

```bash
docker-compose --profile dev run --rm shell
```

Inside the shell:

```bash
# Run pipeline
python src/main.py

# Run analysis scripts
python scripts/analyze_performance.py

# Check data
ls data/
```

## Production Deployment

### Option 1: Docker Standalone

Build and run as a standalone container:

```bash
# Build
docker build -t tinyvc:1.0.0 .

# Run with cron (requires external scheduler)
docker run -d \
  --name tinyvc \
  --restart unless-stopped \
  --env-file .env \
  -v tinyvc-data:/app/data \
  tinyvc:1.0.0
```

### Option 2: Docker Compose with Scheduler

Use with an external cron or systemd timer:

```bash
# In crontab
0 8 * * 0 cd /path/to/tinyvc && docker-compose up tinyvc
```

### Option 3: Kubernetes (Advanced)

For Kubernetes deployment, create manifests:

```yaml
# k8s/deployment.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: tinyvc-pipeline
spec:
  schedule: "0 8 * * 0"  # Sunday 8 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: tinyvc
            image: tinyvc:1.0.0
            envFrom:
            - secretRef:
                name: tinyvc-secrets
            volumeMounts:
            - name: data
              mountPath: /app/data
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: tinyvc-data
          restartPolicy: OnFailure
```

## Volume Persistence

Data is persisted in the `./data` directory:

```
data/
├── raw/           # API responses
├── processed/     # Filtered opportunities
├── llm/           # LLM inputs/outputs
├── reports/       # Final reports
├── metadata/      # Run metadata
├── evaluations/   # Quality assessments
└── performance/   # Return tracking
```

## Security Best Practices

### Image Security

The Dockerfile follows security best practices:

- ✅ Multi-stage build (reduces image size)
- ✅ Non-root user (`tinyvc`)
- ✅ Minimal base image (`python:3.11-slim`)
- ✅ No secrets in image layers
- ✅ Health checks enabled

### Secret Management

**Never commit secrets to Git!**

Options for secret management:

1. **Local Development:** `.env` file (gitignored)
2. **Docker Secrets:** For Docker Swarm
3. **Environment Variables:** For cloud deployment
4. **Vault:** For enterprise (HashiCorp Vault, AWS Secrets Manager)

## Resource Limits

Limit container resources to prevent runaway processes:

```yaml
# docker-compose.yml
services:
  tinyvc:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Monitoring

View container health:

```bash
# Check status
docker ps

# View resource usage
docker stats tinyvc-pipeline

# Inspect container
docker inspect tinyvc-pipeline

# View logs
docker logs -f tinyvc-pipeline
```

## Troubleshooting

### Container exits immediately

Check logs:

```bash
docker-compose logs tinyvc
```

Common causes:
- Missing environment variables
- Invalid API keys
- Permission issues on mounted volumes

### Permission denied errors

Ensure data directory is writable:

```bash
chmod -R 755 data/
```

Or run with current user:

```bash
docker run --user $(id -u):$(id -g) ...
```

### Image build fails

Clear Docker cache:

```bash
docker builder prune
docker-compose build --no-cache
```

### Out of disk space

Clean up Docker resources:

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a
```

## Advantages Over Local Execution

| Benefit | Description |
|---------|-------------|
| **Reproducibility** | Identical environment across machines |
| **Isolation** | Dependencies don't conflict with host |
| **Portability** | Run anywhere Docker runs |
| **Easy Updates** | Rebuild image, restart container |
| **Resource Control** | Set memory/CPU limits |
| **Multi-env** | Dev/staging/prod with same image |

## Alternatives

If not using Docker, consider:

- **GitHub Actions** (recommended for this project)
- **Systemd timers** (Linux servers)
- **Windows Task Scheduler** (Windows servers)
- **Cloud Functions** (AWS Lambda, Google Cloud Functions)

## Further Reading

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose](https://docs.docker.com/compose/)
