# Shadiro - React Implementation Examples

## Quick Start Code Snippets

Developers can use these examples as starting points for their implementation.

---

## 1. Button Component Implementation

### File: `src/components/Button/Button.jsx`

```jsx
import React from 'react';
import PropTypes from 'prop-types';
import './Button.css';

const Button = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  onClick,
  children,
  className = '',
  type = 'button',
  ...props
}) => {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`
        button
        button-${variant}
        button-${size}
        ${fullWidth ? 'button-full-width' : ''}
        ${loading ? 'button-loading' : ''}
        ${className}
      `.trim()}
      {...props}
    >
      {loading ? (
        <>
          <span className="button-spinner"></span>
          {children}
        </>
      ) : (
        children
      )}
    </button>
  );
};

Button.propTypes = {
  variant: PropTypes.oneOf(['primary', 'secondary', 'outline', 'icon']),
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  fullWidth: PropTypes.bool,
  onClick: PropTypes.func,
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  type: PropTypes.string,
};

export default Button;
```

### File: `src/components/Button/Button.css`

```css
/* Button Base Styles */
.button {
  font-family: var(--font-primary);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-standard);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  white-space: nowrap;
}

.button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Button Variants */
.button-primary {
  background-color: var(--color-primary);
  color: white;
  box-shadow: var(--shadow-md);
}

.button-primary:hover:not(:disabled) {
  background-color: var(--color-primary-dark);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.button-primary:active:not(:disabled) {
  background-color: #831843;
  transform: translateY(0);
  box-shadow: var(--shadow-md);
}

.button-secondary {
  background-color: var(--color-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.button-secondary:hover:not(:disabled) {
  background-color: var(--color-border);
  border-color: var(--color-text-secondary);
}

.button-outline {
  background-color: transparent;
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
}

.button-outline:hover:not(:disabled) {
  background-color: #FCE7F3;
}

.button-icon {
  background-color: transparent;
  color: var(--color-text);
  padding: 8px;
  border-radius: var(--radius-sm);
}

.button-icon:hover:not(:disabled) {
  background-color: var(--color-background);
}

/* Button Sizes */
.button-sm {
  padding: 8px 16px;
  font-size: 14px;
}

.button-md {
  padding: 12px 24px;
  font-size: 16px;
}

.button-lg {
  padding: 16px 32px;
  font-size: 18px;
}

/* Full Width */
.button-full-width {
  width: 100%;
}

/* Loading State */
.button-loading {
  opacity: 0.8;
  position: relative;
}

.button-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 600ms linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

---

## 2. Vendor Card Component

### File: `src/components/Card/VendorCard.jsx`

```jsx
import React, { useState } from 'react';
import './VendorCard.css';
import Button from '../Button/Button';
import Badge from '../Badge/Badge';
import Rating from '../Rating/Rating';

const VendorCard = ({
  id,
  image,
  name,
  rating,
  reviewCount,
  priceStart,
  priceEnd,
  distance,
  isAvailable,
  isVerified,
  categories,
  onBookClick,
  onQuoteClick,
  onWishlistClick,
}) => {
  const [isWishlisted, setIsWishlisted] = useState(false);

  const handleWishlist = () => {
    setIsWishlisted(!isWishlisted);
    onWishlistClick?.(!isWishlisted);
  };

  return (
    <div className="vendor-card">
      {/* Image Section */}
      <div className="vendor-card-image">
        <img src={image} alt={name} />
        
        {/* Verified Badge */}
        {isVerified && (
          <Badge variant="gold" className="vendor-verified-badge">
            ✓ Verified
          </Badge>
        )}

        {/* Wishlist Button */}
        <button
          className={`wishlist-button ${isWishlisted ? 'active' : ''}`}
          onClick={handleWishlist}
          aria-label="Add to wishlist"
        >
          ❤️
        </button>
      </div>

      {/* Content Section */}
      <div className="vendor-card-content">
        <h3 className="vendor-name">{name}</h3>

        {/* Rating Section */}
        <div className="rating-row">
          <Rating value={rating} count={reviewCount} />
        </div>

        {/* Meta Info */}
        <div className="meta-info">
          <span className="distance">📍 {distance}km away</span>
          <span className={`availability ${isAvailable ? 'available' : 'unavailable'}`}>
            {isAvailable ? '✅ Available' : '❌ Unavailable'}
          </span>
        </div>

        {/* Price Range */}
        <div className="price-range">
          Est. ₹{priceStart.toLocaleString()} - ₹{priceEnd.toLocaleString()}
        </div>

        {/* Category Chips */}
        {categories && categories.length > 0 && (
          <div className="category-chips">
            {categories.slice(0, 3).map((cat) => (
              <span key={cat} className="chip">
                {cat}
              </span>
            ))}
          </div>
        )}

        {/* Action Buttons */}
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
  );
};

