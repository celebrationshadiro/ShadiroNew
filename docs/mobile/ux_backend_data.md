# 📱 Shadiro Mobile-First UX & Backend Data Model
## React Native Design • API Contract • Real-time Features • Future Extensibility

---

## 📱 Mobile App Architecture (React Native + Expo)

### Why React Native?
```
Benefits:
✓ Code sharing: 70% logic shared with web
✓ Native performance: Smooth 60 FPS animations
✓ Offline-first: Works without internet (syncs later)
✓ Notifications: Push notifications, local alerts
✓ Hardware: Camera, GPS, haptics, contacts
✓ Distribution: App Store & Play Store

Stack:
├─ React Native 0.73+
├─ Expo SDK 50+
├─ React Navigation 6+ (routing)
├─ Redux or Zustand (state)
├─ SQLite (offline DB)
├─ Async Storage (preferences)
└─ Tailwind Native (NativeWind)
```

### App Structure

```
mobile/
├── src/
│   ├── screens/                 (React Navigation screens)
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── SignUpScreen.tsx
│   │   │   ├── OTPScreen.tsx
│   │   │   └── ProfileSetupScreen.tsx
│   │   ├── home/
│   │   │   ├── HomeTabScreen.tsx
│   │   │   ├── ExploreTabScreen.tsx
│   │   │   ├── WishlistTabScreen.tsx
│   │   │   ├── BookingsTabScreen.tsx
│   │   │   └── ProfileTabScreen.tsx
│   │   ├── discovery/
│   │   │   ├── VendorListingScreen.tsx
│   │   │   ├── VendorDetailScreen.tsx
│   │   │   ├── ComparisonScreen.tsx
│   │   │   └── FilterScreen.tsx
│   │   ├── booking/
│   │   │   ├── CheckoutScreen.tsx (4 steps)
│   │   │   ├── PaymentScreen.tsx
│   │   │   └─ ConfirmationScreen.tsx
│   │   ├── chat/
│   │   │   ├── ChatListScreen.tsx
│   │   │   └── ChatDetailScreen.tsx
│   │   ├── vendor/
│   │   │   ├── VendorDashboardScreen.tsx
│   │   │   ├── BookingsManagementScreen.tsx
│   │   │   ├── AvailabilityScreen.tsx
│   │   │   └ AnalyticsScreen.tsx
│   │   └── admin/
│   │       ├── AdminDashboardScreen.tsx
│   │       └── ModerationScreen.tsx
│   ├── components/              (Reusable components)
│   │   ├── shared/
│   │   ├── forms/
│   │   ├── lists/
│   │   └── modals/
│   ├── services/                (API clients, business logic)
│   │   ├── api.ts              (Axios instance)
│   │   ├── vendorService.ts
│   │   ├── bookingService.ts
│   │   ├── chatService.ts
│   │   ├── authService.ts
│   │   └── offlineSync.ts
│   ├── store/                   (State management)
│   │   ├── authSlice.ts
│   │   ├── bookingSlice.ts
│   │   ├── chatSlice.ts
│   │   └── store.ts
│   ├── utils/
│   │   ├── helpers.ts
│   │   ├── formatting.ts
│   │   └── validation.ts
│   └── styles/
│       ├── colors.ts            (Design system tokens)
│       ├── spacing.ts
│       └── typography.ts
├── app.json                     (Expo config)
├── eas.json                     (Expo Application Services)
└── metro.config.js              (Metro bundler config)
```

---

## 🎨 Mobile UI Patterns (React Native)

### Bottom Tab Navigation (Primary)

