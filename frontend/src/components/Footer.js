import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Phone, MapPin, Send } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';

const Footer = () => {
  const [email, setEmail] = useState('');

  const handleSubscribe = (e) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error('Please enter your email');
      return;
    }
    toast.success('Thank you! You will receive updates from Shadiro.');
    setEmail('');
  };

  return (
    <footer className="bg-stone-900 text-stone-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Shadiro Brand */}
          <div className="lg:col-span-2">
            <Link to="/" className="inline-block mb-6">
              <span className="text-3xl font-bold bg-gradient-to-r from-pink-500 to-purple-600 bg-clip-text text-transparent">
                Shadiro
              </span>
            </Link>
            <p className="text-stone-400 text-lg mb-6 max-w-md">
              Your one-stop platform for planning dream events. Connect with verified vendors for weddings, corporate events & celebrations.
            </p>
            <Link to="/vendors">
              <Button className="bg-primary hover:bg-primary/90 text-white rounded-full px-8">
                Start planning your event
              </Button>
            </Link>
            <p className="text-stone-500 text-sm mt-4">Book my event →</p>
          </div>

          {/* Evanza Technologies */}
          <div>
            <h4 className="text-white font-semibold text-lg mb-4">Shadiro Technologies Private Limited</h4>
            <div className="space-y-4">
              <a
                href="https://maps.google.com/?q=5/257A8+Heiley+offices+Kalamassery+Ernakulam"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-start gap-3 hover:text-primary transition-colors"
              >
                <MapPin className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span>5/257A8, Suite No 94B, Boring Road , Rk Society, Near An College, Patna - 800001, Bihar</span>
              </a>
            </div>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold text-lg mb-4">Contact</h4>
            <div className="space-y-4">
              <a
                href="mailto:evanzatechnologies@gmail.com"
                className="flex items-center gap-3 hover:text-primary transition-colors"
              >
                <Mail className="w-5 h-5 flex-shrink-0" />
                Shadiro@gmail.com
              </a>
              <a
                href="tel:+916202968551"
                className="flex items-center gap-3 hover:text-primary transition-colors"
              >
                <Phone className="w-5 h-5 flex-shrink-0" />
                +91 6202968551
              </a>
            </div>

            {/* Email signup */}
            <div className="mt-8">
              <p className="text-white font-medium mb-2">Your email for updates</p>
              <form onSubmit={handleSubscribe} className="flex gap-2">
                <Input
                  type="email"
                  placeholder="Enter your email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-stone-800 border-stone-700 text-white placeholder:text-stone-500 rounded-lg"
                />
                <Button type="submit" size="icon" className="bg-primary hover:bg-primary/90 rounded-lg flex-shrink-0">
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-stone-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-stone-500 text-sm">
            © 2025 Shadiro. All rights reserved.
          </p>
          <p className="text-stone-500 text-sm">
            Design & Developed By{' '}
            <a
              href="https://Shadiro.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Shadiro.com
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
