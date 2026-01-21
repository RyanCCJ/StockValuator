# Zeabur Deployment Guide

## Step 1: Create Postgres and Redis

In Zeabur Dashboard → Marketplace, add the following services:

| Service | Description |
|---------|-------------|
| PostgreSQL | Database |
| Redis | Cache |

After creation, note down the connection information for each service.

---

## Step 2: Deploy Backend from GitHub

1. Click "Deploy from GitHub"
2. Select `RyanCCJ/StockValuator` → Choose `backend` folder
3. Set environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>` | Copy from Postgres service, must include `+asyncpg` |
| `REDIS_URL` | `redis://:<password>@<host>:<port>` | Copy from Redis service |
| `SECRET_KEY` | Random string | Generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | `https://<frontend-domain>.zeabur.app` | Must include https:// |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | From Google Cloud Console |
| `PORT` | `8080` | ⚠️ Zeabur defaults to 8080 |
| `GMAIL_REDIRECT_URI` | `https://<backend-domain>.zeabur.app/email/oauth/callback` | For Gmail OAuth |
| `GMAIL_REFRESH_TOKEN` | OAuth refresh token | Get from /email/oauth/authorize |
| `GMAIL_USER_EMAIL` | Your Gmail address | For sending price alerts |

4. Bind Domain (e.g., `stock-valuator-api`)

---

## Step 3: Deploy Frontend from GitHub

1. Click "Deploy from GitHub"
2. Select `RyanCCJ/StockValuator` → Choose `frontend` folder
3. Set environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `BACKEND_URL` | `https://<backend-domain>.zeabur.app` | Backend public URL |
| `NEXTAUTH_URL` | `https://<frontend-domain>.zeabur.app` | Frontend public URL |
| `AUTH_SECRET` | Random string (32+ chars) | Generate with `openssl rand -base64 32` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Same as Backend |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | Same as Backend |
| `AUTH_TRUST_HOST` | `true` | Required, otherwise UntrustedHost error |
| `NEXT_PUBLIC_BRANDFETCH_CLIENT_ID` | Brandfetch Client ID | Optional, for company logos |

4. Bind Domain (e.g., `stock-valuator`)

---

## Step 4: Deploy Celery Worker from GitHub

1. Click "Deploy from GitHub"
2. Select `RyanCCJ/StockValuator` → Choose `backend` folder
3. **Configure Docker**:
   - Go to Settings → **Docker**
   - Paste the content of `backend/Dockerfile.worker` into the Dockerfile field
4. Set environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | Same as Backend | `postgresql+asyncpg://...` from PostgreSQL service |
| `REDIS_URL` | Same as Backend | From Redis service |
| `SECRET_KEY` | Same as Backend | Same secret key |
| `GOOGLE_CLIENT_ID` | Same as Backend | For Gmail API |
| `GOOGLE_CLIENT_SECRET` | Same as Backend | For Gmail API |
| `GMAIL_REDIRECT_URI` | Same as Backend | OAuth callback URL |
| `GMAIL_REFRESH_TOKEN` | Same as Backend | OAuth refresh token |
| `GMAIL_USER_EMAIL` | Same as Backend | Email sender address |

> ⚠️ **No domain binding needed** - Celery Worker runs as a background process

---

## Step 5: Deploy Celery Beat from GitHub

1. Click "Deploy from GitHub"
2. Select `RyanCCJ/StockValuator` → Choose `backend` folder
3. **Configure Docker**:
   - Go to Settings → **Docker**
   - Paste the content of `backend/Dockerfile.beat` into the Dockerfile field
4. Set environment variables (same as Celery Worker):

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | Same as Backend | PostgreSQL connection string |
| `REDIS_URL` | Same as Backend | Redis connection string |
| `SECRET_KEY` | Same as Backend | Same secret key |

> ⚠️ **No domain binding needed** - Celery Beat runs as a scheduler process
> ⚠️ **Only deploy 1 replica** - Multiple Beat instances will cause duplicate task scheduling

---

## Important Notes

### ⚠️ DATABASE_URL Format
Must start with `postgresql+asyncpg://`, not `postgresql://`

### ⚠️ Backend Port
Zeabur defaults to 8080, set `PORT=8080` in environment variables

### ⚠️ Redeploy vs Restart
After modifying environment variables, you need to **Redeploy** (rebuild), not just Restart

---

## Google OAuth Setup

In [Google Cloud Console](https://console.cloud.google.com/), create an OAuth 2.0 Client:

1. Authorized JavaScript origins:
   - `https://<frontend-domain>.zeabur.app`

2. Authorized redirect URIs:
   - `https://<frontend-domain>.zeabur.app/api/auth/callback/google`

---

## Generate Secrets

```bash
# SECRET_KEY (Backend)
openssl rand -hex 32

# AUTH_SECRET (Frontend)
openssl rand -base64 32
```