```tsx
// File: src/navigation/BottomTabNavigator.tsx

export default function BottomTabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: 'white',
          borderTopColor: '#E2E8F0',
          borderTopWidth: 1,
          height: 80,           // Includes safe area
          paddingBottom: 16,
          paddingTop: 8,
        },
        tabBarLabelStyle: { fontSize: 12 },
        tabBarActiveTintColor: '#2C5285',
        tabBarInactiveTintColor: '#A0AEC0',
      }}
    >
      <Tab.Screen 
        name="Home"
        component={HomeTabScreen}
        options={{
          tabBarIcon: ({ color }) => <Home color={color} size={24} />,
        }}
      />
      <Tab.Screen 
        name="Explore"
        component={ExploreTabScreen}
        options={{
          tabBarIcon: ({ color }) => <Search color={color} size={24} />,
        }}
      />
      <Tab.Screen 
        name="Wishlist"
        component={WishlistTabScreen}
        options={{
          tabBarIcon: ({ color }) => <Heart color={color} size={24} />,
          tabBarBadge: wishlistCount > 0 ? wishlistCount : null,
        }}
      />
      <Tab.Screen 
        name="Bookings"
        component={BookingsTabScreen}
        options={{
          tabBarIcon: ({ color }) => <Calendar color={color} size={24} />,
          tabBarBadge: pendingBookings > 0 ? pendingBookings : null,
        }}
      />
      <Tab.Screen 
        name="Profile"
        component={ProfileTabScreen}
        options={{
          tabBarIcon: ({ color }) => <User color={color} size={24} />,
        }}
      />
    </Tab.Navigator>
  )
}
```

### Screen-Level Safe Area Padding

```tsx
// File: src/components/SafeAreaView.tsx

import { useSafeAreaInsets } from 'react-native-safe-area-context'

export default function SafeScreen({ children }) {
  const insets = useSafeAreaInsets()
  
  return (
    <View style={{
      flex: 1,
      paddingTop: insets.top,
      paddingBottom: insets.bottom,
      paddingLeft: insets.left,
      paddingRight: insets.right,
    }}>
      {children}
    </View>
  )
}

// Usage: Wrap all screens
<SafeScreen>
  <ScrollView>
    {/* Content */}
  </ScrollView>
</SafeScreen>
```

### Modal/Bottom Sheet

```tsx
// File: src/components/BottomSheetModal.tsx

import {useBottomSheetModal} from '@gorhom/bottom-sheet'

export default function BottomSheetModal({
  title,
  children,
  onClose,
  snapPoints = [200, 500, 900]
}) {
  return (
    <BottomSheet
      snapPoints={snapPoints}
      handleIndicatorStyle={{ backgroundColor: '#2D3748' }}
      backgroundStyle={{ backgroundColor: 'white' }}
    >
      <View style={{ paddingHorizontal: 16, paddingTop: 8 }}>
        <View style={{
          height: 4,
          width: 40,
          backgroundColor: '#A0AEC0',
          borderRadius: 2,
          alignSelf: 'center',
          marginBottom: 16,
        }} />
        <Text style={{ fontSize: 20, fontWeight: '600', marginBottom: 16 }}>
          {title}
        </Text>
        {children}
      </View>
    </BottomSheet>
  )
}

// Usage:
<BottomSheetModal title="Filters" onClose={handleClose}>
  <FilterOptions />
</BottomSheetModal>
```

### Swipe Gestures

```tsx
// File: src/hooks/useSwipeGesture.tsx

import { useRef } from 'react'
import { PanResponder, Animated } from 'react-native'

export function useSwipeGesture(direction = 'vertical') {
  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderRelease: (evt, gestureState) => {
        const { dy, dx } = gestureState
        
        if (direction === 'vertical' && dy > 50) {
          // Swiped down
          onSwipeDown?.()
        }
        if (direction === 'horizontal' && dx > 50) {
          // Swiped right
          onSwipeRight?.()
        }
      },
    })
  ).current

  return panResponder.panHandlers
}

// Usage: Image carousel
<View {...useSwipeGesture('horizontal')}>
  <Image source={images[currentIndex]} />
</View>
```

### Haptic Feedback