export default VendorCard;
```

### File: `src/components/Card/VendorCard.css`

```css
.vendor-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-standard);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.vendor-card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

/* Image Section */
.vendor-card-image {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
  background: var(--color-background);
  overflow: hidden;
}

.vendor-card-image img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Verified Badge */
.vendor-verified-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

/* Wishlist Button */
.wishlist-button {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: var(--radius-full);
  width: 40px;
  height: 40px;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 200ms ease-out;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.wishlist-button:hover {
  background: white;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.wishlist-button.active {
  color: #EF4444;
}

/* Content Section */
.vendor-card-content {
  padding: var(--space-5);
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.vendor-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
}

/* Rating Row */
.rating-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Meta Info */
.meta-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.availability {
  font-weight: 600;
}

.availability.unavailable {
  color: var(--color-error);
}

/* Price Range */
.price-range {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-primary);
}

/* Category Chips */
.category-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  display: inline-block;
  padding: 4px 10px;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: 12px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* Button Group */
.button-group {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.button-group > button {
  flex: 1;
}

/* Responsive */
@media (max-width: 768px) {
  .vendor-card {
    border: none;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
  }

  .vendor-card:hover {
    box-shadow: var(--shadow-md);
  }

  .vendor-card-content {
    padding: var(--space-4);
  }
}
```

---

## 3. Quantity Selector Component

### File: `src/components/Form/QuantitySelector.jsx`

```jsx
import React, { useState } from 'react';
import './QuantitySelector.css';

const QuantitySelector = ({
  value = 0,
  min = 0,
  max = 100,
  step = 1,
  unit = 'qty',
  onChange,
}) => {
  const [isFocused, setIsFocused] = useState(false);

  const handleDecrement = () => {
    if (value > min) {
      onChange(value - step);
    }
  };

  const handleIncrement = () => {
    if (value < max) {
      onChange(value + step);
    }
  };

  const handleInputChange = (e) => {
    let newValue = parseFloat(e.target.value) || 0;
    newValue = Math.max(min, Math.min(newValue, max));
    onChange(newValue);
  };

  return (
    <div className="quantity-selector">
      <button
        className="qty-btn qty-decrease"
        onClick={handleDecrement}
        disabled={value <= min}
        aria-label="Decrease quantity"
      >
        −
      </button>

      <div
        className={`qty-display ${isFocused ? 'focused' : ''}`}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
      >
        <input
          type="number"
          value={value}
          onChange={handleInputChange}
          min={min}
          max={max}
          step={step}
          className="qty-input"
        />
        <span className="qty-unit">{unit}</span>
      </div>

      <button
        className="qty-btn qty-increase"
        onClick={handleIncrement}
        disabled={value >= max}
        aria-label="Increase quantity"
      >
        +
      </button>
    </div>
  );
};

export default QuantitySelector;
```

### File: `src/components/Form/QuantitySelector.css`

```css
.quantity-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 2px;
  background: white;
  width: fit-content;
}

.qty-btn {
  background: transparent;
  border: none;
  width: 32px;
  height: 32px;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 150ms ease-out;
}

.qty-btn:hover:not(:disabled) {
  background: var(--color-background);
}

.qty-btn:active:not(:disabled) {
  background: var(--color-border);
}

.qty-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.qty-display {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  background: var(--color-background);
  border-radius: 4px;
  transition: all 150ms ease-out;
}

.qty-display.focused {
  background: white;
  box-shadow: inset 0 0 0 2px var(--color-primary);
}

.qty-input {
  width: 50px;
  background: transparent;
  border: none;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  text-align: center;
}

.qty-input:focus {
  outline: none;
}

/* Chrome number input spinner hide */
.qty-input::-webkit-outer-spin-button,
.qty-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.qty-unit {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .qty-btn {
    width: 28px;
    height: 28px;
    font-size: 16px;
  }

  .qty-input {
    width: 40px;
  }
}
```

---

## 4. Dynamic Services UI - Grocery Vendor

### File: `src/components/VendorDetail/GroceryServicesUI.jsx`

```jsx
import React, { useState } from 'react';
import QuantitySelector from '../Form/QuantitySelector';
import Button from '../Button/Button';
import Rating from '../Rating/Rating';
import './GroceryServicesUI.css';

const GroceryServicesUI = ({ categories, onAddToBooking }) => {
  const [selectedItems, setSelectedItems] = useState({});

  const handleQuantityChange = (itemId, qty) => {
    setSelectedItems((prev) => ({
      ...prev,
      [itemId]: qty,
    }));
  };

  const getTotalPrice = () => {
    return Object.entries(selectedItems).reduce((total, [itemId, qty]) => {
      const item = categories
        .flatMap((cat) => cat.items)
        .find((item) => item.id === itemId);
      return total + (item ? item.price * qty : 0);
    }, 0);
  };

  const getTotalItems = () => {
    return Object.values(selectedItems).reduce((sum, qty) => sum + qty, 0);
  };

  const handleAddToBooking = () => {
    const items = Object.entries(selectedItems)
      .filter(([, qty]) => qty > 0)
      .map(([itemId, qty]) => {
        const item = categories
          .flatMap((cat) => cat.items)
          .find((item) => item.id === itemId);
        return {
          ...item,
          quantity: qty,
          subtotal: item.price * qty,
        };
      });

    onAddToBooking(items);
  };

  return (
    <div className="grocery-services-ui">
      <div className="services-list">
        {categories.map((category) => (
          <div key={category.id} className="category-section">
            <details className="category-accordion">
              <summary className="category-header">
                <span className="category-name">{category.name}</span>
                <span className="category-count">
                  {category.items.length} items
                </span>
                <span className="toggle-icon">▼</span>
              </summary>

              <div className="category-items">
                {category.items.map((item) => (
                  <div key={item.id} className="grocery-item">
                    <div className="item-header">
                      <h4 className="item-name">{item.name}</h4>
                      <Rating value={item.rating} count={item.purchases} />
                    </div>

                    <div className="item-price">
                      <span className="price-value">₹{item.price}</span>
                      <span className="price-unit">/{item.unit}</span>
                    </div>

                    <div className="item-controls">
                      <QuantitySelector
                        value={selectedItems[item.id] || 0}
                        min={0}
                        max={item.maxQty || 100}
                        step={item.unit === 'kg' ? 0.5 : 1}
                        unit={item.unit}
                        onChange={(qty) => handleQuantityChange(item.id, qty)}
                      />
                    </div>

                    {selectedItems[item.id] > 0 && (
                      <div className="item-subtotal">
                        Subtotal: ₹
                        {(item.price * selectedItems[item.id]).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </details>
          </div>
        ))}
      </div>

      {/* Sticky Bottom Bar */}
      {getTotalItems() > 0 && (
        <div className="sticky-summary">
          <div className="summary-details">
            <span className="summary-label">
              Total: {getTotalItems()} items
            </span>
            <span className="summary-price">
              ₹{getTotalPrice().toLocaleString()}
            </span>
          </div>

          <div className="summary-actions">
            <Button variant="secondary" onClick={() => window.scrollTo(0, 0)}>
              Continue Shopping
            </Button>
            <Button variant="primary" onClick={handleAddToBooking}>
              Add to Booking
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroceryServicesUI;
```

### File: `src/components/VendorDetail/GroceryServicesUI.css`

```css
.grocery-services-ui {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.services-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.category-section {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-4);
}

.category-section:last-child {
  border-bottom: none;
}

.category-accordion {
  list-style: none;
}

.category-accordion > summary {
  cursor: pointer;
  user-select: none;
}

.category-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  background: var(--color-background);
  border-radius: var(--radius-md);
  transition: all 200ms ease-out;
}

.category-header:hover {
  background: var(--color-border);
}

.category-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
}

.category-count {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.toggle-icon {
  display: inline-block;
  margin-left: auto;
  transition: transform 200ms ease-out;
}

.category-accordion[open] .toggle-icon {
  transform: rotate(180deg);
}

.category-items {
  padding: var(--space-4) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.grocery-item {
  padding: var(--space-4);
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all 150ms ease-out;
}

.grocery-item:hover {
  box-shadow: var(--shadow-sm);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: var(--space-3);
}

.item-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
  line-height: 1.4;
}

.item-price {
  display: flex;
  gap: 4px;
  align-items: baseline;
}

.price-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
}

.price-unit {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.item-controls {
  display: flex;
  justify-content: center;
}

.item-subtotal {
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent);
  animation: fadeIn 200ms ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Sticky Bottom Summary */
.sticky-summary {
  position: sticky;
  bottom: 0;
  background: white;
  border-top: 1px solid var(--color-border);
  padding: var(--space-4);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.08);
  z-index: 50;
}

.summary-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  font-size: 16px;
  font-weight: 600;
}

.summary-label {
  color: var(--color-text-secondary);
}

.summary-price {
  color: var(--color-primary);
  font-size: 20px;
}

.summary-actions {
  display: flex;
  gap: var(--space-3);
}

.summary-actions button {
  flex: 1;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .sticky-summary {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  }

  /* Add bottom padding to content so it's not hidden behind sticky bar */
  .grocery-services-ui {
    padding-bottom: 140px;
  }

  .summary-actions {
    flex-direction: column;
  }
}
```

---

## 5. Chat Component

### File: `src/components/Chat/ChatWindow.jsx`

```jsx
import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import './ChatWindow.css';

const ChatWindow = ({ messages, vendor, onSendMessage, isTyping }) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      onSendMessage(inputMessage);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-window">
      {/* Header */}
      <div className="chat-header">
        <div className="vendor-info">
          <img src={vendor.avatar} alt={vendor.name} className="vendor-avatar" />
          <div>
            <h3 className="vendor-name">{vendor.name}</h3>
            <span className={`status ${vendor.isOnline ? 'online' : 'offline'}`}>
              {vendor.isOnline ? '🟢 Online' : `🔴 Active ${vendor.lastSeen}`}
            </span>
          </div>
        </div>
        <button className="header-action" aria-label="More options">
          ⋮
        </button>
      </div>

      {/* Messages Area */}
      <div className="messages-container">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            isOwn={message.senderId === 'current-user'}
          />
        ))}

        {isTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-actions">
          <button className="input-action-btn" aria-label="Attach file">
            📎
          </button>
          <button className="input-action-btn" aria-label="Add emoji">
            😊
          </button>
        </div>

        <textarea
          className="message-input"
          placeholder="Type your message..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          rows="1"
        />

        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim()}
          aria-label="Send message"
        >
          ➤
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
```

### File: `src/components/Chat/ChatWindow.css`

```css
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
}

/* Header */
.chat-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  z-index: 10;
}

.vendor-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
}

.vendor-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.vendor-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.status {
  font-size: 12px;
  color: var(--color-text-secondary);
  display: block;
}

.status.online {
  color: var(--color-success);
  font-weight: 500;
}

.header-action {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Input Area */
.input-area {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  background: white;
}

.input-actions {
  display: flex;
  gap: var(--space-2);
}

.input-action-btn {
  background: transparent;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 150ms ease-out;
}

.input-action-btn:hover {
  transform: scale(1.1);
}

.message-input {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: 16px;
  font-family: var(--font-primary);
  resize: none;
  max-height: 100px;
  transition: all 150ms ease-out;
}

.message-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.1);
}

.message-input::placeholder {
  color: var(--color-text-secondary);
}

.send-button {
  background: var(--color-primary);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 150ms ease-out;
}

.send-button:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .chat-window {
    height: calc(100vh - 64px); /* Account for bottom nav */
  }

  .input-area {
    padding: var(--space-3);
    gap: var(--space-2);
  }

  .message-input {
    padding: var(--space-2) var(--space-3);
    font-size: 14px;
  }
}
```

---

## 6. Micro-Animation Hook

### File: `src/hooks/useAnimation.js`

```javascript
import { useEffect, useRef, useState } from 'react';

