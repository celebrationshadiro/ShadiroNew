# Shadiro – Advanced Local Event Services Marketplace
## Phase 3: Category-Specific Vendor Logic & Premium Features Edition

![Status](https://img.shields.io/badge/Phase-3-blue?style=flat-square)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)
![Frontend](https://img.shields.io/badge/Frontend-React-61DAFB?style=flat-square)
![Database](https://img.shields.io/badge/Database-MongoDB-green?style=flat-square)
![Deployment](https://img.shields.io/badge/Deployment-Docker-2496ED?style=flat-square)

---

## 🎯 Project Overview

**Shadiro** is a premium, AI-assisted marketplace platform connecting users with local event service vendors. Phase 3 introduces **category-specific vendor logic**, **smart emergency policies**, and **intelligent vendor recommendations**.

### Key Features
- 🏢 **9 Vendor Categories** with distinct booking flows and UI
- 🎬 **Category-Specific Services** (catering menu, DJ equipment, photo packages)
- 🚨 **Emergency Policy** with auto-replacement vendor suggestions
- 🤖 **AI Recommendations** for vendors and packages
- 💬 **Real-Time Chat** via Socket.IO
- 💳 **Razorpay Payments** integration
- 👨‍💼 **Admin Dashboard** with analytics and override controls
- 📱 **Mobile-Ready** React Native app (Expo)

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker & Docker Compose
- Node.js 16+ (for local development)
- Python 3.11+ (for backend development)

### Run with Docker
```bash
# 1. Clone and configure
git clone https://github.com/your-repo/shadiro.git
cd shadiro
cp .env.example .env

# 2. Start the stack
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python init_db.py

# 4. Access
# Frontend: http://localhost
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:socket_app --reload

# Frontend (new terminal)
cd frontend
npm install
npm start

# Mobile
cd mobile
npx expo start
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Complete setup, testing, troubleshooting |
| [PHASE3_CHECKLIST.md](PHASE3_CHECKLIST.md) | Feature matrix, status, implementation details |
| [PHASE3_Implementation_Summary.md](PHASE3_Implementation_Summary.md) | Session progress, deliverables, next steps |
| [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) | Phase 2 completion details |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
│  - VendorListPage, VendorDetailPage, BookingFlow        │
│  - AdminPanel, VendorDashboard, UserDashboard           │
│  - CategoryServiceSelector (dynamic per category)        │
│  - Emergency & Replacement Modals                        │
└─────────────┬───────────────────────────────────────────┘
              │ REST API + WebSocket
┌─────────────▼───────────────────────────────────────────┐
│                 Backend (FastAPI)                        │
├─────────────────────────────────────────────────────────┤
│ Routers:                                                 │
│  - /auth (login, register, JWT)                          │
│  - /vendors (CRUD, filtering)                            │
│  - /services (category-specific items)                   │
│  - /bookings (booking lifecycle + emergency)             │
│  - /quotes (quote management)                            │
│  - /admin (vendor approval, analytics, audit)            │
│  - /notifications (email/SMS)                            │
│  - /chat (Socket.IO for real-time)                       │
│                                                          │
│ Services:                                               │
│  - replacement_matcher: Smart vendor suggestions         │
│  - email_service: Resend integration                     │
│  - cloud_storage: Cloudinary/S3                          │
│  - auth: JWT token management                            │
├─────────────────────────────────────────────────────────┤
│ Models: User, Vendor, Booking, ServiceItem, Review, ... │
└─────────────┬───────────────────────────────────────────┘
              │ Motor/AsyncIO
┌─────────────▼───────────────────────────────────────────┐
│              Database (MongoDB)                          │
│  Collections:  users, vendors, bookings, services,       │
│                orders, payments, reviews, chats, ...     │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Vendor Categories (9 Types)

| Category | Services | Booking Model | UI Components |
|----------|----------|---------------|--------------|
| Event Venues | Capacity, AV setup, parking | Capacity + date | VenueSelector |
| Wedding Planners | Full planning, coordination | Full event | EventPlanner |
| Makeup Artists | Makeup, styling | Duration slots | ServiceGrid |
| Photographers | Photos, videos, albums | Duration + packages | **PackageSelector** ⭐ |
| Decorators | Themes, flowers, setup | Item + quantity | **ItemQuantityGrid** ⭐ |
| Caterers | Menu items, servings | Menu selection | **MenuSelector** ⭐ |
| DJs/Entertainers | Equipment, duration | Equipment checklist | **EquipmentChecklist** ⭐ |
| Transport | Vehicle type, duration | Vehicle + hours | VehicleSelector |
| Mehandi Designers | Designs, duration | Duration slots | ServiceGrid |

⭐ = Custom UI implemented in CategoryServiceSelector component

---

## 🎨 Phase 3 Features Implemented

### ✅ Completed This Session (Session 1 - Feb 9, 2026)

#### 1. Category-Specific Service Items
- Backend models: `ServiceItem`, `ServiceDefinition`
- API endpoints for CRUD operations
- Category templates with example items
- **Frontend Component**: `CategoryServiceSelector.js`
  - Renders 5 different layouts based on category
  - Supports quantity, checkboxes, single-choice packages
  - Real-time selection summary

#### 2. Emergency Cancellation UI
- Frontend modal: `EmergencyCancelModal.js`
- Vendor workflow: confirm → provide reason → submit
- Success feedback with replacement count
- **Backend Integration**: Already existed, UI now complete
  - Calls `/bookings/{id}/cancel-emergency`
  - Gets replacement suggestions from `replacement_matcher.py`

#### 3. Deployment Infrastructure
- `docker-compose.yml` with 3 services (frontend, backend, mongodb)
- Health checks on all services
- Environment variable configuration
- Quick start guide & troubleshooting

#### 4. Documentation
- QUICKSTART.md (setup, testing, troubleshooting)
- PHASE3_CHECKLIST.md (feature matrix)
- PHASE3_Implementation_Summary.md (session progress)

---

## 🔨 Next Steps (Phase 3 Continuation)

### Priority 1: Component Integration (1 hour)
```javascript
// 1. Integrate CategoryServiceSelector into BookingFlow
import { CategoryServiceSelector } from './CategoryServiceSelector';

// 2. Integrate EmergencyCancelModal into VendorDashboard
<EmergencyCancelModal booking={booking} isOpen={showModal} {...} />

// 3. Create ReplacementOfferModal for users
// Shows when vendor emergency cancels
<ReplacementOfferModal suggestions={replacementVendors} {...} />
```

### Priority 2: AI Recommendations (1-2 hours)
```python
# backend/services/recommendation_engine.py
async def recommend_vendors(event_type, city, budget, category):
    # Score vendors by:
    # - Category + location match
    # - Price range alignment
    # - Rating + review recency
    # - Availability
    # Return top 5-10 vendors
```

### Priority 3: Testing (1 hour)
- E2E test: Emergency cancellation flow
- Smoke tests: Service item CRUD
- Integration tests: Booking with category items

### Priority 4: CI/CD (1 hour)
- GitHub Actions workflow
- Docker image build & push
- Automated testing on PR

---

## 🛠️ Technology Stack

### Frontend
- **React 18** with hooks
- **React Router v6** for navigation (lazy-loaded routes)
- **TailwindCSS** for styling
- **Lucide Icons** for UI
- **Sonner** for toast notifications
- **Socket.IO Client** for real-time chat

### Backend
- **FastAPI** for REST API
- **Motor** (async MongoDB driver)
- **Socket.IO** for WebSocket
- **Pydantic** for data validation
- **JWT** for authentication
- **Razorpay SDK** for payments
- **Resend API** for emails

### Infrastructure
- **Docker & Docker Compose**
- **MongoDB 7** for database
- **Nginx** for frontend serving
- **uvicorn** for ASGI server

---

## 📁 Project Structure

```
shadiro/
├── backend/
│   ├── models.py              # Pydantic models
│   ├── auth.py                # JWT, hashing
│   ├── server.py              # FastAPI app
│   ├── routers/
│   │   ├── admin.py           # Admin endpoints
│   │   ├── bookings.py        # Booking lifecycle
│   │   ├── services.py        # Service items ⭐ NEW
│   │   ├── notifications.py   # Email/SMS
│   │   └── vendor_registration.py
│   ├── services/
│   │   ├── replacement_matcher.py  # Smart matching
│   │   ├── email_service.py        # Email templates
│   │   └── cloud_storage.py        # Cloudinary/S3
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CategoryServiceSelector.js ⭐ NEW
│   │   │   ├── EmergencyCancelModal.js   ⭐ NEW
│   │   │   └── ... (other UI components)
│   │   ├── pages/
│   │   │   ├── VendorDetailPage.js
│   │   │   ├── BookingFlow.js
│   │   │   ├── VendorDashboard.js
│   │   │   ├── AdminPanel.js
│   │   │   └── ... (more pages)
│   │   ├── lib/
│   │   │   ├── api.js               # API wrappers + servicesApi ⭐
│   │   │   ├── apiClient.js         # Central fetch client
│   │   │   └── utils.js
│   │   ├── styles/
│   │   │   ├── CategoryServiceSelector.css ⭐ NEW
│   │   │   ├── EmergencyCancelModal.css   ⭐ NEW
│   │   │   └── ... (component styles)
│   │   └── App.js                   # Main app (lazy-loaded routes)
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
│
├── mobile/
│   ├── src/
│   │   ├── screens/ (React Native Expo)
│   │   └── services/
│   └── app.json
│
├── tests/
│   ├── backend/
│   └── frontend/
│
├── docker-compose.yml          ⭐ NEW
├── .env.example                ⭐ NEW
├── QUICKSTART.md               ⭐ NEW
├── PHASE3_CHECKLIST.md         ⭐ UPDATED
├── PHASE3_Implementation_Summary.md ⭐ NEW
└── README.md
```

---

## 🔐 Security Features

- **JWT Authentication**: Secure token-based auth
- **Role-Based Access Control**: User, Vendor, Admin roles
- **Data Validation**: Pydantic model validation on all inputs
- **Audit Logging**: Admin actions tracked in AdminAuditLog
- **Emergency Verification**: Reason required + admin review
- **CORS Protection**: Configurable allowed origins

---

## 📊 Database Schema (Key Collections)

### Users
```javascript
{
  _id: ObjectId,
  id: UUID,
  email: String,        // unique
  name: String,
  role: "user" | "vendor" | "admin",
  hashed_password: String,
  phone: String,
  created_at: ISODate,
  is_active: Boolean
}
```

### Vendors
```javascript
{
  _id: ObjectId,
  id: UUID,
  user_id: UUID,       // foreign key
  business_name: String,
  category_id: UUID,   // foreign key (cat-caterer, cat-dj, etc.)
  city: String,
  status: "pending" | "approved" | "suspended" | "rejected",
  
  // Reliability metrics (Phase 3)
  acceptance_rate: Float,    // % of bookings accepted
  emergency_count: Integer,  // emergency cancellations
  completed_count: Integer,  // completed bookings
  
  created_at: ISODate,
  approved_at: ISODate
}
```

### ServiceDefinitions
```javascript
{
  _id: ObjectId,
  id: UUID,
  vendor_id: UUID,    // foreign key
  category_id: UUID,
  service_items: [
    {
      id: UUID,
      name: String,
      unit_price: Float,
      unit: "item" | "per_plate" | "per_hour" | "package",
      service_category: String,  // "appetizers", "equipment", etc.
      is_available: Boolean
    }
  ],
  created_at: ISODate,
  updated_at: ISODate
}
```

### Bookings
```javascript
{
  _id: ObjectId,
  id: UUID,
  user_id: UUID,       // foreign key
  vendor_id: UUID,     // foreign key
  event_id: UUID,      // optional
  
  // Category-specific items (Phase 3)
  items: [
    { id, name, qty, unit_price, total_price }
  ],
  
  // Emergency handling (Phase 3)
  emergency_reason: String,
  emergency_notified_admin: Boolean,
  replacement_vendor_id: UUID,      // if reassigned
  replacement_suggestions: [UUID],  // vendor IDs
  
  status: "pending" | "confirmed" | "in_progress" | "completed" | 
          "cancelled_by_user" | "cancelled_by_vendor" | 
          "cancelled_by_vendor_emergency",
  
  total_amount: Float,
  created_at: ISODate,
  updated_at: ISODate
}
```

---

## 🧪 Testing

### Backend API Tests
```bash
# In terminal
cd backend
pytest tests/ -v

# Smoke tests
python smoke_test_bookings.py
```

### Frontend Component Tests
```bash
cd frontend
npm test

# E2E tests (Cypress - if configured)
npm run cypress:open
```

---

## 📈 Performance Optimizations

✅ **Already Implemented:**
- React lazy-loading for routes
- Frontend Dockerfile with multi-stage build
- MongoDB query optimization with filters
- API response caching ready

🟡 **Recommended for Scale:**
- Redis caching layer for vendor recommendations
- Database indexing on frequently queried fields
- CDN for static assets
- API rate limiting
- Load balancing (nginx upstream)

---

## 🚀 Deployment

### Development
```bash
docker-compose -f docker-compose.yml up -d
```

### Production
```bash
# 1. Update .env with production values
MONGO_URL=mongodb+srv://...           # Atlas or managed DB
JWT_SECRET_KEY=<generate-secure>
RAZORPAY_KEY_ID=pk_live_...
RESEND_API_KEY=re_...

# 2. Build & push images
docker build -t myregistry/backend:latest backend/
docker push myregistry/backend:latest

# 3. Deploy to Kubernetes, ECS, or similar
kubectl apply -f k8s-manifest.yaml
```

### SSL/HTTPS
```bash
# Use Let's Encrypt with certbot
certbot certonly --standalone -d yourdomain.com

# Update nginx.conf with SSL certificates
```

---

## 🐛 Troubleshooting

**Q: MongoDB connection fails**  
A: Check `MONGO_URL` in .env, ensure MongoDB container is running:
```bash
docker-compose logs mongodb
```

**Q: Backend returns 401 Unauthorized**  
A: Verify JWT token in Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/auth/me
```

**Q: Frontend doesn't load category-specific selector**  
A: Check browser console for errors, verify vendor has service items:
```bash
curl http://localhost:8000/api/services/vendor/VENDOR_ID/items
```

**Q: Emergency cancellation not working**  
A: Check backend logs, ensure booking is confirmed first:
```bash
docker-compose logs backend | grep -i "emergency"
```

See [QUICKSTART.md](QUICKSTART.md) for more troubleshooting.

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/category-recommendations`
2. Commit changes: `git commit -am 'Add category-based recommendations'`
3. Push: `git push origin feature/category-recommendations`
4. Create Pull Request with description

---

## 📞 Support & Contact

- 📧 Email: support@shadiro.local
- 🐛 Issues: GitHub Issues
- 📖 Docs: See [QUICKSTART.md](QUICKSTART.md) & [PHASE3_CHECKLIST.md](PHASE3_CHECKLIST.md)

---

## 📄 License

Proprietary - Shadiro Platform © 2026

---

## 🎯 Roadmap

| Phase | Status | Features |
|-------|--------|----------|
| **Phase 1** | ✅ Done | Core auth, vendors, bookings |
| **Phase 2** | ✅ Done | Dashboards, chat, real-time |
| **Phase 3** | 🟡 In Progress | Category logic, emergency, recommendations |
| **Phase 4** | ⏳ Upcoming | Mobile app scale, AI personalization |
| **Phase 5** | ⏳ Upcoming | Analytics, B2B features, marketplace |

---

**Last Updated**: February 9, 2026  
**Current Version**: Phase 3 (Beta)  
**Maintainer**: Shadiro Dev Team

