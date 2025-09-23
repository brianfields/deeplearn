# ARQ Worker Deployment Guide

This guide covers deploying and managing ARQ workers for background flow execution.

## Overview

ARQ workers are separate processes that execute background flows. They connect to the same database and Redis instance as your API server to process tasks from the queue.

## Prerequisites

- Redis server running and accessible
- PostgreSQL database running and accessible
- Same environment variables as API server
- Python dependencies installed (see requirements.txt)

## Starting Workers

### Development

Start a single worker for development:

```bash
cd backend
python scripts/start_worker.py
```

With custom options:

```bash
# Custom worker settings
python scripts/start_worker.py --max-jobs 5 --log-level DEBUG

# Different queue name
python scripts/start_worker.py --queue-name background --max-jobs 20

# Custom environment file
python scripts/start_worker.py --env-file .env.production
```

### Production

For production, run multiple worker processes for redundancy and throughput:

#### Using systemd (Linux)

Create `/etc/systemd/system/arq-worker@.service`:

```ini
[Unit]
Description=ARQ Worker %i
After=network.target redis.service postgresql.service

[Service]
Type=exec
User=your-app-user
Group=your-app-group
WorkingDirectory=/path/to/your/backend
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python scripts/start_worker.py --max-jobs 10
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Start multiple workers:

```bash
# Enable and start 3 worker instances
sudo systemctl enable arq-worker@1.service arq-worker@2.service arq-worker@3.service
sudo systemctl start arq-worker@1.service arq-worker@2.service arq-worker@3.service
```

#### Using supervisor

Install supervisor and create `/etc/supervisor/conf.d/arq-workers.conf`:

```ini
[program:arq-worker]
command=/path/to/your/venv/bin/python scripts/start_worker.py --max-jobs 10
directory=/path/to/your/backend
user=your-app-user
numprocs=3
numprocs_start=1
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=10
startretries=3
exitcodes=0,2
stopsignal=TERM
stopwaitsecs=600
killasgroup=false
priority=999
redirect_stderr=false
stdout_logfile=/var/log/arq-worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stdout_capture_maxbytes=1MB
stderr_logfile=/var/log/arq-worker-error.log
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
stderr_capture_maxbytes=1MB
```

Reload and start:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start arq-worker:*
```

#### Using Docker

Create a Dockerfile for workers:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "scripts/start_worker.py"]
```

Docker Compose configuration:

```yaml
version: '3.8'
services:
  api:
    # ... your API service configuration
    
  worker:
    build: .
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    
  postgres:
    image: postgres:15
    restart: unless-stopped
```

## Configuration

Workers use the same environment variables as your API server:

### Required Environment Variables

- `DATABASE_URL` or database connection components (`DATABASE_HOST`, `DATABASE_PORT`, etc.)
- `REDIS_URL` or Redis connection components (`REDIS_HOST`, `REDIS_PORT`, etc.)

### Optional Environment Variables

- `LOG_LEVEL`: Worker log level (DEBUG, INFO, WARNING, ERROR)
- `PROJECT_ROOT`: Path to project root (auto-detected if not set)

### Worker-Specific Options

Command-line options for `start_worker.py`:

- `--queue-name`: Queue name to process (default: "default")
- `--max-jobs`: Maximum concurrent jobs per worker (default: 10)
- `--job-timeout`: Job timeout in seconds (default: 3600)
- `--log-level`: Log level override
- `--env-file`: Custom .env file path (propagates to infrastructure.initialize)

## Monitoring

### Health Checks

Workers report their health to Redis. Monitor worker health via:

1. **Admin Interface**: Visit `/workers` in your admin interface
2. **API Endpoints**: Use `/api/v1/task_queue/workers` endpoint
3. **Redis Direct**: Check `arq:worker:*` keys in Redis

### Logs

Workers log important events:

- Task execution start/completion
- Errors and failures  
- Worker startup/shutdown
- Health status updates

Configure log aggregation to collect logs from all worker processes.

### Metrics

Key metrics to monitor:

- **Worker Count**: Number of active workers
- **Queue Length**: Number of pending tasks
- **Task Completion Rate**: Tasks completed per second
- **Task Failure Rate**: Percentage of failed tasks
- **Worker Health**: Last heartbeat from each worker

## Scaling

### Horizontal Scaling

Add more worker processes to handle increased load:

```bash
# Scale up with systemd
sudo systemctl start arq-worker@4.service arq-worker@5.service

# Scale with supervisor
sudo supervisorctl add arq-worker:arq-worker_04
sudo supervisorctl start arq-worker:arq-worker_04

# Scale with Docker
docker-compose up --scale worker=5
```

### Vertical Scaling

Adjust `--max-jobs` per worker based on:

- Available CPU cores
- Memory usage per job
- I/O characteristics of your flows

General guideline: Start with 1-2 jobs per CPU core.

## Troubleshooting

### Common Issues

**Workers not processing tasks:**
- Check Redis connection
- Verify queue name matches between API and workers
- Check worker logs for errors

**High memory usage:**
- Reduce `--max-jobs` per worker
- Check for memory leaks in flow code
- Monitor long-running tasks

**Tasks timing out:**
- Increase `--job-timeout`
- Optimize flow performance
- Break large flows into smaller steps

**Workers crashing:**
- Check database connection stability
- Monitor system resources
- Review flow error handling

### Debugging

Enable debug logging:

```bash
python scripts/start_worker.py --log-level DEBUG
```

Check Redis for task queue status:

```bash
# Connect to Redis CLI
redis-cli

# Check queue length
LLEN arq:queue:default

# Check worker heartbeats  
KEYS arq:worker:*
```

### Recovery

**Stuck tasks:**
Tasks that timeout are automatically retried once. For manual intervention:

1. Check task status in admin interface
2. Cancel stuck tasks if needed
3. Clear Redis queue if corrupted:
   ```bash
   redis-cli DEL arq:queue:default
   ```

**Worker recovery:**
Workers automatically reconnect on Redis/DB disconnection. For manual restart:

```bash
# Systemd
sudo systemctl restart arq-worker@*.service

# Supervisor  
sudo supervisorctl restart arq-worker:*

# Docker
docker-compose restart worker
```

## Security

- Use Redis AUTH if Redis is network-accessible
- Restrict database permissions for worker user
- Run workers with minimal system privileges
- Use SSL/TLS for Redis and PostgreSQL connections in production
- Isolate worker processes using containers or separate servers

## Performance Tuning

### Redis Configuration

For high throughput, tune Redis settings:

```
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 0
```

### Database Connection Pooling

Workers use connection pooling. Tune pool settings in environment:

```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_RECYCLE=3600
```

### Operating System

- Increase file descriptor limits
- Tune TCP settings for high connection count
- Monitor system resources (CPU, memory, disk I/O)