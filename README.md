# Shadiro - Multi-Vendor Event Planning Platform

## Project Overview

Shadiro is a budget-driven event planning platform that connects users with verified event professionals and vendors. Built with web and mobile support.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT + Role-Based Access Control (User, Vendor, Admin)
- **Payment**: Razorpay (test keys configured)
- **API Architecture**: Modular service-oriented design

### Frontend (Web)
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS
- **Design System**: Shadcn/UI components
- **Fonts**: Playfair Display (headings) + DM Sans (body)
- **Theme**: Royal Celebration (Pink/Purple/Gold)
- **State Management**: React Context API
- **Routing**: React Router v7

### Mobile (Structure Provided)
- **Framework**: React Native (Expo)
- **Shared Backend**: Same FastAPI backend

## Features Implemented

### Core Functionality
✅ User Authentication (Register/Login with JWT)
✅ Role-Based Access Control (User/Vendor/Admin)
✅ 9 Vendor Categories (Venues, Planners, Makeup, Photography, Decor, Catering, Entertainment, Transport, Mehandi)
✅ Vendor Listing with Filters (category, city, price range, search)
✅ Vendor Detail Pages
✅ Budget-Based Vendor Matching
✅ Quote Request System
✅ Package Management (Silver/Gold/Platinum/Custom)
✅ Order Management
✅ Payment Integration (Razorpay)
✅ Review & Rating System
✅ Media Management with Reorderable Images

### Backend API Endpoints

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

#### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create category (Admin only)

#### Vendors
- `GET /api/vendors` - List vendors (with filters)
- `GET /api/vendors/{id}` - Get vendor details
- `POST /api/vendors` - Create vendor profile
- `PUT /api/vendors/{id}` - Update vendor
- `POST /api/vendors/{id}/media` - Add media
- `PUT /api/vendors/{id}/media/reorder` - Reorder media

#### Events
- `POST /api/events` - Create event
- `GET /api/events` - List user events
- `GET /api/events/{id}` - Get event details

#### Packages
- `GET /api/packages` - List packages (with filters)
- `GET /api/packages/{id}` - Get package details
- `POST /api/packages` - Create package

#### Quotes
- `POST /api/quotes` - Request quote
- `GET /api/quotes` - List quotes
- `PUT /api/quotes/{id}/respond` - Respond to quote

#### Orders
- `POST /api/orders` - Create order
- `GET /api/orders` - List orders
- `GET /api/orders/{id}` - Get order details

#### Payments
- `POST /api/payments/create-order` - Create Razorpay order
- `POST /api/payments/verify` - Verify payment

#### Reviews
- `POST /api/reviews` - Create review
- `GET /api/reviews` - List reviews

## Web Pages Implemented

1. **Home Page** (`/`) - Hero section with search, category grid, features
2. **Vendor Listing** (`/vendors`) - Filterable vendor grid
3. **Vendor Detail** (`/vendors/:id`) - Vendor info, packages, reviews
4. **Authentication** (`/auth`) - Login/Register forms

## Database Schema

### Collections
- `users` - User accounts with roles
- `vendors` - Vendor profiles
- `vendor_categories` - Service categories
- `events` - User events
- `packages` - Vendor packages
- `quotes` - Quote requests/responses
- `orders` - Bookings
- `payments` - Payment records
- `reviews` - Vendor reviews

## Environment Variables

### Backend (`/app/backend/.env`)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
CORS_ORIGINS=*
JWT_SECRET_KEY=shadiro-secret-key-change-in-production
RAZORPAY_KEY_ID=rzp_test_OvKz3xMbOJL3Np
RAZORPAY_KEY_SECRET=7Ff5WcFKQ3fkRRtjvapUKx0z
```

### Frontend (`/app/frontend/.env`)
```
REACT_APP_BACKEND_URL=[auto-configured]
```

## Setup & Run

### Initialize Database
```bash
cd /app/backend
python init_db.py
```

### Backend
```bash
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend (Web)
```bash
cd /app/frontend
yarn install
yarn start
```

## API Usage Examples

### Register User
```bash
curl -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "phone": "+91 9876543210",
    "role": "user"
  }'
```

### Login
```bash
curl -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

### List Vendors
```bash
curl "$API_URL/api/vendors?category_id=cat-venues&city=Mumbai&min_price=50000&max_price=200000"
```

## Design System

### Colors
- **Primary**: `#BE185D` (Festive Pink)
- **Secondary**: `#F59E0B` (Celebration Gold)
- **Accent**: `#8B5CF6` (Royal Purple)
- **Background**: `#FAFAF9` (Stone 50)

### Typography
- **Headings**: Playfair Display (serif)
- **Body**: DM Sans (sans-serif)

### Components
- Glass-morphism cards
- Rounded buttons with hover effects
- Smooth transitions
- Shadow elevation
- Responsive grid layouts

## Mobile App Structure

A basic React Native (Expo) project structure has been provided at `/app/mobile/` for future development. It will use the same backend API.

## Next Steps & Enhancements

### Phase 2 Features (Not Yet Implemented)
- [ ] Dashboard pages (User/Vendor/Admin)
- [ ] Quote request flow
- [ ] Package customization
- [ ] Booking checkout flow
- [ ] Payment integration UI
- [ ] Chat system
- [ ] Admin analytics
- [ ] Email notifications
- [ ] WhatsApp integration
- [ ] Mobile app complete implementation
- [ ] Image upload to cloud storage
- [ ] Advanced search & recommendations
- [ ] Vendor verification workflow

### Suggested Improvements
- Add real-time chat using WebSockets
- Implement push notifications
- Add calendar integration
- Build admin analytics dashboard
- Implement automated vendor matching algorithm
- Add multi-language support
- Implement progressive web app (PWA)
- Add vendor portfolio showcase
- Implement saved vendors/wishlists

## File Structure

```
/app/
├── backend/
│   ├── server.py          # Main FastAPI app
│   ├── models.py          # Pydantic models
│   ├── auth.py            # Authentication logic
│   ├── init_db.py         # Database initialization
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/       # Shadcn components
│   │   │   └── Navbar.js
│   │   ├── contexts/
│   │   │   └── AuthContext.js
│   │   ├── lib/
│   │   │   └── api.js     # API client
│   │   ├── pages/
│   │   │   ├── HomePage.js
│   │   │   ├── VendorListPage.js
│   │   │   ├── VendorDetailPage.js
│   │   │   └── AuthPage.js
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env
├── design_guidelines.json  # Design specifications
└── README.md
```

## Testing

The backend API is fully functional and can be tested with:
- API calls via curl or Postman
- Web UI testing via browser
- Database operations via MongoDB shell

## Security Notes

⚠️ **Important**: Current configuration is for development only
- Change JWT_SECRET_KEY in production
- Use production Razorpay keys
- Implement rate limiting
- Add input validation
- Enable HTTPS
- Implement CORS restrictions
- Add API authentication for sensitive endpoints

## License

Proprietary - Shadiro Platform

## Support

For issues or questions, refer to the project documentation or contact the development team.
