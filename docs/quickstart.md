# Shadiro Phase 3 – Quick Start Guide

## 🚀 Getting Started (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- Git cloned locally
- .env file configured (see below)

### 1. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your values:
nano .env
```

**Essential Configs:**
```env
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your-secure-password
JWT_SECRET_KEY=your-secret-jwt-key
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
RESEND_API_KEY=your-resend-email-api-key
```

### 2. Build & Start the Stack

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### 3. Access the Application

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost | Web UI (React) |
| Backend API | http://localhost:8000 | REST API + WebSocket |
| MongoDB | localhost:27017 | Database |

### 4. Initialize Database (First Run)

```bash
# Run initialization script
docker-compose exec backend python init_db.py

# Verify categories loaded
curl http://localhost:8000/api/categories
```

---

## 📝 Phase 3 Features to Test

### A. Category-Specific Service Items

**Scenario: Vendor adds menu items (Catering category)**

1. **Login as vendor**
   - Navigate to: http://localhost/vendor-register
   - Create account in "Catering" category

2. **Add service items**
   ```bash
   # Get category template
   curl http://localhost:8000/api/services/category-template/caterer
   
   # Add multiple items from template
   curl -X POST http://localhost:8000/api/services/vendor/bulk-add-items \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '[
       {
         "vendor_id": "VENDOR_ID",
         "category_id": "caterer",
         "name": "Paneer Tikka",
         "unit_price": 250,
         "unit": "per_plate"
       }
     ]'
   ```

3. **View items in booking UI**
   - Navigate to vendor details
   - See category-specific item selector
   - Add items to cart with quantities

### B. Emergency Cancellation Flow

**Scenario: Vendor triggers emergency → User sees replacements → Admin reviews**

1. **Vendor emergency cancel**
   - VendorDashboard → Active Bookings
   - Click "Emergency Cancel" button
   - Provide reason (medical, equipment, legal)
   - Submit

2. **Backend processes**
   - Runs replacement_matcher.py
   - Finds 5-6 alternative vendors
   - Triggers email to customer
   - Updates vendor metrics (emergency_count++)

3. **User notification**
   - Receives email with replacement suggestions
   - ReplacementOfferModal shows alternatives
   - Can accept replacement or request refund

4. **Admin review**
   - AdminPanel → Emergency Cancellations
   - Can verify reason, override, or penalize

### C. AI Recommendations

**Test the recommendation engine** (Phase 3C):

```bash
# Get recommended vendors for an event
curl http://localhost:8000/api/vendor-recommendations \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  --data-urlencode "event_type=wedding" \
  --data-urlencode "city=Mumbai" \
  --data-urlencode "budget_max=100000"
```

---

## 🔧 Common Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (full reset)
docker-compose down -v

# Restart a specific service
docker-compose restart backend

# View detailed logs
docker-compose logs --tail=100 backend

# Execute command in container
docker-compose exec backend python -c "print('Hello')"

# Build without cache
docker-compose build --no-cache

# Scale replicas (for load balancing)
docker-compose up -d --scale backend=2
```

---

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# Verify credentials
docker-compose logs mongodb | grep -i "auth"

# Access MongoDB shell
docker-compose exec mongodb mongosh
```

### Backend API Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Verify service is healthy
curl http://localhost:8000/health

# Restart backend
docker-compose restart backend
```

### Frontend Not Loading
```bash
# Check nginx logs
docker-compose logs frontend

# Verify build completed
docker images | grep shadiro

# Rebuild frontend
docker-compose build --no-cache frontend
```

### Port Conflicts
```bash
# Change ports in docker-compose.yml
# Or kill processes using ports:
lsof -i :3000       # Find process on port 3000
kill -9 <PID>       # Kill that process
```

---

## 📊 Monitoring & Debugging

### Health Checks
All services have health checks. Monitor them:
```bash
docker-compose ps  # Shows health status
```

### Database Management
```bash
# Backup MongoDB
docker-compose exec mongodb mongodump --out /backup

# Restore MongoDB
docker-compose exec mongodb mongorestore /backup
```

### Performance Metrics
```bash
# Monitor resource usage
docker stats

# View container details
docker-compose exec backend df -h
```

---

## 🚢 Production Deployment

### Pre-Deployment Checklist
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure real Razorpay credentials
- [ ] Set up Resend API for emails
- [ ] Configure Cloudinary for media
- [ ] Update CORS_ORIGINS to production domains
- [ ] Enable DB backups
- [ ] Set up monitoring/alerting

### Deploy to Cloud (Example: AWS ECS)
```bash
# Push images to registry
docker tag shadiro-backend:latest myregistry/backend:latest
docker push myregistry/backend:latest

docker tag shadiro-frontend:latest myregistry/frontend:latest
docker push myregistry/frontend:latest

# Deploy using AWS ECS, Kubernetes, or similar
```

### SSL/HTTPS Setup
```bash
# Update nginx.conf to include SSL
# Or use Let's Encrypt with certbot
docker run --rm -it -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone -d yourdomain.com
```

---

## 🔗 Useful Links

- [docker-compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [React Production Build](https://create-react-app.dev/docs/deployment/)
- [MongoDB on Docker](https://hub.docker.com/_/mongo)
- [Nginx Configuration](https://nginx.org/en/docs/)

---

## 📝 Next Steps

1. **Phase 3C**: Implement AI recommendation engine
   - Create backend/services/recommendation_engine.py
   - Wire HomePage with "Recommended for You"
   - Add package suggestions in booking flow

2. **Phase 3D**: Testing & CI/CD
   - Write E2E tests for emergency flow
   - Set up GitHub Actions CI pipeline
   - Deploy to staging environment

3. **Phase 4**: Performance & Scale
   - Add caching layer (Redis)
   - Implement database indexing
   - Set up CDN for static assets
   - Load testing & optimization

---

**For issues or questions, check:**
- GitHub Issues
- API Documentation (http://localhost:8000/docs)
- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`

