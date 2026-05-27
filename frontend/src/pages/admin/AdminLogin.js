import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Mail, Lock, AlertCircle, LogIn } from 'lucide-react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const AdminLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, login, logout } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (user && user.role === 'admin') {
      navigate('/admin', { replace: true });
    } else if (user && user.role !== 'admin') {
      navigate('/auth', { state: { from: location }, replace: true });
    }
  }, [user, navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const userData = await login(email, password);

      // Check if user is admin
      if (!userData || userData.role !== 'admin') {
        logout();
        setError('Only admin users can access the admin panel');
        setLoading(false);
        return;
      }

      toast.success('Admin login successful!');
      navigate('/admin', { replace: true });
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || 'Login failed. Please try again.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-900 via-stone-800 to-stone-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="bg-white rounded-2xl shadow-2xl p-8 border-0">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-stone-900 mb-2">Admin Portal</h1>
            <p className="text-stone-500">Secure access for administrators only</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-5 h-5 text-stone-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@shadiro.com"
                  className="w-full pl-10 pr-4 py-2.5 border border-stone-200 rounded-lg focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-5 h-5 text-stone-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 border border-stone-200 rounded-lg focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-all"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-black hover:bg-stone-900 text-white py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-all"
            >
              <LogIn className="w-4 h-4" />
              {loading ? 'Logging in...' : 'Admin Login'}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-stone-200">
            <p className="text-xs text-stone-500 text-center">
              🔐 This is a restricted area. Unauthorized access attempts are logged and monitored.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AdminLogin;
