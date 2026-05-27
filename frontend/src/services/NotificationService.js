/**
 * Notification Service
 * Handles email, SMS, in-app, and push notifications
 */

class NotificationService {
  constructor() {
    this.subscribers = [];
    this.wsConnection = null;
    this.reconnectTimer = null;
    this.currentUserId = null;
    this.currentToken = null;
    this.manualDisconnect = false;
    this.pendingMessages = [];
  }

  /**
   * Initialize WebSocket connection for real-time notifications
   */
  initializeWebSocket(userId, token) {
    if (!userId) return;

    this.currentUserId = userId;
    this.currentToken = token;
    this.manualDisconnect = false;

    // Avoid duplicate connect attempts for same user while socket is active/connecting.
    if (
      this.wsConnection &&
      (this.wsConnection.readyState === WebSocket.OPEN || this.wsConnection.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    const wsUrl = `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/notifications/${userId}`;

    const socket = new WebSocket(wsUrl);
    this.wsConnection = socket;

    socket.onopen = () => {
      // Send auth token only on the socket that actually opened.
      if (token) {
        this.send({
          type: 'auth',
          token: token,
        });
      }
      if (this.pendingMessages.length > 0) {
        const queued = [...this.pendingMessages];
        this.pendingMessages = [];
        queued.forEach((msg) => socket.send(msg));
      }
    };

    socket.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      this.notifySubscribers(notification);
      this.handleNotification(notification);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = () => {
      if (this.wsConnection === socket) {
        this.wsConnection = null;
      }
      if (this.manualDisconnect) return;

      // Reconnect after 3 seconds using latest stored credentials
      this.reconnectTimer = setTimeout(() => {
        this.initializeWebSocket(this.currentUserId, this.currentToken);
      }, 3000);
    };
  }

  /**
   * Subscribe to notification updates
   */
  subscribe(callback) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter((cb) => cb !== callback);
    };
  }

  /**
   * Notify all subscribers
   */
  notifySubscribers(notification) {
    this.subscribers.forEach(callback => callback(notification));
  }

  /**
   * Handle different notification types
   */
  async handleNotification(notification) {
    const { type, priority, message, data } = notification;

    // Show in-app notification
    this.showInAppNotification(notification);

    // Send push notification if enabled
    if (this.isPushNotificationEnabled() && priority === 'high') {
      this.sendPushNotification(notification);
    }
  }

  /**
   * Show in-app notification
   */
  showInAppNotification(notification) {
    // Create notification element
    const notificationEl = document.createElement('div');
    notificationEl.className = `notification notification-${notification.priority}`;
    notificationEl.innerHTML = `
      <div class="notification-icon">${this.getIcon(notification.type)}</div>
      <div class="notification-content">
        <h4>${notification.title}</h4>
        <p>${notification.message}</p>
      </div>
      <button class="notification-close">×</button>
    `;

    const container = document.getElementById('notifications-container') || this.createContainer();
    container.appendChild(notificationEl);

    // Add close handler
    notificationEl.querySelector('.notification-close').addEventListener('click', () => {
      notificationEl.remove();
    });

    // Auto-remove after duration
    setTimeout(() => {
      notificationEl.remove();
    }, notification.duration || 5000);
  }

  /**
   * Send push notification
   */
  async sendPushNotification(notification) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/icon-192x192.png',
        tag: notification.id,
        requireInteraction: notification.priority === 'high',
      });
    }
  }

  /**
   * Send email notification
   */
  async sendEmailNotification(userId, emailTemplateId, data) {
    try {
      // use centralized api client
      const apiClient = (await import('../lib/apiClient')).default;
      await apiClient.post('/api/notifications/email', {
        user_id: userId,
        template_id: emailTemplateId,
        data: data,
      });
    } catch (error) {
      console.error('Error sending email notification:', error);
    }
  }

  /**
   * Send SMS notification
   */
  async sendSmsNotification(phone, message) {
    try {
      const apiClient = (await import('../lib/apiClient')).default;
      await apiClient.post('/api/notifications/sms', { phone, message });
    } catch (error) {
      console.error('Error sending SMS notification:', error);
    }
  }

  /**
   * Get icon for notification type
   */
  getIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
      booking_confirmed: '✓',
      booking_cancelled: '✗',
      message: '💬',
      payment: '💳',
    };
    return icons[type] || 'ℹ️';
  }

  /**
   * Check if push notifications are enabled
   */
  isPushNotificationEnabled() {
    return 'Notification' in window && Notification.permission === 'granted';
  }

  /**
   * Request push notification permission
   */
  async requestPushPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  }

  /**
   * Create notification container
   */
  createContainer() {
    const container = document.createElement('div');
    container.id = 'notifications-container';
    container.className = 'notifications-container';
    document.body.appendChild(container);
    return container;
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    this.manualDisconnect = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.pendingMessages = [];
    if (this.wsConnection && this.wsConnection.readyState !== WebSocket.CLOSED) {
      this.wsConnection.close();
    }
    this.wsConnection = null;
  }

  send(message) {
    const payload = typeof message === 'string' ? message : JSON.stringify(message);
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(payload);
      return;
    }
    this.pendingMessages.push(payload);
  }
}

// Notification templates for different events
export const NotificationTemplates = {
  BOOKING_CREATED: {
    title: '✅ Booking Confirmed',
    message: 'Your booking has been placed successfully',
    type: 'booking_confirmed',
    priority: 'high',
  },
  VENDOR_ACCEPTED: {
    title: '✓ Vendor Accepted Your Booking',
    message: 'Vendor has accepted your booking. You can now chat with them.',
    type: 'booking_confirmed',
    priority: 'high',
  },
  VENDOR_REJECTED: {
    title: '❌ Vendor Rejected Your Booking',
    message: 'Unfortunately, this vendor cannot fulfill your booking. Try another vendor.',
    type: 'error',
    priority: 'medium',
  },
  VENDOR_CANCELLED: {
    title: '⚠️ Vendor Emergency',
    message: 'We are arranging a replacement vendor for you. You will be notified shortly.',
    type: 'warning',
    priority: 'high',
  },
  REPLACEMENT_FOUND: {
    title: '✅ Replacement Vendor Found',
    message: 'We found a replacement vendor with the same quality and price.',
    type: 'success',
    priority: 'high',
  },
  NEW_MESSAGE: {
    title: '💬 New Message',
    message: 'You have a new message from a vendor',
    type: 'message',
    priority: 'medium',
  },
  PAYMENT_SUCCESS: {
    title: '✅ Payment Successful',
    message: 'Your payment has been processed successfully',
    type: 'success',
    priority: 'high',
  },
  PAYMENT_FAILED: {
    title: '❌ Payment Failed',
    message: 'Your payment could not be processed. Please try again.',
    type: 'error',
    priority: 'high',
  },
};

export default new NotificationService();
