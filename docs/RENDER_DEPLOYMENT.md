# Render Deployment Guide

## Overview

This application consists of:
1. **PostgreSQL Database** - Main data store
2. **Redis** - Task queue for ARQ
3. **FastAPI Backend** - Main API server
4. **ARQ Worker** - Background task processor
5. **Next.js Admin Frontend** - Admin dashboard

## Prerequisites

1. Render account: https://render.com
2. AWS account with S3 bucket created
3. OpenAI API key

## Deployment Steps

### 1. Connect GitHub Repository

1. Go to Render Dashboard
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Select the `render.yaml` file

### 2. Set Environment Variables

After the services are created, you need to set these **secret** environment variables in the Render dashboard:

#### Backend Service (`lantern-room-backend`)
Navigate to the service → Environment tab → Add:

- `OPENAI_API_KEY` - Your OpenAI API key
- `S3_ACCESS_KEY_ID` - Your AWS access key ID
- `S3_SECRET_ACCESS_KEY` - Your AWS secret access key

#### Worker Service (`lantern-room-worker`)
Same as backend (needs access to OpenAI and S3):

- `OPENAI_API_KEY` - Your OpenAI API key
- `S3_ACCESS_KEY_ID` - Your AWS access key ID
- `S3_SECRET_ACCESS_KEY` - Your AWS secret access key

### 3. Create S3 Bucket

1. Go to AWS S3 Console
2. Create a bucket named `lantern-room-storage` (or update the `OBJECT_STORE_BUCKET` value in `render.yaml`)
3. Configure CORS for the bucket:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

4. Create an IAM user with S3 access and get the access keys

### 4. Verify Services

Once deployed, check:

1. **Database**: Should show "Available"
2. **Redis**: Should show "Available"
3. **Backend**: Visit `https://lantern-room-backend.onrender.com/health` - should return healthy status
4. **Worker**: Check logs for "✅ ARQ Worker started successfully"
5. **Admin**: Visit `https://lantern-room-admin.onrender.com/` - should load the admin dashboard

## Service Dependencies

```
┌─────────────┐
│  PostgreSQL │
└──────┬──────┘
       │
       ├─────────┐
       │         │
┌──────▼──────┐  │  ┌─────────┐
│   Backend   │  └─▶│ Worker  │
│  (FastAPI)  │     │  (ARQ)  │
└──────┬──────┘     └────┬────┘
       │                 │
       │            ┌────▼────┐
       │            │  Redis  │
       │            └─────────┘
       │
┌──────▼──────┐
│    Admin    │
│  (Next.js)  │
└─────────────┘
```

## Configuration Details

### Backend Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `DATABASE_URL` | Auto (from DB) | PostgreSQL connection string |
| `REDIS_URL` | Auto (from Redis) | Redis connection string |
| `OPENAI_API_KEY` | Manual (secret) | OpenAI API key |
| `OPENAI_MODEL` | Auto | Model to use (gpt-4o) |
| `S3_REGION` | Auto | AWS region (us-west-1) |
| `S3_ACCESS_KEY_ID` | Manual (secret) | AWS access key |
| `S3_SECRET_ACCESS_KEY` | Manual (secret) | AWS secret key |
| `OBJECT_STORE_BUCKET` | Auto | S3 bucket name |
| `TASK_QUEUE_REGISTRATIONS` | Auto | Modules to register with ARQ |
| `DEBUG` | Auto | Debug mode (false) |
| `LOG_LEVEL` | Auto | Logging level (INFO) |

### Admin Frontend Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `BACKEND_URL` | Auto (from backend) | Backend service URL |
| `NODE_ENV` | Auto | Node environment (production) |
| `NODE_VERSION` | Auto | Node version (23.1.0) |

### Worker Environment Variables

Same as backend (needs DB, Redis, OpenAI, S3).

## Troubleshooting

### Backend fails to start

1. Check logs: `Logs` tab in Render dashboard
2. Verify `DATABASE_URL` is set (should be automatic)
3. Verify `REDIS_URL` is set (should be automatic)
4. Check that migrations ran: Look for "alembic upgrade head" in pre-deploy logs

### Worker fails to start

1. Check logs for startup errors
2. Verify Redis connection: Should see "✅ Connected to Redis"
3. Verify task registrations: Should see "📦 Registered task handler"

### Admin can't connect to backend

1. Check that `BACKEND_URL` is set correctly
2. Test backend health endpoint directly
3. Check browser console for CORS errors
4. Verify backend CORS settings allow requests from admin domain

### Database migrations fail

1. Check that PostgreSQL version is compatible (Render uses 15+)
2. Review migration files in `backend/alembic/versions/`
3. Try manually running: `alembic upgrade head` in Render shell

### S3 uploads fail

1. Verify S3 credentials are correct
2. Check S3 bucket CORS configuration
3. Verify bucket name matches `OBJECT_STORE_BUCKET`
4. Check IAM user permissions (needs s3:PutObject, s3:GetObject, s3:DeleteObject)

## Scaling Considerations

### Current Setup (Starter Plan)
- Good for: Development, testing, small-scale production
- Limitations: Limited CPU/RAM, single instance

### Production Scaling
Consider upgrading:

1. **Database**: Upgrade to Standard plan for better performance
2. **Redis**: Upgrade for more memory and connections
3. **Backend**: Upgrade to Standard for auto-scaling
4. **Worker**: Add more worker instances or upgrade plan
5. **Admin**: Usually starter plan is sufficient

### Worker Scaling

To add more worker instances:

```yaml
# In render.yaml
- type: worker
  name: lantern-room-worker
  numInstances: 3  # Add this line for multiple workers
```

Or use Render dashboard: Service Settings → Scaling → Increase instances

## Monitoring

### Health Checks

- Backend: `/health` endpoint (checked every 30s by Render)
- Worker: No HTTP endpoint (monitored via process health)
- Admin: Root path `/` (checked every 30s by Render)

### Logs

Access logs via:
1. Render Dashboard → Service → Logs tab
2. Or use Render CLI: `render logs <service-name>`

### Metrics

Monitor in Render Dashboard:
- CPU usage
- Memory usage
- Request rate
- Response times

## Cost Estimate (Starter Plans)

- PostgreSQL: $7/month
- Redis: $10/month
- Backend Web Service: $7/month
- Worker Service: $7/month
- Admin Web Service: $7/month

**Total: ~$38/month**

## Mobile App API URL

Once deployed, update the mobile app to use your production backend:

In `mobile/modules/infrastructure/public.ts`:

```typescript
const DEFAULT_HTTP_CONFIG: HttpClientConfig = {
  baseURL: __DEV__
    ? DEV_BASE_URL
    : 'https://lantern-room-backend.onrender.com',
  timeout: 30000,
  retryAttempts: 3,
};
```

See `mobile/EAS_DEPLOYMENT.md` for mobile deployment instructions.

## Resources

- [Render Documentation](https://render.com/docs)
- [Render Blueprint Spec](https://render.com/docs/blueprint-spec)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Redis on Render](https://render.com/docs/redis)
