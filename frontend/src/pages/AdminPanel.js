import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import '../styles/AdminPanel.css';
import apiClient from '../lib/apiClient';
import { toast } from 'sonner';

const AdminPanel = () => {
  const [tab, setTab] = useState('urgent');
  const [cancellations, setCancellations] = useState([]);
  const [vendorReplacements, setVendorReplacements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const data = await apiClient.get('/api/admin/incidents');
      setCancellations(data.cancellations || []);
      setVendorReplacements(data.replacements || []);
    } catch (error) {
      console.error('Error fetching admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssignReplacement = async (incidentId, suggestedVendor, refundMethod) => {
    try {
      await apiClient.post(`/api/admin/incidents/${incidentId}/assign-replacement`, {
        replacement_vendor_id: suggestedVendor.id,
        refund_method: refundMethod,
      });
      toast.success('Replacement vendor assigned and customer notified');
      fetchAdminData();
    } catch (error) {
      console.error('Error assigning replacement:', error);
      toast.error('Error assigning replacement: ' + (error.message || 'Unknown'));
    }
  };

  if (loading) return <div className="admin-loading">Loading admin panel...</div>;

  const urgentCount = cancellations.filter(c => c.status === 'pending').length;

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1>🔧 Admin Panel</h1>
        <div className="admin-stats">
          <div className="stat">
            <span className="stat-label">Urgent Cases</span>
            <span className="stat-value">{urgentCount}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Pending Action</span>
            <span className="stat-value">{vendorReplacements.filter(r => r.status === 'awaiting_assignment').length}</span>
          </div>
        </div>
      </div>

      <div className="tab-navigation">
        <button
          className={`tab-btn ${tab === 'urgent' ? 'active' : ''}`}
          onClick={() => setTab('urgent')}
        >
          🔴 Urgent Cancellations ({urgentCount})
        </button>
        <button
          className={`tab-btn ${tab === 'replacements' ? 'active' : ''}`}
          onClick={() => setTab('replacements')}
        >
          🔄 Replacement Assignments ({vendorReplacements.filter(r => r.status === 'awaiting_assignment').length})
        </button>
        <button
          className={`tab-btn ${tab === 'analytics' ? 'active' : ''}`}
          onClick={() => setTab('analytics')}
        >
          📊 Analytics
        </button>
      </div>

      {/* Urgent Cancellations */}
      {tab === 'urgent' && (
        <div className="tab-content">
          <h2>Vendor Cancellation Incidents</h2>
          <div className="incidents-list">
            {cancellations.filter(c => c.status === 'pending').length === 0 ? (
              <Card className="empty-state">
                <p>✅ No urgent cases at the moment!</p>
              </Card>
            ) : (
              cancellations.filter(c => c.status === 'pending').map(incident => (
                <Card key={incident.id} className="incident-card">
                  <div className="incident-header">
                    <div>
                      <h3>Incident #{incident.id}</h3>
                      <p className="incident-time">Reported: {new Date(incident.created_at).toLocaleString()}</p>
                    </div>
                    <span className="badge urgent">⚠️ URGENT</span>
                  </div>

                  <div className="incident-details">
                    <div className="detail">
                      <span className="label">Cancelled Vendor:</span>
                      <span className="value">{incident.vendor_name} ⭐ {incident.vendor_rating}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Client:</span>
                      <span className="value">{incident.client_name}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Service:</span>
                      <span className="value">{incident.service_type}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Event Date:</span>
                      <span className="value">{incident.event_date}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Amount:</span>
                      <span className="value bold">₹{incident.amount?.toLocaleString()}</span>
                    </div>
                    <div className="detail">
                      <span className="label">Reason:</span>
                      <span className="value">{incident.cancellation_reason}</span>
                    </div>
                  </div>

                  <div className="replacement-suggestions">
                    <h4>AI-Suggested Replacements:</h4>
                    {incident.suggested_vendors?.map((vendor, idx) => (
                      <div key={vendor.id} className="replacement-option">
                        <div className="replacement-info">
                          <span className="rank">#{idx + 1}</span>
                          <div>
                            <p className="vendor-name">{vendor.name}</p>
                            <p className="vendor-meta">
                              ⭐ {vendor.rating} | {vendor.distance}km away | Availability: ✅
                            </p>
                          </div>
                        </div>
                        <div className="replacement-actions">
                          <Button 
                            onClick={() => handleAssignReplacement(incident.id, vendor, 'full_refund')}
                            variant="primary"
                          >
                            Assign
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Replacement Assignments */}
      {tab === 'replacements' && (
        <div className="tab-content">
          <h2>Replacement Assignment Queue</h2>
          <div className="replacements-list">
            {vendorReplacements.filter(r => r.status === 'awaiting_assignment').length === 0 ? (
              <Card className="empty-state">
                <p>✅ All replacements assigned!</p>
              </Card>
            ) : (
              vendorReplacements.filter(r => r.status === 'awaiting_assignment').map(replacement => (
                <Card key={replacement.id} className="replacement-card">
                  <div className="replacement-header">
                    <h3>Replacement for Booking #{replacement.original_booking_id}</h3>
                    <span className="time-badge">
                      {Math.round((new Date() - new Date(replacement.created_at)) / 60000)} min ago
                    </span>
                  </div>
                  <div className="replacement-details">
                    <p><strong>Client:</strong> {replacement.client_name}</p>
                    <p><strong>Original Vendor:</strong> {replacement.original_vendor_name}</p>
                    <p><strong>Service:</strong> {replacement.service_type}</p>
                    <p><strong>Date & Time:</strong> {replacement.event_date} @ {replacement.event_time}</p>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}

      {/* Analytics */}
      {tab === 'analytics' && (
        <div className="tab-content">
          <h2>Platform Analytics</h2>
          <div className="analytics-grid">
            <Card className="analytics-card">
              <h3>Cancellation Rate</h3>
              <p className="analytics-value">2.3%</p>
              <p className="analytics-meta">↓ 0.5% from last month</p>
            </Card>
            <Card className="analytics-card">
              <h3>Avg Resolution Time</h3>
              <p className="analytics-value">18 mins</p>
              <p className="analytics-meta">✓ Within SLA</p>
            </Card>
            <Card className="analytics-card">
              <h3>Replacement Success</h3>
              <p className="analytics-value">98.5%</p>
              <p className="analytics-meta">Customer satisfied</p>
            </Card>
            <Card className="analytics-card">
              <h3>Total Incidents Today</h3>
              <p className="analytics-value">{cancellations.length}</p>
              <p className="analytics-meta">{Math.round(urgentCount / cancellations.length * 100)}% resolved</p>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
