import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

/**
 * AdminRoute Component
 * 
 * A route guard that protects admin-only pages. This component ensures that only
 * authenticated users with admin role can access protected admin routes.
 * 
 * Usage:
 * <AdminRoute>
 *   <AdminDashboard />
 * </AdminRoute>
 * 
 * If the user is not authenticated or doesn't have admin role, they'll be
 * redirected to /admin/login
 */
const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-stone-200 border-t-black rounded-full animate-spin mx-auto mb-4" />
          <p className="text-stone-600">Verifying admin access...</p>
        </div>
      </div>
    );
  }

  // Check if user is authenticated and is an admin
  if (!user) {
    return <Navigate to="/admin/login" replace />;
  }

  if (user.role !== 'admin') {
    // Non-admin users trying to access admin routes
    return <Navigate to="/auth" replace />;
  }

  return children;
};

export default AdminRoute;