```tsx
// File: src/utils/haptics.ts

import * as Haptics from 'expo-haptics'

export async function triggerHaptic(type: 'light' | 'medium' | 'heavy' | 'success') {
  switch (type) {
    case 'light':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)
      break
    case 'medium':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium)
      break
    case 'heavy':
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy)
      break
    case 'success':
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)
      break
  }
}

// Usage: Button click
<TouchableOpacity
  onPress={async () => {
    await triggerHaptic('medium')
    handleBooking()
  }}
>
  <Text>Book Now</Text>
</TouchableOpacity>
```

### Push Notifications

```tsx
// File: src/services/pushNotifications.ts

import * as Notifications from 'expo-notifications'
import * as Device from 'expo-device'

export async function registerForPushNotifications() {
  if (!Device.isDevice) {
    alert('Must use physical device for Push Notifications')
    return
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync()
  let finalStatus = existingStatus

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync()
    finalStatus = status
  }

  if (finalStatus !== 'granted') {
    alert('Failed to get push token for push notification!')
    return
  }

  const token = (await Notifications.getExpoPushTokenAsync()).data
  console.log('Push token:', token)  // Send to backend for storage
  
  return token
}

export function setupNotificationListeners() {
  // Handle notification when app is in foreground
  Notifications.setNotificationHandler({
    handleNotification: async (notification) => {
      return {
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }
    },
  })

  // Handle notification tap
  Notifications.addNotificationResponseReceivedListener((response) => {
    const { notification } = response
    const { data } = notification.request.content
    
    // Navigate to relevant screen
    if (data.type === 'booking_confirmed') {
      navigation.navigate('BookingDetail', { id: data.bookingId })
    } else if (data.type === 'vendor_message') {
      navigation.navigate('ChatDetail', { vendorId: data.vendorId })
    }
  })
}
```

---

## 🔌 Backend API Contract

### Core Data Models

#### 1. Vendor Entity

```typescript
interface Vendor {
  id: string
  userId: string
  name: string
  category: VendorCategory              // ENUM
  image: string                         // Profile image URL
  imageGallery: string[]                // Up to 20 images
  description: string
  specializations: string[]
  location: {
    city: string
    address: string
    coordinates: { lat: number; lng: number }
    serviceRadiusKm: number
  }
  
  pricing: {
    startingPrice: number
    priceUnit: 'flat' | 'per_plate' | 'per_hour'
    priceRange: { min: number; max: number }
    currency: 'INR'
  }
  
  packages: Package[]
  items: VendorItem[]
  
  verification: {
    status: 'pending' | 'approved' | 'suspended' | 'rejected'
    verifiedAt?: Date
    approvedByAdmin?: string
  }
  
  ratings: {
    averageRating: number              // 0-5, decimal
    totalReviews: number
    ratingBreakdown: {
      5: number
      4: number
      3: number
      2: number
      1: number
    }
  }
  
  metrics: {
    totalBookings: number
    completedBookings: number
    cancelledBookings: number
    emergencyCancellations: number
    acceptanceRate: number              // 0-100%
    averageResponseTimeMinutes: number
    isFeatured: boolean
  }
  
  availability: {
    scheduleType: 'calendar' | 'always_available'
    availableDates: Date[]
    unavailableDates: Date[]
    bufferDaysBetweenBookings: number
  }
  
  contact: {
    phone: string
    whatsapp: string
    email: string
    respondByEmail: boolean
    respondByPhone: boolean
    respondByWhatsApp: boolean
  }
  
  policies: {
    cancellationPolicy: string
    refundPolicy: string
    modificationPolicy: string
    advancePaymentRequired: number      // % of total amount
  }
  
  metadata: {
    experienceYears: number
    totalEventsHandled: number
    teamSize: number
    awards?: string[]
    certifications?: string[]
    createdAt: Date
    updatedAt: Date
  }
}

enum VendorCategory {
  VENUE = 'venue',
  WEDDING_PLANNER = 'wedding_planner',
  MAKEUP_ARTIST = 'makeup_artist',
  PHOTOGRAPHER = 'photographer',
  DECORATOR = 'decorator',
  CATERER = 'caterer',
  DJ = 'dj',
  TRANSPORT = 'transport',
  MEHANDI_DESIGNER = 'mehandi_designer',
}
```

