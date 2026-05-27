import type { Metadata } from 'next';
import { Playfair_Display, DM_Sans } from 'next/font/google';
import Script from 'next/script';
import React from 'react';
import '../src/index.css'; // Leverage existing global CSS configurations

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-playfair',
  weight: ['400', '600', '700'],
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dmsans',
  weight: ['400', '500', '700'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'Shadiro | Premium Multi-Vendor Event Planner & Grocery Marketplace',
    template: '%s | Shadiro',
  },
  description: 'Connect with verified event professionals, plan wedding budgets, and order fresh local groceries with Shadiro multi-vendor platform.',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://shadiro.com'),
  alternates: {
    canonical: './',
  },
  openGraph: {
    type: 'website',
    locale: 'en_IN',
    url: 'https://shadiro.com',
    siteName: 'Shadiro',
    title: 'Shadiro | Premium Multi-Vendor Event Planner & Grocery Marketplace',
    description: 'Connect with verified event professionals, plan wedding budgets, and order fresh local groceries.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const gaId = process.env.NEXT_PUBLIC_GA_ID;

  return (
    <html lang="en" className={`${playfair.variable} ${dmSans.variable}`}>
      <body className="font-sans antialiased bg-stone-50 text-stone-900 min-h-screen flex flex-col">
        {gaId && (
          <>
            <Script
              src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`}
              strategy="afterInteractive"
            />
            <Script id="google-analytics" strategy="afterInteractive">
              {`
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${gaId}', {
                  page_path: window.location.pathname,
                });
              `}
            </Script>
          </>
        )}
        <header className="w-full bg-white border-b border-stone-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <a href="/" className="font-serif text-2xl font-bold text-pink-600" aria-label="Shadiro Homepage">
              Shadiro
            </a>
            <nav className="flex space-x-6">
              <a href="/vendors" className="text-stone-600 hover:text-pink-600 font-medium transition" aria-label="Browse Vendors">
                Browse Vendors
              </a>
              <a href="/grocery" className="text-stone-600 hover:text-pink-600 font-medium transition" aria-label="Order Grocery">
                Grocery Catalog
              </a>
              <a href="/dashboard" className="text-stone-600 hover:text-pink-600 font-medium transition" aria-label="User Dashboard">
                My Account
              </a>
            </nav>
          </div>
        </header>

        <main className="flex-grow flex flex-col">
          {children}
        </main>

        <footer className="w-full bg-stone-900 text-stone-400 py-12 mt-auto border-t border-stone-800">
          <div className="max-w-7xl mx-auto px-4 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <span className="font-serif text-xl font-bold text-white mb-4 block">Shadiro</span>
              <p className="text-sm">
                Premium multi-vendor event marketplace connecting clients with verified wedding planners and local suppliers.
              </p>
            </div>
            <div>
              <span className="text-white font-bold mb-4 block">Event Categories</span>
              <ul className="space-y-2 text-sm">
                <li><a href="/vendors/mumbai/venue" className="hover:text-white transition">Banquet Venues</a></li>
                <li><a href="/vendors/mumbai/photography" className="hover:text-white transition">Photography</a></li>
                <li><a href="/vendors/mumbai/catering" className="hover:text-white transition">Catering Services</a></li>
              </ul>
            </div>
            <div>
              <span className="text-white font-bold mb-4 block">Contact Support</span>
              <p className="text-sm">
                Email: support@shadiro.com<br />
                Phone: +91 99999 99999
              </p>
            </div>
          </div>
          <div className="max-w-7xl mx-auto px-4 mt-8 pt-8 border-t border-stone-850 text-center text-xs">
            &copy; {new Date().getFullYear()} Shadiro Technologies Private Limited. All rights reserved.
          </div>
        </footer>
      </body>
    </html>
  );
}
