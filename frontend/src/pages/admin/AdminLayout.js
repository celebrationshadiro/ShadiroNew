import React from 'react';
import { Navigate, Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { LayoutDashboard, Users, Store, CreditCard, LogOut, Activity, TrendingUp, Timer } from 'lucide-react';

const AdminLayout = () => {
  const { user, loading, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500">Loading...</p>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const nav = [
    { path: '/admin', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/admin/vendors', label: 'Vendors', icon: Store },
    { path: '/admin/users', label: 'Users', icon: Users },
    { path: '/admin/orders', label: 'Grocery Orders', icon: CreditCard },
    { path: '/admin/bookings', label: 'Service Bookings', icon: CreditCard },
    { path: '/admin/payments', label: 'Payments', icon: CreditCard },
    { path: '/admin/payouts', label: 'Payouts', icon: CreditCard },
    { path: '/admin/audit-logs', label: 'Audit Logs', icon: Activity },
    { path: '/admin/platform-audit-logs', label: 'Platform Logs', icon: Activity },
    { path: '/admin/automation', label: 'Automation', icon: Timer },
    { path: '/admin/report', label: 'Reliability Report', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen bg-stone-50 flex">
      <aside className="w-64 bg-white border-r border-stone-200 p-4 flex flex-col">
        <div className="mb-6">
          <h2 className="text-lg font-bold px-2">Admin Panel</h2>
          <p className="text-xs text-stone-500 px-2 mt-1">{user.email}</p>
        </div>

        <nav className="space-y-1 flex-1">
          {nav.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                location.pathname === path
                  ? 'bg-black text-white'
                  : 'hover:bg-stone-100 text-stone-700'
              }`}
            >
              <Icon className="w-5 h-5" />
              {label}
            </Link>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-stone-700 hover:bg-stone-100 transition-colors border-t border-stone-200 mt-4"
        >
          <LogOut className="w-5 h-5" />
          Logout
        </button>
      </aside>

      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