#### 2. Package Entity

```typescript
interface Package {
  id: string
  vendorId: string
  name: string                         // 'Essential', 'Premium', 'Luxury'
  description: string
  price: number
  priceUnit: 'flat' | 'per_plate' | 'per_head'
  
  inclusions: {
    items: string[]                    // Item names/IDs included
    services: string[]                 // Services included
    duration?: number                  // Hours or days
    headCount?: string                 // "For 100+ guests"
  }
  
  addOns?: Array<{
    id: string
    name: string
    price: number
    unit: string
  }>
  
  customizable: boolean
  available: boolean
  displayOrder: number
  isRecommended: boolean               // Mark as "recommended"
  
  metrics: {
    totalBookings: number
    averageRating: number
  }
}
```

#### 3. VendorItem Entity

```typescript
interface VendorItem {
  id: string
  vendorId: string
  category: string                     // 'Non-Veg Curry', 'Decorations'
  name: string
  description?: string
  photo?: string
  price: number
  unit: 'per_plate' | 'per_piece' | 'per_hour' | 'per_set'
  inStock: boolean
  allergenInfo?: string[]              // ['gluten', 'dairy']
  
  metadata: {
    createdAt: Date
    updatedAt: Date
  }
}
```

#### 4. Booking Entity

```typescript
interface Booking {
  id: string
  userId: string
  vendorId: string
  originalBookingId?: string           // If this is a replacement booking
  
  eventDetails: {
    type: string                       // 'wedding', 'birthday', etc.
    date: Date
    time: string                       // "18:30"
    location: {
      address: string
      city: string
      coordinates: { lat: number; lng: number }
    }
    guestCount: number
    specialRequirements: string
  }
  
  service: {
    packageId: string
    packageName: string
    selectedItems: Array<{
      itemId: string
      name: string
      quantity: number
      price: number
    }>
    addOns: Array<{
      id: string
      name: string
      quantity: number
      price: number
    }>
  }
  
  pricing: {
    baseAmount: number
    tax: number
    platformFee: number
    discount?: number
    total: number
    currency: 'INR'
  }
  
  payment: {
    status: 'pending' | 'completed' | 'failed' | 'refunded'
    method: 'card' | 'upi' | 'wallet' | 'bank_transfer'
    transactionId?: string
    paidAt?: Date
    refundedAt?: Date
  }
  
  status: BookingStatus                // ENUM
  statusHistory: Array<{
    status: BookingStatus
    changedAt: Date
    changedBy: 'user' | 'vendor' | 'admin'
    reason?: string
  }>
  
  emergency?: {
    triggeredAt: Date
    reason: string
    vendorName: string
    suggestedReplacements: string[]    // Vendor IDs
    acceptedReplacementId?: string
    resolutionType?: 'replacement' | 'refund' | 'escalated'
    resolvedAt?: Date
    notes?: string
  }
  
  cancellation?: {
    cancelledAt: Date
    cancelledBy: 'user' | 'vendor' | 'admin'
    reason: string
    refundAmount: number
    refundStatus: 'pending' | 'processed' | 'failed'
  }
  
  communication: {
    messages: string[]                 // Message IDs
    lastMessage?: {
      text: string
      sentAt: Date
      sentBy: 'user' | 'vendor'
    }
  }
  
  review?: {
    rating: number                     // 1-5
    title: string
    text: string
    photos?: string[]
    submittedAt: Date
    vendorResponse?: {
      text: string
      respondedAt: Date
    }
  }
  
  auditLog: Array<{
    action: string
    performedBy: string
    timestamp: Date
    details: Record<string, any>
  }>
  
  createdAt: Date
  updatedAt: Date
}

enum BookingStatus {
  PENDING = 'pending',                      // Quote sent
  QUOTE_RECEIVED = 'quote_received',        // Vendor sent quote
  CONFIRMED = 'confirmed',                  // Payment completed
  VENDOR_ACCEPTED = 'vendor_accepted',      // Vendor accepted booking
  IN_PROGRESS = 'in_progress',              // Event happening
  COMPLETED = 'completed',                  // Event finished
  CANCELLED_BY_USER = 'cancelled_by_user',
  CANCELLED_BY_VENDOR = 'cancelled_by_vendor',
  CANCELLED_BY_VENDOR_EMERGENCY = 'cancelled_by_vendor_emergency',
  RESOLVED = 'resolved',                    // Emergency replacement accepted
  REFUNDED = 'refunded',                    // Refund processed
  ESCALATED = 'escalated',                  // Manual review needed
}
```

