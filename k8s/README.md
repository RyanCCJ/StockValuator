# Kubernetes Deployment Guide

This guide helps you deploy StockValuator locally using Kubernetes. It is compatible with macOS, Linux, and Windows.

## Prerequisites

- **Kubernetes Cluster**: 
  - **Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) with **WSL2 backend** enabled.
  - **macOS**: [OrbStack](https://orbstack.dev/) (recommended) or Docker Desktop.
  - **Linux**: [Minikube](https://minikube.sigs.k8s.io/) or [Kind](https://kind.sigs.k8s.io/).
- **Tools**: `kubectl`, `docker`. (On Windows, it is recommended to run these inside a WSL2 terminal like Ubuntu).

## Step 1: Build Docker Images

```bash
# Build Backend
docker build -t stockvaluator-backend:latest ./backend

# Build Frontend
docker build -t stockvaluator-frontend:latest ./frontend
```

**Note for Minikube users**: Run `eval $(minikube docker-env)` (bash/zsh) before building so the images are available inside the Minikube node.

## Step 2: Configure Environment

1. **Secrets**: 
   Copy the template and fill in your private keys (Google OAuth, etc.).
   ```bash
   cp k8s/secrets-template.yaml k8s/secrets.yaml
   ```

2. **ConfigMap**:
   Decide your access mode and edit `k8s/configmap.yaml`.

   ### Option A: Local Mode (Standard)
   Use this for direct access via `localhost`.
   - `NEXTAUTH_URL`: `http://localhost:3500`
   - `CORS_ORIGINS`: `http://localhost:3500`

   ### Option B: Remote Mode (Tailscale Services)
   Use this for HTTPS and external access without port forwarding.
   - `NEXTAUTH_URL`: `https://stock-valuator.<your-tailnet>.ts.net`
   - `CORS_ORIGINS`: `https://stock-valuator.<your-tailnet>.ts.net`
   - **Setup**: Follow the [Tailscale Services Documentation](https://tailscale.com/docs/features/tailscale-services) to enable `svc:stock-valuator` in your Tailscale ACLs, then run:
     ```bash
     tailscale serve --service=svc:stock-valuator --bg 3500
     ```

## Step 3: Deploy to Cluster

```bash
# 1. Infrastructure (PostgreSQL & Redis)
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml

# 2. Configuration & Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# 3. Application (Deployments & Services)
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Step 4: Google OAuth Setup

Update your Google Cloud Console based on your chosen domain:
- **Authorized JavaScript origins**: `https://your-domain`
- **Authorized Redirect URI**: `https://your-domain/api/auth/callback/google`

## Accessing the App

- **OrbStack/Docker Desktop (macOS/Windows)**: Open [http://localhost:3500](http://localhost:3500).
- **Linux/Minikube**: Run `minikube service stockvaluator-frontend` to get the URL, or start `minikube tunnel` in a separate terminal to enable `LoadBalancer` access on `localhost`.
- **Tailscale**: Ensure your `tailscale serve` command is active, then open your `.ts.net` domain.

## Maintenance

### Database Migrations

```bash
# Find backend pod
kubectl get pods -l component=backend
# Run migration
kubectl exec -it <pod-name> -- uv run alembic upgrade head
```

### Cache Management

The `scripts/` directory is included in the backend Docker image. You can run maintenance scripts via `kubectl exec`:

```bash
# Clear all Redis cache
kubectl exec -it <pod-name> -- uv run python scripts/clear_redis_cache.py

# Clear specific Redis cache pattern
kubectl exec -it <pod-name> -- uv run python scripts/clear_redis_cache.py --pattern "financial_data:*"

# List available Redis cache patterns
kubectl exec -it <pod-name> -- uv run python scripts/clear_redis_cache.py --list

# Clear all DB cache tables (financial_data, ai_score_cache, etc.)
kubectl exec -it <pod-name> -- uv run python scripts/clear_db_cache.py

# Clear specific DB table
kubectl exec -it <pod-name> -- uv run python scripts/clear_db_cache.py --table financial_data

# List available DB cache tables
kubectl exec -it <pod-name> -- uv run python scripts/clear_db_cache.py --list
```
