# Phase 3 Deployment Checklist

## 🚀 Pre-Deployment Phase

### Code Quality & Testing
- [ ] Run linter: `npm run lint` (frontend)
- [ ] Run tests: `pytest tests/` (backend)
- [ ] All tests pass: ✅ 0 failures
- [ ] No console errors in browser dev tools
- [ ] No TypeScript/ESLint warnings
- [ ] Code review completed

### Security Audit
- [ ] All API endpoints have auth checks
- [ ] Admin routes protected with role validation
- [ ] No sensitive data in client-side code
- [ ] No credentials in environment variables (use .env)
- [ ] CORS properly configured (production domain)
- [ ] SQL injection protection (N/A - using MongoDB)
- [ ] XSS prevention validated
- [ ] CSRF tokens implemented

### Environment Setup
- [ ] Create `.env` file (backend):
  ```
  DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/shadiro
  JWT_SECRET=your-very-secure-secret-key-min-32-chars
  SENDGRID_API_KEY=sg_xxxxx
  ENVIRONMENT=production
  CLOUDINARY_CLOUD_NAME=your_cloud_name
  CLOUDINARY_API_KEY=your_cloud_key
  CLOUDINARY_API_SECRET=your_cloud_secret
  ```
- [ ] Create `.env` file (frontend):
  ```
  REACT_APP_API_URL=https://api.shadiro.app
  REACT_APP_AUTH_DOMAIN=shadiro.auth0.com
  ```
- [ ] Verify environment variables are NOT in git repo
- [ ] `.gitignore` includes `.env` and `.env.local`

### Database Preparation
- [ ] MongoDB database created and running
- [ ] Indexes created for performance:
  - [ ] Bookings: `status`, `vendor_id`, `user_id`
  - [ ] Vendors: `category`, `city`, `status`
  - [ ] Events: `user_id`, `event_date`
- [ ] Database backup configured (daily)
- [ ] Test restore from backup works
- [ ] Initial data loaded (test categories, admin user)

### API Endpoints Verification
```bash
# Test critical endpoints (with valid auth token)
✅ GET /api/bookings/emergencies/list
✅ PUT /api/bookings/{id}/approve-replacement
✅ PUT /api/bookings/{id}/initiate-refund
✅ PUT /api/bookings/{id}/escalate
✅ GET /api/vendors/recommendations
✅ GET /api/bookings/{id}
✅ POST /api/bookings
```

---

## 🔧 Deployment Configuration

### Backend Deployment (FastAPI + Gunicorn)

**Step 1: Install Production Server**
```bash
pip install gunicorn uvicorn
```

**Step 2: Create Gunicorn Config** (`gunicorn.conf.py`)
```python
# workers = number of CPU cores * 2
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
max_requests = 1000
timeout = 30
```

**Step 3: Update Server Startup** (`server.py`)
```python
# For production, use Gunicorn instead of uvicorn.run()
# Command: gunicorn -c gunicorn.conf.py server:app
```

**Step 4: Docker Build** (optional)
```bash
# Dockerfile already exists at backend/Dockerfile
docker build -t shadiro-api:latest .
docker run -p 8000:8000 --env-file .env shadiro-api:latest
```

### Frontend Deployment (React + Nginx)

**Step 1: Build Production Bundle**
```bash
cd frontend
npm run build
# Creates optimized ./build folder
```

