# IncuEdit — Production Deployment Guide

This guide details how to deploy **IncuEdit** to cloud platforms (Render, Railway, Fly.io, or VPS) for a public live demo.

---

## 1. Application Architecture for Deployment

IncuEdit is packaged as a single deployable unit:
- **Backend:** FastAPI (Python 3.11+) asynchronous REST API.
- **Frontend:** Precompiled React 18 + TypeScript SPA served directly by FastAPI at `/app/` (with fallback studio at `/`).
- **Media Engine:** Static FFmpeg binaries (automatically provisioned via `static-ffmpeg` or container base).
- **Storage:** Local filesystem with persistent disk volume at `/app/data` (or S3/MinIO adapter).

---

## 2. Environment Variables

Configure these environment variables in your deployment dashboard or `.env`:

| Variable | Recommended Production Value | Description |
|---|---|---|
| `APP_ENV` | `production` | Enforces strict startup validation and secret checks. |
| `WEBHOOK_SECRET` | `generate-random-32-char-hex-string` | Cryptographically secure secret for HMAC-SHA256 callback signing. Must be >= 16 characters and non-default. |
| `PORT` | `8000` (or assigned `$PORT`) | Port on which FastAPI / Uvicorn binds. |
| `DATA_DIR` | `/app/data` | Path to persistent storage for video uploads and renders. |
| `MAX_UPLOAD_MB` | `500` | Maximum file upload size limit in megabytes. |
| `TRANSCRIPTION_PROVIDER` | `mock` (or `whisper`) | Speech-to-text adapter (`mock` for zero-cost default). |
| `DIARIZATION_PROVIDER` | `none` (or `pyannote`) | Speaker diarization provider. |
| `FFMPEG_BIN` | `ffmpeg` | Path or binary name for FFmpeg executable. |

> [!IMPORTANT]
> **Production Secret Requirement:**  
> When `APP_ENV=production`, IncuEdit validates `WEBHOOK_SECRET` at boot. Weak values (e.g. `secret`, `incuedit_secret_key_2026`) or placeholder strings containing `replace_me` are rejected with `ValueError` to prevent insecure deployments.  
> Generate a secure secret with:  
> `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 3. Deployment Options

### Option A: Render.com (Recommended — Free / Low Cost)

1. Create a free account at [render.com](https://render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository: `https://github.com/rvsr26/incubrix`.
4. Configure service settings:
   - **Root Directory:** `incuedit`
   - **Environment:** `Python 3` (or `Docker`)
   - **Build Command:**  
     ```bash
     pip install -r requirements.txt && cd frontend && npm ci && npm run build && cd ..
     ```
   - **Start Command:**  
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
5. Add a Persistent Disk:
   - Mount path: `/app/data`
   - Size: 1 GB
6. Set Environment Variables:
   - `APP_ENV` = `production`
   - `WEBHOOK_SECRET` = *(Paste your 64-character random hex token)*
   - `DATA_DIR` = `/app/data`
7. Click **Deploy**. Your live demo URL will be available at `https://<your-service>.onrender.com/app/`.

---

### Option B: Railway.app

1. Sign in to [railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select `rvsr26/incubrix`.
4. Under Settings:
   - **Root Directory:** `/incuedit`
   - **Custom Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a Volume:
   - Mount path: `/app/data`
6. Add Environment Variables (`APP_ENV`, `WEBHOOK_SECRET`, `DATA_DIR`).
7. Generate Domain and verify.

---

### Option C: Docker on Linux VPS (Ubuntu 22.04 / 24.04)

```bash
# 1. Clone repository
git clone https://github.com/rvsr26/incubrix.git
cd incubrix/incuedit

# 2. Configure production .env
cp .env.example .env
# Edit .env and set a random 64-character hex string for WEBHOOK_SECRET

# 3. Build and launch container
docker compose up -d --build

# 4. Verify running health
curl -f http://localhost:8000/api/v1/health
```

---

## 4. Verification After Deployment

Once deployed, verify the public endpoints:

1. **Health Check:**
   ```bash
   curl -f https://<your-app-domain>/api/v1/health
   # Expected: {"status":"ok","service":"incuedit"}
   ```
2. **React Studio UI:**
   Open in browser: `https://<your-app-domain>/app/`
3. **OpenAPI Interactive Documentation:**
   Open in browser: `https://<your-app-domain>/docs`
4. **End-to-End Render Test:**
   Upload a short MP4 video via the UI or API and execute a 2-second cut instruction to verify FFmpeg rendering on the deployed container.