#### 5. Chat Entity

```typescript
interface ChatMessage {
  id: string
  bookingId: string
  vendorId: string
  userId: string
  
  type: 'text' | 'quote' | 'image' | 'file'
  
  content: {
    text?: string
    quote?: {
      packageId: string
      items: Array<{ name: string; price: number }>
      total: number
      validUntil: Date
    }
    mediaUrl?: string
  }
  
  metadata: {
    sentBy: 'user' | 'vendor'
    sentAt: Date
    readAt?: Date
    status: 'sent' | 'delivered' | 'read'
  }
}
```

#### 6. User Entity

```typescript
interface User {
  id: string
  phone: string
  email: string
  name: string
  profileImage?: string
  
  role: 'customer' | 'vendor' | 'admin'
  
  preferences: {
    eventType?: string
    budget?: { min: number; max: number }
    location?: string
    notifications: {
      push: boolean
      email: boolean
      sms: boolean
    }
    languagePreference: 'en' | 'hi'
  }
  
  wishlist: string[]                    // Vendor IDs
  savedFilters: SavedFilter[]
  
  pushToken?: string                    // For notifications
  
  metadata: {
    createdAt: Date
    lastLogin: Date
    accountStatus: 'active' | 'suspended' | 'deleted'
  }
}
```

---

## 🔌 API Endpoints (RESTful)

### Authentication Endpoints

```
POST   /api/auth/send-otp
       Body: { phone: "+91..." }
       Returns: { message: "OTP sent" }

POST   /api/auth/verify-otp
       Body: { phone, otp }
       Returns: { token, user }

POST   /api/auth/logout
       Headers: { Authorization: "Bearer token" }

POST   /api/auth/refresh-token
       Body: { refreshToken }
       Returns: { token }
```

### Vendor Endpoints

```
GET    /api/vendors
       Query: {
         category?, city?, lat?, lng?, radius?,
         minRating?, maxPrice?, verified?, featured?,
         sort?, page?, limit?
       }
       Returns: { vendors[], totalCount, pageInfo }

GET    /api/vendors/{id}
       Returns: { vendor (full detail) }

POST   /api/vendors                    (Create new - Auth required)
       Body: { category, name, ... }
       Returns: { vendorId }

PUT    /api/vendors/{id}               (Update - Vendor only)
       Body: { updated fields }
       Returns: { vendor }

GET    /api/vendors/{id}/reviews
       Query: { rating?, page?, limit?, sort }
       Returns: { reviews[], totalCount }

GET    /api/vendors/{id}/availability
       Query: { month?, year? }
       Returns: { calendar with available dates }

POST   /api/vendors/{id}/availability  (Set availability - Vendor only)
       Body: { availableDates, unavailableDates }
       Returns: { success }

GET    /api/vendors/{id}/analytics      (Vendor only)
       Query: { dateRange }
       Returns: { 
         totalEarnings, bookingCount, 
         averageRating, conversionRate,
         chartData
       }
```

### Booking Endpoints

