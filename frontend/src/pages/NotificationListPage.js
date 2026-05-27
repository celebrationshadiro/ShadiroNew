import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Trash2, Loader } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../styles/NotificationList.css';
import apiClient from '../lib/apiClient';
import { toast } from 'sonner';

const NotificationListPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedNotifications, setSelectedNotifications] = useState(new Set());

  useEffect(() => {
    fetchNotifications();
  }, [filter]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (filter !== 'all') {
        queryParams.append('type', filter);
      }

      try {
        const data = await apiClient.get(`/api/notifications?${queryParams}`);
        setNotifications(data.notifications || data || []);
      } catch (err) {
        console.error('Failed to fetch notifications:', err);
        toast.error('Failed to load notifications');
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedNotifications(new Set(notifications.map(n => n.id)));
    } else {
      setSelectedNotifications(new Set());
    }
  };

  const handleSelectNotification = (id) => {
    const newSelected = new Set(selectedNotifications);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedNotifications(newSelected);
  };

  const handleDeleteSelected = async () => {
    if (selectedNotifications.size === 0) return;

    try {
      try {
        await apiClient.post('/api/notifications/bulk-delete', {
          notification_ids: Array.from(selectedNotifications),
        });
        setNotifications(prev => prev.filter(n => !selectedNotifications.has(n.id)));
        setSelectedNotifications(new Set());
        toast.success('Deleted selected notifications');
      } catch (err) {
        console.error('Failed to delete notifications:', err);
        toast.error('Failed to delete notifications');
      }
    } catch (error) {
      console.error('Failed to delete notifications:', error);
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'booking': return '📅';
      case 'payment': return '💳';
      case 'message': return '💬';
      case 'vendor': return '👔';
      case 'user': return '👤';
      case 'system': return '⚙️';
      default: return 'ℹ️';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'booking': return 'booking';
      case 'payment': return 'payment';
      case 'message': return 'message';
      case 'vendor': return 'vendor';
      case 'user': return 'user';
      case 'system': return 'system';
      default: return 'default';
    }
  };

  return (
    <div className="notification-list-page">
      <div className="notification-list-container">
        {/* Header */}
        <div className="notification-list-header">
          <button
            onClick={() => navigate(-1)}
            className="back-btn"
            title="Go back"
          >
            <ArrowLeft size={24} />
          </button>
          <h1>Notifications</h1>
          <div className="header-right">
            {selectedNotifications.size > 0 && (
              <button
                onClick={handleDeleteSelected}
                className="delete-btn"
                title="Delete selected"
              >
                <Trash2 size={20} />
                Delete ({selectedNotifications.size})
              </button>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="notification-filters">
          {['all', 'booking', 'payment', 'message', 'vendor', 'system'].map(type => (
            <button
              key={type}
              className={`filter-btn ${filter === type ? 'active' : ''}`}
              onClick={() => setFilter(type)}
            >
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </button>
          ))}
        </div>

        {/* Select All */}
        {notifications.length > 0 && (
          <div className="select-all-section">
            <input
              type="checkbox"
              id="select-all"
              checked={selectedNotifications.size === notifications.length && notifications.length > 0}
              onChange={handleSelectAll}
            />
            <label htmlFor="select-all">Select All ({notifications.length})</label>
          </div>
        )}

        {/* Notifications List */}
        {loading ? (
          <div className="loading-state">
            <Loader className="spinner" />
            <p>Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔕</div>
            <h3>No notifications</h3>
            <p>
              {filter === 'all'
                ? "You're all caught up!"
                : `No ${filter} notifications`}
            </p>
          </div>
        ) : (
          <div className="notifications-grid">
            {notifications.map(notification => (
              <div
                key={notification.id}
                className={`notification-row ${getTypeColor(notification.type)} ${
                  selectedNotifications.has(notification.id) ? 'selected' : ''
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedNotifications.has(notification.id)}
                  onChange={() => handleSelectNotification(notification.id)}
                  className="notification-checkbox"
                />
                <div className="notification-row-content">
                  <div className="row-header">
                    <span className="type-icon">
                      {getTypeIcon(notification.type)}
                    </span>
                    <div className="row-title-section">
                      <h4>{notification.title}</h4>
                      <span className="type-label">
                        {notification.type.charAt(0).toUpperCase() +
                          notification.type.slice(1)}
                      </span>
                    </div>
                  </div>
                  <p className="row-message">{notification.message}</p>
                  <div className="row-footer">
                    <span className="timestamp">
                      {getRelativeTime(notification.created_at)}
                    </span>
                    {notification.actionUrl && (
                      <button className="action-link">
                        View Details →
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const getRelativeTime = (timestamp) => {
  const now = new Date();
  const date = new Date(timestamp);
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;

  return date.toLocaleDateString();
};

export default NotificationListPage;
