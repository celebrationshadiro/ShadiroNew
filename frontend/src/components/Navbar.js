import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useGroceryCart } from '../contexts/GroceryCartContext';
import { Button } from './ui/button';
import { Menu, X, User, LogOut, LayoutDashboard, Shield, Store, ShoppingCart } from 'lucide-react';
import NotificationCenter from './NotificationCenter';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { cart } = useGroceryCart();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-white border-b border-stone-200 sticky top-0 z-50" data-testid="navbar">
      <div className="max-w-7xl mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center" data-testid="logo-link">
            <span className="text-2xl font-bold font-heading bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
              Shadiro
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/vendors" className="text-stone-600 hover:text-primary transition-colors" data-testid="vendors-link">
              Browse Vendors
            </Link>
            <Link to="/packages" className="text-stone-600 hover:text-primary transition-colors" data-testid="packages-link">
              Packages
            </Link>
            <Link to="/vendor-register" className="text-stone-600 hover:text-primary transition-colors">
              Become a Vendor
            </Link>
            {user?.role === 'admin' && (
              <Link to="/admin" className="text-stone-600 hover:text-primary transition-colors flex items-center gap-1">
                <Shield size={16} /> Admin
              </Link>
            )}

            {user && <NotificationCenter userId={user.id} />}

            {cart.items.length > 0 && (
              <Link to="/grocery/cart" className="relative text-stone-600 hover:text-primary transition-colors">
                <ShoppingCart size={18} />
                <span className="absolute -top-2 -right-2 bg-primary text-white text-xs rounded-full px-1.5">
                  {cart.items.length}
                </span>
              </Link>
            )}

            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 h-10 rounded-lg"
                    data-testid="user-menu-button"
                  >
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                      <User size={16} className="text-primary" />
                    </div>
                    <span>{user.name}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem 
                    onClick={() => navigate(user.role === 'vendor' ? '/vendor-dashboard' : '/dashboard')} 
                    data-testid="dashboard-menu-item"
                  >
                    <LayoutDashboard size={16} className="mr-2" />
                    Dashboard
                  </DropdownMenuItem>
                  {user.role === 'admin' && (
                    <DropdownMenuItem onClick={() => navigate('/admin')}>
                      <Shield size={16} className="mr-2" />
                      Admin Panel
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem onClick={handleLogout} data-testid="logout-menu-item">
                    <LogOut size={16} className="mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button
                onClick={() => navigate('/auth')}
                className="bg-primary hover:bg-primary/90 h-10 px-6 rounded-full"
                data-testid="login-button"
              >
                Login
              </Button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2"
            data-testid="mobile-menu-button"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-stone-200" data-testid="mobile-menu">
            <div className="flex flex-col gap-4">
              <Link
                to="/vendors"
                className="text-stone-600 hover:text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Browse Vendors
              </Link>
              <Link
                to="/packages"
                className="text-stone-600 hover:text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Packages
              </Link>
              <Link
                to="/vendor-register"
                className="text-stone-600 hover:text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                Become a Vendor
              </Link>
              {user?.role === 'admin' && (
                <Link
                  to="/admin"
                  className="text-stone-600 hover:text-primary transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Admin Panel
                </Link>
              )}
              {user ? (
                <>
                  <Link
                    to={user.role === 'vendor' ? '/vendor-dashboard' : '/dashboard'}
                    className="text-stone-600 hover:text-primary transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Dashboard
                  </Link>
                  <button
                    onClick={() => {
                      handleLogout();
                      setMobileMenuOpen(false);
                    }}
                    className="text-left text-stone-600 hover:text-primary transition-colors"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Button
                  onClick={() => {
                    navigate('/auth');
                    setMobileMenuOpen(false);
                  }}
                  className="bg-primary hover:bg-primary/90 h-10 rounded-full w-full"
                >
                  Login
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