```
POST   /api/bookings                   (Create quote request)
       Body: {
         vendorId, eventDate, guestCount,
         location, specialRequirements
       }
       Returns: { booking }

GET    /api/bookings                   (List user bookings)
       Query: { status?, page?, limit? }
       Returns: { bookings[] }

GET    /api/bookings/{id}
       Returns: { booking (full detail) }

PUT    /api/bookings/{id}/select-package
       Body: { packageId, selectedItems[], addOns[] }
       Returns: { booking with pricing }

POST   /api/bookings/{id}/checkout
       Body: { paymentMethod, promoCode? }
       Returns: { paymentUrl or { success: true } }

PUT    /api/bookings/{id}/confirm-payment
       Body: { transactionId }
       Returns: { booking }

PUT    /api/bookings/{id}/request-revision
       Body: { packageId, notes }
       Returns: { booking }

PUT    /api/bookings/{id}/cancel        (User cancels)
       Body: { reason }
       Returns: { booking, refund }

PUT    /api/bookings/{id}/vendor-cancel-emergency (Vendor emergency)
       Body: { reason }
       Returns: { booking (emergency status) }

GET    /api/bookings/{id}/emergency-replacements
       Returns: { suggestedVendors[] }

PUT    /api/bookings/{id}/accept-replacement
       Body: { replacementVendorId }
       Returns: { newBooking }

PUT    /api/bookings/{id}/approve-refund
       Returns: { booking (refunded) }
```

### Chat Endpoints

```
GET    /api/chats                      (List conversations)
       Query: { page?, limit? }
       Returns: { conversations[] }

GET    /api/chats/{bookingId}
       Returns: { messages[], vendor, booking }

POST   /api/chats/{bookingId}/message
       Body: { text or mediaUrl }
       Returns: { message }

POST   /api/chats/{bookingId}/quote-response
       Body: { packageId, approve/decline }
       Returns: { message }

GET    /api/chats/{bookingId}/is-typing (WebSocket)
       Returns: { vendorIsTyping: boolean }
```

### Review Endpoints

```
POST   /api/bookings/{id}/review
       Body: { rating, title, text, photos[] }
       Returns: { review }

PUT    /api/reviews/{id}               (Update review)
       Body: { rating, title, text }
       Returns: { review }

POST   /api/reviews/{id}/helpful      (Mark as helpful)
       Returns: { helpful count }

POST   /api/vendors/{id}/reply        (Vendor replies to review)
       Body: { reviewId, text }
       Returns: { review with reply }
```

### Admin Endpoints

```
GET    /api/admin/dashboard
       Returns: { 
         totalUsers, totalVendors, totalBookings,
         revenue, emergencies, chartsData
       }

GET    /api/admin/emergencies
       Query: { status?, page?, limit? }
       Returns: { emergencies[] }

PUT    /api/admin/bookings/{id}/approve-replacement
       Body: { replacementVendorId, notes }
       Returns: { booking }

PUT    /api/admin/bookings/{id}/refund
       Body: { reason, notes }
       Returns: { booking }

PUT    /api/admin/bookings/{id}/escalate
       Body: { reason, notes }
       Returns: { booking }

POST   /api/admin/vendors/{id}/verify
       Returns: { vendor (verified) }

POST   /api/admin/vendors/{id}/suspend
       Body: { reason }
       Returns: { vendor (suspended) }
```

---

## 🔄 Real-Time Features (WebSocket)

### Socket Events

```javascript
// Client emits
socket.emit('user:typing', { bookingId, isTyping })
socket.emit('chat:message', { bookingId, text })
socket.emit('booking:cancel-emergency-request', { bookingId, reason })

// Server broadcasts
socket.on('vendor:typing', (data) => {})
socket.on('chat:new-message', (data) => {})
socket.on('booking:emergency-cancelled', (data) => {})
socket.on('booking:replacement-suggested', (data) => {})
socket.on('quote:received', (data) => {})
```

---

## 💾 Offline-First Architecture

### SQLite Local Database

