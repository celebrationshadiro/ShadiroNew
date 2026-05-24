# Shadiro Production Deployment

## Runtime Targets

- Frontend: Render static site on `https://shadiro.com` and `https://www.shadiro.com`
- Backend: Render Docker web service on `https://api.shadiro.com`
- Database: MongoDB Atlas dedicated cluster or M10+ shared cluster for launch
- Cache/rate limiting: Render Key Value with internal URL assigned to `REDIS_URL`

## MongoDB Atlas

1. Create an Atlas project and cluster.
2. Create a database user with read/write permissions for the `shadiro` database.
3. Add Render outbound IPs to Atlas Network Access, or temporarily allow `0.0.0.0/0` only during initial validation.
4. Set `MONGO_URL` on Render:

```text
mongodb+srv://<db-user>:<password>@<cluster-host>/shadiro?retryWrites=true&w=majority
```

5. Keep `DB_NAME=shadiro`.
6. On first backend startup, the app creates production indexes for users, vendors, categories, packages, reviews, bookings, payments, refresh tokens, revoked tokens, and password reset tokens.

## Redis / Render Key Value

`render.yaml` provisions `shadiro-redis` as a Render Key Value instance and injects the internal connection string into `REDIS_URL`.

Use Redis for:

- Sliding-window rate limits
- Burst protection
- Shared limits across Render instances

The app falls back to in-memory limiting during local development if Redis is unavailable, but production should always set `REDIS_URL`.

## Render

1. Push the repository to GitHub.
2. In Render, create a Blueprint and select this repository.
3. Render reads `render.yaml`.
4. Provide secret values prompted by the Blueprint:
   - `MONGO_URL`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET`
5. Confirm `ALLOWED_ORIGINS` includes:
   - `https://shadiro.com`
   - `https://www.shadiro.com`
   - Localhost development origins
6. Deploy `shadiro-api`, `shadiro-web`, and `shadiro-redis`.
7. Verify:

```bash
curl https://api.shadiro.com/health
curl https://api.shadiro.com/health/ready
```

## Hostinger DNS

Configure DNS in Hostinger:

```text
Type   Name   Target
A      @      216.24.57.1
CNAME  www    shadiro-web.onrender.com
CNAME  api    shadiro-api.onrender.com
```

Then add these custom domains in Render:

- `shadiro.com` to the frontend static site
- `www.shadiro.com` to the frontend static site
- `api.shadiro.com` to the backend API service

Remove stale `AAAA` records while validating Render domains. Render provisions HTTPS certificates after DNS validates.

## Local Commands

```powershell
docker compose up --build
```

Backend only:

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend only:

```powershell
cd frontend
npm install
npm start
```

## Load Test

```bash
k6 run backend/loadtests/k6/auth_rate_limit.js
```