**Step 2: Configure Nginx** (nginx.conf exists)
```nginx
server {
    listen 80;
    server_name shadiro.app www.shadiro.app;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name shadiro.app www.shadiro.app;
    
    # SSL certificates
    ssl_certificate /etc/ssl/shadiro.crt;
    ssl_certificate_key /etc/ssl/shadiro.key;
    
    root /var/www/shadiro/build;
    index index.html;
    
    # React Router fallback
    location / {
        try_files $uri /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://api.shadiro.app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 3: Docker Build** (optional)
```bash
# Frontend Dockerfile exists
docker build -t shadiro-web:latest .
docker run -p 80:80 -p 443:443 shadiro-web:latest
```

### Using Docker Compose (Recommended)

**Step 1: Update `docker-compose.yml`**
```yaml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=production
    depends_on:
      - mongodb
  
  web:
    build: ./frontend
    ports:
      - "80:80"
      - "443:443"
    environment:
      - REACT_APP_API_URL=https://api.shadiro.app
    depends_on:
      - api
  
  mongodb:
    image: mongo:5.0
    volumes:
      - mongo_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${DB_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${DB_PASS}

volumes:
  mongo_data:
```

**Step 2: Deploy**
```bash
docker-compose up -d
# Monitor logs
docker-compose logs -f
```

---

## 🌐 Cloud Deployment Options

### Option A: AWS Deployment

**EC2 + RDS:**
1. Create EC2 instance (Ubuntu 20.04)
2. Install Docker, Docker Compose
3. Clone repository
4. Create `.env` file
5. `docker-compose up -d`

**Route 53:**
- Point `shadiro.app` → EC2 public IP
- Configure SSL certificate (free via ACM)

**RDS MongoDB** (if not self-hosted):
- Create MongoDB cluster
- Update `DATABASE_URL` in `.env`

### Option B: Heroku Deployment

**Backend:**
```bash
# Create Procfile
web: gunicorn server:app

# Deploy
heroku create shadiro-api
git push heroku main
```

**Frontend:**
```bash
# Install Heroku buildpack
heroku buildpacks:add heroku/nodejs
heroku env:set REACT_APP_API_URL=https://shadiro-api.herokuapp.com
git push heroku main
```

### Option C: Vercel + Firebase

**Frontend:** Deploy to Vercel
```bash
npm i -g vercel
vercel --prod
```

**Backend:** Firebase Cloud Functions
```bash
firebase deploy
```

---

## ✅ Post-Deployment Verification

### Health Checks
```bash
# API Health
curl -I https://api.shadiro.app/health
# Expected: 200 OK

# Frontend Health
curl -I https://shadiro.app
# Expected: 200 OK

# Database Connection
curl https://api.shadiro.app/api/health/db
# Expected: {"status": "connected"}
```

### Smoke Tests
```python
# Run smoke tests
pytest backend/smoke_test_bookings.py -v

# All 5 tests should pass:
✅ test_homepage_loads
✅ test_vendor_listing
✅ test_booking_flow
✅ test_emergency_cancellation
✅ test_admin_dashboard
```

### Performance Monitoring
- [ ] Setup APM (Application Performance Monitoring)
- [ ] Configure error tracking (Sentry)
- [ ] Setup uptime monitoring (StatusPage.io)
- [ ] Configure log aggregation (ELK Stack)

### User Testing
- [ ] 5 test users: Complete full booking flow
- [ ] Check all 8 features work end-to-end
- [ ] Verify mobile experience
- [ ] Test emergency cancellation workflow
- [ ] Validate email notifications

---

## 📊 Monitoring & Maintenance

### Daily Checks (Automated)
```python
# Cron job every 6 hours
- Check API uptime
- Verify database connectivity
- Monitor error rates (< 0.1%)
- Check log aggregation
```

### Weekly Reviews
- [ ] User feedback review
- [ ] Performance metrics
- [ ] Security logs
- [ ] Database size
- [ ] Backup verification

### Monthly Maintenance
- [ ] Update dependencies
- [ ] Review error logs
- [ ] Optimize slow queries
- [ ] Capacity planning
- [ ] Security audit

### Monitoring Tools Setup
```javascript
// Frontend (Sentry)
import * as Sentry from "@sentry/react";
Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: "production"
});

// Backend (APM)
from elasticapm.contrib.starlette import make_apm_client
apm_client = make_apm_client({
  'SERVICE_NAME': 'shadiro-api',
  'SERVER_URL': 'https://apm.shadiro.app'
})
```

---

## 🔒 Security Hardening

### SSL/TLS Configuration
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] SSL certificate valid and not self-signed
- [ ] Certificate auto-renewal configured (Let's Encrypt)
- [ ] TLS 1.2+ only
- [ ] HSTS header enabled (`max-age=31536000`)

### API Security
- [ ] Rate limiting enabled:
  - [ ] 100 requests/min per IP (general)
  - [ ] 5 requests/min per IP (login endpoint)
- [ ] API key rotation scheduled
- [ ] JWT token expiry: 24 hours
- [ ] Refresh tokens: 30 days
- [ ] CORS whitelist configured

### Data Protection
- [ ] Passwords hashed: bcrypt (10+ rounds)
- [ ] Sensitive data encrypted at rest
- [ ] PII not logged
- [ ] Database backups encrypted
- [ ] Secrets manager integrated (AWS Secrets, HashiCorp Vault)

### Compliance
- [ ] GDPR compliance verified
- [ ] User data retention policy set (90 days for deleted users)
- [ ] Privacy policy updated
- [ ] Terms of Service updated
- [ ] Cookie consent implemented

---

## 📱 Mobile App Deployment (If Applicable)

### iOS (TestFlight)
```bash
cd mobile
eas build --platform ios
eas submit --platform ios
```

### Android (Google Play)
```bash
eas build --platform android
eas submit --platform android
```

---

## 🎯 Launch Checklist

### 48 Hours Before Launch
- [ ] Final security audit
- [ ] Load testing (1000+ concurrent users)
- [ ] Database backup verified
- [ ] On-call team assigned
- [ ] Support documentation ready
- [ ] Customer support scripts prepared

### 24 Hours Before Launch
- [ ] Code freeze - no new commits
- [ ] Final testing round (all 8 features)
- [ ] Monitoring alerts configured
- [ ] Incident response plan ready
- [ ] Communication channels active

### Launch Day (T-0 to T+2 hours)
```
T-1 hour:
  - Notify stakeholders
  - Final system checks
  - Team on standby
  