```typescript
// File: src/services/offlineDb.ts

import SQLite from 'expo-sqlite'

const db = await SQLite.openDatabaseAsync('shadiro.db')

// Tables to sync offline
const tables = {
  bookings: 'id, userId, vendorId, status, amount, createdAt',
  vendors: 'id, name, rating, image, category, location',
  chats: 'id, bookingId, senderId, text, timestamp',
  reviews: 'id, vendorId, rating, text',
}

export async function syncOfflineData() {
  const unsyncedBookings = await db.getAllAsync(
    'SELECT * FROM bookings WHERE synced = 0'
  )
  
  for (const booking of unsyncedBookings) {
    try {
      const response = await api.post('/bookings', booking)
      await db.runAsync(
        'UPDATE bookings SET synced = 1 WHERE id = ?',
        [booking.id]
      )
    } catch (error) {
      // Retry on next sync
    }
  }
}

// Sync when app comes online
import NetInfo from '@react-native-community/netinfo'

NetInfo.addEventListener(state => {
  if (state.isConnected && state.isInternetReachable) {
    syncOfflineData()
  }
})
```

---

## 🎯 Performance Metrics (Mobile Target)

```
Metric                          Target        Current
──────────────────────────────────────────────────────
Cold Start Time                 < 3s          TBD
Hot Start Time                  < 500ms       TBD
First Contentful Paint (FCP)    < 2s          TBD
Largest Contentful Paint (LCP)  < 3s          TBD
Interaction to Paint (INP)      < 200ms       TBD
Cumulative Layout Shift (CLS)   < 0.1         TBD
Bundle Size                     < 30MB        TBD
Memory Usage                    < 150MB       TBD
Scroll FPS                      60 FPS        TBD
Animation FPS                   60 FPS        TBD
Battery (1 hour usage)          < 10%         TBD
```

---

## 🚀 Deployment Strategy

### iOS (App Store)

```bash
# Build
eas build --platform ios --auto-submit

# Monitor build status
eas build:list

# Submit to App Store
eas submit --platform ios

# Track deployment
eas analytics:builds
```

### Android (Play Store)

```bash
# Build
eas build --platform android --auto-submit

# Generate Play Store signing key
eas credential pull --platform android

# Make sure service account email has Play Console access
```

---

## 📱 Device Configuration

### iPhone Sizes to Test
- iPhone 15 (6.1" - Standard)
- iPhone 15 Plus (6.7" - Larger)
- iPhone SE 3 (4.7" - Compact)

### Android Sizes to Test
- Samsung Galaxy S24 (6.2" - Standard)
- Samsung Galaxy Tab S10 (10.9" - Tablet)
- Google Pixel 9 Pro (6.3" - Standard)

### OS Versions
- iOS: 16.0+ (support last 2+ versions)
- Android: 10.0+ (API 29+)

---

## 🔐 Security Best Practices (Mobile)

```typescript
// Secure storage
import * as SecureStore from 'expo-secure-store'

export async function secureSetToken(token: string) {
  await SecureStore.setItemAsync('auth_token', token)
}

export async function secureGetToken(): Promise<string | null> {
  return await SecureStore.getItemAsync('auth_token')
}

// Certificate pinning
import { Cert } from 'react-native-cert-pinner'

Cert.allow('api.shadiro.app', {
  cert: CERT_PINNING_DATA,
})

// Biometric authentication
import BiometricAuth from 'react-native-biometric-auth'

export async function enableBiometricAuth() {
  const available = await BiometricAuth.isSensorAvailable()
  if (available) {
    await BiometricAuth.createBiometricSecret({
      authenticateOnBoot: true,
    })
  }
}
```

---

## 📊 Analytics (Mobile)

```typescript
// File: src/services/analytics.ts

import * as Analytics from 'expo-firebase-analytics'

export async function trackEvent(
  name: string,
  params?: Record<string, any>
) {
  await Analytics.logEvent(name, params)
}

// Usage
trackEvent('vendor_viewed', { vendorId, category })
trackEvent('booking_completed', { amount, vendorId, duration })
trackEvent('emergency_encountered', { vendorId, reason })
```

---

**Mobile UX & Backend Status**: 🟢 READY FOR DEVELOPMENT

**Total Components**: 40+  
**API Endpoints**: 50+  
**Real-time Features**: WebSocket enabled  
**Offline Support**: SQLite + sync  
**Target Platforms**: iOS 16+, Android 10+