export const useAnimation = (animationType = 'fadeIn', duration = 300) => {
  const ref = useRef(null);
  const [isAnimating, setIsAnimating] = useState(true);

  useEffect(() => {
    if (!ref.current) return;

    const animations = {
      fadeIn: {
        keyframes: [
          { opacity: 0 },
          { opacity: 1 },
        ],
        options: { duration, easing: 'ease-out' },
      },
      slideUp: {
        keyframes: [
          { opacity: 0, transform: 'translateY(20px)' },
          { opacity: 1, transform: 'translateY(0)' },
        ],
        options: { duration, easing: 'ease-out' },
      },
      scaleIn: {
        keyframes: [
          { opacity: 0, transform: 'scale(0.95)' },
          { opacity: 1, transform: 'scale(1)' },
        ],
        options: { duration, easing: 'ease-out' },
      },
    };

    const animation = animations[animationType];
    if (animation) {
      ref.current.animate(animation.keyframes, animation.options);
    }
  }, [animationType, duration]);

  return ref;
};
```

---

## 7. API Integration Example

### File: `src/services/api.js`

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Vendor API
export const vendorAPI = {
  getVendors: (params) => api.get('/api/vendors', { params }),
  getVendorById: (id) => api.get(`/api/vendors/${id}`),
  getVendorServices: (id) => api.get(`/api/vendors/${id}/services`),
  getVendorReviews: (id) => api.get(`/api/vendors/${id}/reviews`),
};

// Booking API
export const bookingAPI = {
  createBooking: (data) => api.post('/api/bookings', data),
  getBookings: (params) => api.get('/api/bookings', { params }),
  getBookingById: (id) => api.get(`/api/bookings/${id}`),
  updateBooking: (id, data) => api.put(`/api/bookings/${id}`, data),
  cancelBooking: (id, reason) => 
    api.post(`/api/bookings/${id}/cancel`, { reason }),
};

// Chat API
export const chatAPI = {
  getConversations: () => api.get('/api/chat/conversations'),
  getMessages: (vendorId) => api.get(`/api/chat/${vendorId}/messages`),
  sendMessage: (vendorId, message) =>
    api.post(`/api/chat/${vendorId}/messages`, { text: message }),
};

export default api;
```