T+0 min:
  - DNS switchover (if applicable)
  - Monitor error rates
  - Check user signups
  
T+30 min:
  - Review first 100 bookings
  - Check emergency flows
  - Verify notifications
  
T+1 hour:
  - User feedback collection
  - Performance baseline
  - All systems operational alert
  
T+2 hours:
  - Close incident response mode
  - Schedule retrospective
  - Document learnings
```

### Post-Launch (Days 1-7)
- [ ] Monitor error rates daily
- [ ] Check user adoption metrics
- [ ] Review customer feedback
- [ ] Performance trending
- [ ] Security scanning
- [ ] Fix critical bugs within 24 hours

---

## 📞 Rollback Plan

**If critical issue found within 2 hours of launch:**

**Option 1: Quick Patch**
```bash
# Fix bug
git commit -m "fix: critical issue"
git push origin main

# Rebuild and redeploy
docker-compose up -d --build
```

**Option 2: Rollback to Previous Version**
```bash
# Revert to previous version
git revert HEAD
docker pull shadiro-api:v2.0
docker-compose up -d

# Notify users
Email support: "Experiencing issues, reverted to stable version"
```

**Option 3: Database Rollback**
```bash
# Restore from backup (if data corruption)
mongorestore --uri "mongodb+srv://..." dump/
```

---

## 📈 Success Metrics (First 30 Days)

### Technical Metrics
- **Uptime**: ≥ 99.5%
- **Error Rate**: < 0.1%
- **API Response Time**: < 500ms (p95)
- **Page Load Time**: < 3s

### Business Metrics
- **User Signups**: 500+ new users
- **Booking Completion**: 70%+
- **Emergency Resolution**: < 30 min avg
- **Customer Satisfaction**: 4.5+ rating

### Adoption Metrics
- **Planner Mode Usage**: 40%+
- **Vendor Comparison**: 50%+ of users
- **Event Timeline**: 60%+ views
- **Feature Discovery**: 80%+ feature awareness

---

## 📋 Post-Launch Documentation

### Keep Updated
- [ ] Architecture Diagram (current deployment)
- [ ] Runbook for common issues
- [ ] Database schema documentation
- [ ] API changelog log
- [ ] Security incident log
- [ ] Customer support FAQ

### Training Materials
- [ ] Admin user guide
- [ ] Vendor onboarding guide
- [ ] Customer support scripts
- [ ] Emergency response procedures
- [ ] Video tutorials (for major features)

---

## 🎓 Team Handoff

### Before Handing to Operations
- [ ] All systems documented
- [ ] Deployment playbook created
- [ ] Monitoring configured
- [ ] On-call rotation established
- [ ] Escalation procedures defined
- [ ] Communication channels set up

### Operations Team Tasks
- [ ] Monitor logs 24/7
- [ ] Respond to user issues < 1 hour
- [ ] Track SLA metrics
- [ ] Schedule maintenance windows
- [ ] Manage database backups
- [ ] Report weekly metrics

---

## 📞 Support Contacts

### Deployment Issues
- **DevOps Lead**: [Name] - [Email]
- **Database Admin**: [Name] - [Email]
- **Security**: [Name] - [Email]

### Emergency Escalation
1. Notify [Team Lead]
2. Page [CTO] if P1 issue
3. Conference call: [Slack Channel]

---

**Deployment Status**: 🟢 READY FOR LAUNCH

**Last Updated**: February 9, 2026  
**Next Review**: 30 days post-launch
