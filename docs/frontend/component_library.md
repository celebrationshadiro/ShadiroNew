# Shadiro Component Library - React Implementation Guide

## Overview
This document provides detailed React component specifications for implementing the Shadiro design system.

---

## Table of Contents
1. [Button Components](#button-components)
2. [Card Components](#card-components)
3. [Form Components](#form-components)
4. [Layout Components](#layout-components)
5. [Navigation Components](#navigation-components)
6. [Data Display Components](#data-display-components)
7. [Modal & Overlay Components](#modal-components)
8. [Chat Components](#chat-components)
9. [Vendor-Specific Components](#vendor-specific)
10. [Admin Components](#admin-components)

---

## Button Components

### Primary Button
```jsx
// Usage
<Button variant="primary" size="md">
  Book Now
</Button>

// Props
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline' | 'icon';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  fullWidth?: boolean;
}

// Default Styles
.button-primary {
  background: #BE185D;
  color: white;
  padding: 12px 24px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 250ms ease-out;
}

.button-primary:hover:not(:disabled) {
  background: #9D174D;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.button-primary:active:not(:disabled) {
  background: #831843;
  transform: translateY(0);
}

.button-primary:disabled {
  background: #9CA3AF;
  opacity: 0.6;
  cursor: not-allowed;
}
```

### Button with Loading State
```jsx
<Button loading={isSubmitting}>
  {isSubmitting ? 'Confirming...' : 'Confirm Booking'}
</Button>

// Animated loading indicator (spinner)
// Replace text with spinner during loading
// Spinner color: match button variant
```

### Icon Button
```jsx
<Button variant="icon" size="md">
  <HeartIcon />
</Button>

// Icon button should have:
// - Circular shape (width = height)
// - Transparent background
// - Hover background: light shade
// - No text, only icon
```

---

## Card Components

### Vendor Preview Card
```jsx
<VendorCard
  image={vendorImage}
  name="Rahul's Catering"
  rating={4.8}
  reviewCount={234}
  priceStart={2000}
  priceEnd={5000}
  distance={3}
  isAvailable={true}
  onBookClick={() => navigate('/vendor/{id}/booking')}
  onQuoteClick={() => navigate('/vendor/{id}/quote')}
/>

// Component Structure
<div className="vendor-card">
  <img className="vendor-image" src={image} alt={name} />
  
  {isVerified && <Badge className="verified-badge">✓ Verified</Badge>}
  
  <div className="card-content">
    <h3 className="vendor-name">{name}</h3>
    
    <div className="rating-section">
      <StarRating rating={rating} />
      <span className="review-count">({reviewCount} reviews)</span>
    </div>
    
    <div className="meta">
      <span>{distance}km away</span>
      <span className="availability">
        {isAvailable ? '✅ Available' : '❌ Unavailable'}
      </span>
    </div>
    
    <div className="price-range">
      Est. ₹{priceStart} - ₹{priceEnd}
    </div>
    
    <CategoryChips categories={categories} />
    
    <div className="button-group">
      <Button variant="primary" fullWidth onClick={onBookClick}>
        Book Now
      </Button>
      <Button variant="secondary" fullWidth onClick={onQuoteClick}>
        Request Quote
      </Button>
    </div>
  </div>
</div>
```

### Info Card
```jsx
<InfoCard title="Total Revenue" value="₹24,560" change="+12%" icon={<TrendUpIcon />} />

// Simple stats card used in dashboard
<div className="info-card">
  <div className="card-icon">{icon}</div>
  <div className="card-content">
    <h4 className="title">{title}</h4>
    <p className="value">{value}</p>
    <span className={`change ${change > 0 ? 'positive' : 'negative'}`}>
      {change}
    </span>
  </div>
</div>
```

---

## Form Components

### Text Input
```jsx
<Input
  label="Shipping Address"
  placeholder="Enter full address"
  value={address}
  onChange={(e) => setAddress(e.target.value)}
  error={errors.address}
  hint="Include flat number and landmark"
/>

// Component
<div className="input-group">
  {label && <label htmlFor={id}>{label}</label>}
  
  <input
    id={id}
    type="text"
    placeholder={placeholder}
    value={value}
    onChange={onChange}
    disabled={disabled}
    className={`input ${error ? 'input-error' : ''}`}
  />
  
  {hint && <p className="input-hint">{hint}</p>}
  {error && <p className="input-error">{error}</p>}
</div>

// CSS
.input {
  background: white;
  border: 1px solid #D1D5DB;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 16px;
  transition: all 150ms ease-out;
}

.input:focus {
  border-color: #BE185D;
  outline: none;
  box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.1);
}

.input-error {
  border-color: #EF4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.input:disabled {
  background: #F3F4F6;
  color: #9CA3AF;
}
```

### Quantity Selector
```jsx
<QuantitySelector
  value={quantity}
  min={1}
  max={100}
  step={1}
  unit="kg"
  onChangeValue={setQuantity}
/>

// Component
<div className="quantity-selector">
  <button
    className="qty-btn"
    onClick={() => handleChange(value - step)}
    disabled={value <= min}
  >
    −
  </button>
  
  <div className="qty-display">
    <input
      type="number"
      value={value}
      onChange={(e) => handleChange(Number(e.target.value))}
      min={min}
      max={max}
    />
    <span className="unit">{unit}</span>
  </div>
  
  <button
    className="qty-btn"
    onClick={() => handleChange(value + step)}
    disabled={value >= max}
  >
    +
  </button>
</div>

// Animations
.qty-display input {
  /* Number increases with brief scale animation */
  animation: scaleUp 200ms ease-out;
}

@keyframes scaleUp {
  0% { transform: scale(1); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}
```

### Checkbox
```jsx
<Checkbox
  label="I agree to terms"
  checked={agreed}
  onChange={setAgreed}
/>

// Component
<div className="checkbox-group">
  <input
    type="checkbox"
    id={id}
    checked={checked}
    onChange={onChange}
    className="checkbox-input"
  />
  {label && <label htmlFor={id}>{label}</label>}
</div>

// CSS
.checkbox-input {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 2px solid #D1D5DB;
  border-radius: 6px;
  cursor: pointer;
  background: white;
  transition: all 150ms ease-out;
}

.checkbox-input:checked {
  background: #BE185D;
  border-color: #BE185D;
}

.checkbox-input:checked::after {
  content: '✓';
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### Radio Button
```jsx
<RadioGroup value={duration} onChange={setDuration}>
  <Radio value="2h" label="2 Hours" price={3000} />
  <Radio value="4h" label="4 Hours" price={6000} />
  <Radio value="6h" label="6 Hours" price={9000} />
</RadioGroup>
```

---

## Layout Components

### Container
```jsx
<Container padding="md">
  {children}
</Container>

// CSS
.container {
  max-width: 1200px;
  margin: 0 auto;
}

.container-padding-sm { padding: 16px; }
.container-padding-md { padding: 20px; }
.container-padding-lg { padding: 24px; }

// Responsive
@media (max-width: 768px) {
  .container {
    padding: 16px;
  }
}
```

### Grid
```jsx
<Grid columns={3} gap="md">
  {items.map(item => (
    <GridItem key={item.id}>{item.name}</GridItem>
  ))}
</Grid>

// CSS
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

// Responsive
@media (max-width: 1024px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
```

### Stack (Flexbox)
```jsx
<Stack direction="column" gap="md" align="center">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Stack>

// CSS
.stack {
  display: flex;
  gap: 16px;
}

.stack-row {
  flex-direction: row;
}

.stack-column {
  flex-direction: column;
}

.stack-align-start {
  align-items: flex-start;
}

.stack-align-center {
  align-items: center;
}

.stack-justify-between {
  justify-content: space-between;
}
```

---

## Navigation Components

### Bottom Tab Navigation (Mobile)
```jsx
const MobileNav = () => {
  const [active, setActive] = useState('home');
  
  return (
    <nav className="mobile-nav">
      <NavItem
        icon={<HomeIcon />}
        label="Home"
        active={active === 'home'}
        onClick={() => setActive('home')}
      />
      <NavItem
        icon={<SearchIcon />}
        label="Search"
        active={active === 'search'}
        onClick={() => setActive('search')}
      />
      <NavItem
        icon={<CalendarIcon />}
        label="Bookings"
        badge={3}
        active={active === 'bookings'}
        onClick={() => setActive('bookings')}
      />
      <NavItem
        icon={<MessageIcon />}
        label="Chat"
        badge={2}
        active={active === 'chat'}
        onClick={() => setActive('chat')}
      />
      <NavItem
        icon={<UserIcon />}
        label="Profile"
        active={active === 'profile'}
        onClick={() => setActive('profile')}
      />
    </nav>
  );
};

// CSS
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: white;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: space-around;
  z-index: 100;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #6B7280;
  transition: color 200ms ease-out;
}

.nav-item.active {
  color: #BE185D;
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  top: 0;
  width: 20px;
  height: 3px;
  background: #BE185D;
  border-radius: 0 0 3px 3px;
}
```

### Sidebar Navigation (Desktop)
```jsx
const DesktopNav = () => (
  <aside className="sidebar">
    <div className="logo">Shadiro</div>
    
    <nav className="nav-links">
      <NavLink icon={<DashboardIcon />} label="Dashboard" href="/" />
      <NavLink icon={<StoreIcon />} label="Vendors" href="/vendors" />
      <NavLink icon={<CalendarIcon />} label="Bookings" href="/bookings" />
      <NavLink icon={<MessageIcon />} label="Chat" href="/chat" />
      <NavLink icon={<CreditCardIcon />} label="Payments" href="/payments" />
      <NavLink icon={<UserIcon />} label="Profile" href="/profile" />
    </nav>
    
    <div className="sidebar-footer">
      <SettingsIcon /> Settings
    </div>
  </aside>
);

// CSS
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #E5E7EB;
  padding: 24px 0;
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 16px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: #6B7280;
  text-decoration: none;
  border-radius: 8px;
  transition: all 150ms ease-out;
}

.nav-link:hover {
  background: #F3F4F6;
  color: #1F2937;
}

.nav-link.active {
  background: #FCE7F3;
  color: #BE185D;
  font-weight: 600;
}
```

---

## Data Display Components

### Rating Component
```jsx
<Rating value={4.8} count={234} />

// Component
<div className="rating">
  <div className="stars">
    {[1, 2, 3, 4, 5].map(i => (
      <span key={i} className={i <= Math.round(value) ? 'star filled' : 'star'}>
        ★
      </span>
    ))}
  </div>
  <span className="value">{value}/5</span>
  <span className="count">({count} reviews)</span>
</div>

// CSS
.rating {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stars {
  display: flex;
  gap: 2px;
}

.star {
  font-size: 16px;
  color: #D1D5DB;
}

.star.filled {
  color: #F59E0B;
}
```

### Badge Component
```jsx
<Badge variant="primary" icon={<VerifiedIcon />}>
  Verified
</Badge>

// Variants
<Badge variant="primary">Primary</Badge>
<Badge variant="success">Success</Badge>
<Badge variant="warning">Warning</Badge>
<Badge variant="gold">Premium</Badge>

// CSS
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.badge-primary {
  background: #FCE7F3;
  color: #BE185D;
}

.badge-success {
  background: #ECFDF5;
  color: #10B981;
}

.badge-warning {
  background: #FFFBEB;
  color: #F59E0B;
}

.badge-gold {
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
  color: #D97706;
}
```

### Category Chips
```jsx
<CategoryChips categories={['Catering', 'North Indian', 'Vegetarian']} />

// Component
<div className="category-chips">
  {categories.map(cat => (
    <span key={cat} className="chip">
      {cat}
    </span>
  ))}
</div>

// CSS
.chip {
  display: inline-block;
  padding: 6px 12px;
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 999px;
  font-size: 12px;
  color: #6B7280;
  margin-right: 4px;
  margin-bottom: 4px;
}
```

---

## Modal & Overlay Components

### Modal Dialog
```jsx
<Modal
  open={isOpen}
  title="Confirm Booking"
  onClose={() => setIsOpen(false)}
>
  <div className="modal-content">
    <p>Are you sure you want to confirm this booking?</p>
    <div className="modal-details">
      <p>Service: {booking.service}</p>
      <p>Date: {booking.date}</p>
      <p>Amount: ₹{booking.amount}</p>
    </div>
  </div>
  
  <div className="modal-actions">
    <Button variant="secondary" onClick={() => setIsOpen(false)}>
      Cancel
    </Button>
    <Button variant="primary" onClick={handleConfirm}>
      Confirm Booking
    </Button>
  </div>
</Modal>

// CSS
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 250ms ease-out;
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 300ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    transform: translateY(40px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
```

### Bottom Sheet (Mobile Modal)
```jsx
<BottomSheet open={isOpen} onClose={() => setIsOpen(false)}>
  <div className="filters">
    <h2>Filters</h2>
    {/* Filter content */}
  </div>
</BottomSheet>

// CSS
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-radius: 16px 16px 0 0;
  max-height: 90vh;
  overflow-y: auto;
  z-index: 1000;
  animation: slideUp 300ms ease-out;
}

.bottom-sheet-handle {
  width: 40px;
  height: 4px;
  background: #D1D5DB;
  border-radius: 2px;
  margin: 8px auto 16px;
}
```

### Toast Notification
```jsx
<Toast
  message="Booking confirmed!"
  type="success"
  duration={4000}
  onClose={() => setShowToast(false)}
/>

// CSS
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 2000;
  animation: slideIn 250ms ease-out;
}

.toast.success {
  background: #ECFDF5;
  color: #10B981;
  border-left: 4px solid #10B981;
}

.toast.error {
  background: #FEF2F2;
  color: #EF4444;
  border-left: 4px solid #EF4444;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## Chat Components

### Chat List Item
```jsx
<ChatListItem
  avatar={vendor.avatar}
  name={vendor.name}
  lastMessage={lastMsg}
  timestamp={lastMsg.timestamp}
  unreadCount={3}
  isOnline={true}
  onClick={() => navigateToChat(vendor.id)}
/>

// Component
<div className="chat-list-item" onClick={onClick}>
  <div className="item-avatar">
    <img src={avatar} alt={name} />
    <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
  </div>
  
  <div className="item-content">
    <div className="header">
      <h4>{name}</h4>
      <span className="time">{formatTime(timestamp)}</span>
    </div>
    <p className="message">{lastMessage}</p>
  </div>
  
  {unreadCount > 0 && (
    <Badge variant="primary">{unreadCount}</Badge>
  )}
</div>

// CSS
.chat-list-item {
  padding: 12px;
  border-bottom: 1px solid #F3F4F6;
  cursor: pointer;
  transition: background 150ms ease-out;
}

.chat-list-item:hover {
  background: #F9FAFB;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  position: absolute;
  bottom: 0;
  right: 0;
  background: #6B7280;
}

.status-dot.online {
  background: #10B981;
}
```

### Chat Message Bubble
```jsx
<MessageBubble
  message={msg}
  isOwn={msg.senderId === userId}
  timestamp={msg.timestamp}
  read={msg.read}
/>

// Component
<div className={`message ${isOwn ? 'own' : 'other'}`}>
  <div className="bubble">
    <p>{message.text}</p>
    {message.image && <img src={message.image} alt="Shared" />}
  </div>
  
  <div className="meta">
    <span className="time">{formatTime(timestamp)}</span>
    {isOwn && <span className="status">{read ? '✔✔' : '✔'}</span>}
  </div>
</div>

// CSS
.message {
  display: flex;
  margin-bottom: 12px;
  gap: 8px;
}

.message.own {
  justify-content: flex-end;
}

.message.other {
  justify-content: flex-start;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  word-wrap: break-word;
}

.message.own .bubble {
  background: #BE185D;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.other .bubble {
  background: #F3F4F6;
  color: #1F2937;
  border-bottom-left-radius: 4px;
}
```

### Typing Indicator
```jsx
<TypingIndicator show={isVendorTyping} />

// Component
<div className={`typing-indicator ${show ? 'visible' : 'hidden'}`}>
  <span></span>
  <span></span>
  <span></span>
  <p>Vendor is typing...</p>
</div>

// CSS
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #D1D5DB;
  border-radius: 50%;
  animation: bounce 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
}
```

---

## Vendor-Specific Components

### Grocery Item Card
```jsx
<GroceryItem
  name="Basmati Rice (Premium)"
  price={120}
  unit="per kg"
  rating={4.9}
  purchases={450}
  quantity={quantity}
  onQuantityChange={setQuantity}
  onAddToCart={handleAdd}
/>

// Component structure
<div className="grocery-item">
  <div className="item-header">
    <h4>{name}</h4>
    <Rating value={rating} count={purchases} />
  </div>
  
  <div className="price-section">
    <span className="price">₹{price}</span>
    <span className="unit">{unit}</span>
  </div>
  
  <div className="quantity-controls">
    <QuantitySelector value={quantity} onChange={onQuantityChange} />
  </div>
  
  <div className="subtotal">
    Subtotal: ₹{price * quantity}
  </div>
</div>
```

### DJ Service Package Card
```jsx
<DJPackageCard
  name="Basic Package"
  items={['DJ + Sound', 'Equipment setup']}
  price={3000}
  unit="per hour"
  selected={selectedPackage === 'basic'}
  onSelect={() => setSelectedPackage('basic')}
/>

// Component
<div className={`package-card ${selected ? 'selected' : ''}`}>
  <div className="header">
    <h4>{name}</h4>
    <span className="price">₹{price}/{unit}</span>
  </div>
  
  <ul className="features">
    {items.map(item => (
      <li key={item}>✓ {item}</li>
    ))}
  </ul>
  
  <Button
    variant={selected ? 'primary' : 'secondary'}
    onClick={onSelect}
    fullWidth
  >
    {selected ? 'Selected' : 'Select'}
  </Button>
</div>
```

### Wedding Theme Card
```jsx
<ThemeCard
  image={themeImage}
  name="Traditional Theme"
  price={25000}
  features={['Full decor', 'Lighting', 'Setup']}
  selected={selectedTheme === 'traditional'}
  onSelect={() => setSelectedTheme('traditional')}
/>
```

---

## Admin Components

### Vendor Management Table
```jsx
<VendorTable
  vendors={vendors}
  columns={['name', 'rating', 'status', 'actions']}
  onApprove={(vendorId) => handleApprove(vendorId)}
  onSuspend={(vendorId) => handleSuspend(vendorId)}
/>

// Component renders table with:
// - Vendor info (name, email, rating)
// - Status badge (active, inactive, flagged)
// - Action buttons (approve, suspend, edit, delete)
// - Responsive: scroll on mobile, full table on desktop
```

### Replacement Assignment Modal
```jsx
<ReplacementAssignmentModal
  booking={booking}
  suggestions={suggestedVendors}
  onAssign={(vendorId) => assignReplacement(vendorId)}
  onCancel={() => setShowModal(false)}
/>

// Shows:
// - Original booking details
// - List of AI-suggested replacement vendors
// - Vendor cards with rating, availability, distance
// - Refund method options
// - Assign button
```

---

## Animation & Transition Utilities

### Fade Transition
```jsx
import { Transition } from 'react-transition-group';

<Transition in={isOpen} timeout={300}>
  {state => (
    <div
      style={{
        opacity: state === 'entered' ? 1 : 0,
        transition: 'opacity 300ms ease-out'
      }}
    >
      Content
    </div>
  )}
</Transition>
```

### Stagger Animation for Lists
```jsx
const StaggerContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  
  & > * {
    animation: slideUp 500ms ease-out;
    animation-fill-mode: both;
  }
  
  & > :nth-child(1) { animation-delay: 0ms; }
  & > :nth-child(2) { animation-delay: 50ms; }
  & > :nth-child(3) { animation-delay: 100ms; }
  /* ... etc */
`;

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## Accessibility Implementation

### ARIA Labels
```jsx
<button aria-label="Add to wishlist" className="heart-button">
  ❤️
</button>

<div role="alert" className="notification">
  Booking confirmed!
</div>

<nav aria-label="Main navigation">
  {/* Navigation items */}
</nav>
```

### Focus Management
```jsx
.button:focus-visible {
  outline: 2px solid #BE185D;
  outline-offset: 2px;
}

.input:focus-visible {
  outline: 2px solid #BE185D;
  outline-offset: 2px;
}
```

### Semantic HTML
- Use `<button>` for clickable elements, not `<div>`
- Use `<nav>` for navigation
- Use `<main>` for main content
- Use `<aside>` for sidebars
- Use `<form>` for forms with `<label>` elements
- Use `<article>` for independent content

---

## Component File Structure

```
src/components/
├── Button/
│   ├── Button.jsx
│   ├── Button.css
│   ├── Button.stories.jsx
│   └── index.js
├── Card/
│   ├── VendorCard.jsx
│   ├── InfoCard.jsx
│   ├── Card.css
│   └── index.js
├── Form/
│   ├── Input.jsx
│   ├── Checkbox.jsx
│   ├── RadioGroup.jsx
│   ├── QuantitySelector.jsx
│   ├── Form.css
│   └── index.js
├── Layout/
│   ├── Container.jsx
│   ├── Grid.jsx
│   ├── Stack.jsx
│   ├── Layout.css
│   └── index.js
├── Navigation/
│   ├── MobileNav.jsx
│   ├── DesktopNav.jsx
│   ├── Navigation.css
│   └── index.js
├── Chat/
│   ├── ChatListItem.jsx
│   ├── MessageBubble.jsx
│   ├── TypingIndicator.jsx
│   ├── Chat.css
│   └── index.js
├── Modal/
│   ├── Modal.jsx
│   ├── BottomSheet.jsx
│   ├── Toast.jsx
│   ├── Modal.css
│   └── index.js
└── Shared/
    ├── Rating.jsx
    ├── Badge.jsx
    ├── Loading.jsx
    ├── Shared.css
    └── index.js
```

---

## CSS Variables (Custom Properties)

```css
:root {
  /* Colors */
  --color-primary: #BE185D;
  --color-primary-dark: #9D174D;
  --color-secondary: #1F2937;
  --color-accent: #F59E0B;
  --color-background: #FAFAFA;
  --color-surface: #FFFFFF;
  --color-border: #E5E7EB;
  --color-text: #1F2937;
  --color-text-secondary: #6B7280;
  --color-success: #10B981;
  --color-error: #EF4444;
  --color-warning: #F59E0B;

  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-secondary: 'Poppins', sans-serif;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-full: 999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

  /* Transitions */
  --transition-fast: 150ms ease-out;
  --transition-standard: 250ms ease-out;
}
```

---

**Component Library Version: 1.0**  
**Last Updated: February 9, 2026**  
**Status: Ready for Development**