---

## 8. Example Page Component - Home

### File: `src/pages/HomePage.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import VendorCard from '../components/Card/VendorCard';
import Button from '../components/Button/Button';
import { vendorAPI } from '../services/api';
import './HomePage.css';

const HomePage = () => {
  const navigate = useNavigate();
  const [recommendedVendors, setRecommendedVendors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVendors = async () => {
      try {
        const response = await vendorAPI.getVendors({ limit: 6 });
        setRecommendedVendors(response.data);
      } catch (error) {
        console.error('Error fetchingvendors:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchVendors();
  }, []);

  const handleQuickAction = (eventType) => {
    navigate('/vendors', { state: { eventType } });
  };

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1>Plan your perfect event, effortlessly</h1>
          <Button variant="primary" size="lg" onClick={() => navigate('/vendors')}>
            Explore Vendors
          </Button>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="quick-actions">
        <h2>Get Started</h2>
        <div className="actions-grid">
          <button className="action-card" onClick={() => handleQuickAction('wedding')}>
            <span className="action-icon">💍</span>
            <span className="action-label">Wedding</span>
          </button>
          <button className="action-card" onClick={() => handleQuickAction('birthday')}>
            <span className="action-icon">🎂</span>
            <span className="action-label">Birthday</span>
          </button>
          <button className="action-card" onClick={() => handleQuickAction('corporate')}>
            <span className="action-icon">🏢</span>
            <span className="action-label">Corporate</span>
          </button>
          <button className="action-card" onClick={() => handleQuickAction('custom')}>
            <span className="action-icon">⚙️</span>
            <span className="action-label">Custom Event</span>
          </button>
        </div>
      </section>

      {/* Recommended Vendors */}
      <section className="recommended-section">
        <div className="section-header">
          <h2>Recommended for You</h2>
          <Button variant="outline" onClick={() => navigate('/vendors')}>
            View All
          </Button>
        </div>

        {loading ? (
          <div className="loading-skeleton">Loading vendors...</div>
        ) : (
          <div className="vendors-grid">
            {recommendedVendors.map((vendor) => (
              <VendorCard
                key={vendor.id}
                {...vendor}
                onBookClick={() => navigate(`/vendor/${vendor.id}`)}
                onQuoteClick={() => navigate(`/vendor/${vendor.id}/quote`)}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default HomePage;
```

---

## Best Practices Summary

1. **Component Composition**: Keep components small and focused
2. **Props Drilling**: Use context for deeply nested props
3. **Performance**: Memoize components with React.memo where needed
4. **Accessibility**: Always include aria-labels and semantic HTML
5. **Responsive Design**: Mobile-first CSS approach
6. **Error Handling**: Wrap async operations with try-catch
7. **Loading States**: Show skeletons or spinners during data fetching
8. **Animation**: Keep animations under 300ms for responsiveness
9. **CSS Variables**: Use tokens for consistency
10. **Reusability**: Extract reusable logic into custom hooks

---

**React Implementation Examples Version: 1.0**  
**Last Updated: February 9, 2026**  
**Ready for Development**
