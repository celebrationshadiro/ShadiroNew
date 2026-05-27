import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const AuthPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, register } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({
    email: location.state?.prefillEmail || '',
    password: '',
  });
  const [registerForm, setRegisterForm] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    role: 'customer',
  });

  const normalizePhone = (value) => {
    const digits = (value || '').replace(/\D/g, '');
    if (digits.length === 12 && digits.startsWith('91')) return digits.slice(2);
    return digits;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginForm.email, loginForm.password);
      toast.success('Login successful!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if ((registerForm.password || '').length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    const normalizedPhone = normalizePhone(registerForm.phone);
    if (normalizedPhone && normalizedPhone.length !== 10) {
      toast.error('Phone number must be exactly 10 digits');
      return;
    }
    setLoading(true);
    try {
      await register({
        ...registerForm,
        phone: normalizedPhone || '',
      });
      toast.success('Registration successful!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center px-4">
      <Card className="w-full max-w-md p-8 bg-white rounded-2xl shadow-xl" data-testid="auth-card">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-semibold tracking-tight mb-2 font-heading">Welcome to Shadiro</h1>
          <p className="text-stone-600">Plan your dream event with verified vendors</p>
        </div>

        <Tabs defaultValue={location.state?.defaultTab || 'login'} className="w-full">
          <TabsList className="w-full bg-stone-100 p-1 rounded-lg mb-6">
            <TabsTrigger value="login" className="flex-1 rounded-md" data-testid="login-tab">
              Login
            </TabsTrigger>
            <TabsTrigger value="register" className="flex-1 rounded-md" data-testid="register-tab">
              Register
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <Label htmlFor="login-email">Email</Label>
                <Input
                  id="login-email"
                  type="email"
                  placeholder="your@email.com"
                  className="h-12 rounded-lg mt-2"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  required
                  data-testid="login-email-input"
                />
              </div>
              <div>
                <Label htmlFor="login-password">Password</Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder="••••••••"
                  className="h-12 rounded-lg mt-2"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  required
                  data-testid="login-password-input"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90 h-12 rounded-full text-base font-medium"
                disabled={loading}
                data-testid="login-submit-button"
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="register">
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <Label htmlFor="register-name">Full Name</Label>
                <Input
                  id="register-name"
                  type="text"
                  placeholder="John Doe"
                  className="h-12 rounded-lg mt-2"
                  value={registerForm.name}
                  onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                  required
                  data-testid="register-name-input"
                />
              </div>
              <div>
                <Label htmlFor="register-email">Email</Label>
                <Input
                  id="register-email"
                  type="email"
                  placeholder="your@email.com"
                  className="h-12 rounded-lg mt-2"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                  required
                  data-testid="register-email-input"
                />
              </div>
              <div>
                <Label htmlFor="register-phone">Phone</Label>
                <Input
                  id="register-phone"
                  type="tel"
                  placeholder="+91 9876543210"
                  className="h-12 rounded-lg mt-2"
                  value={registerForm.phone}
                  onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                  pattern="[0-9]{10}"
                  maxLength={10}
                  data-testid="register-phone-input"
                />
              </div>
              <div>
                <Label htmlFor="register-password">Password</Label>
                <Input
                  id="register-password"
                  type="password"
                  placeholder="••••••••"
                  className="h-12 rounded-lg mt-2"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                  minLength={8}
                  required
                  data-testid="register-password-input"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-primary hover:bg-primary/90 h-12 rounded-full text-base font-medium"
                disabled={loading}
                data-testid="register-submit-button"
              >
                {loading ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
};

export default AuthPage;
