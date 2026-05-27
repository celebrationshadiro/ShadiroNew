import React, { Suspense, lazy, memo } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { GroceryCartProvider } from './contexts/GroceryCartContext';
import { Toaster } from './components/ui/sonner';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import VendorOnboardingBanner from './components/VendorOnboardingBanner';
import GlobalAssistant from './components/assistant/GlobalAssistant';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy-loaded pages for performance
const HomePage = lazy(() => import('./pages/HomePage'));
const VendorListPage = lazy(() => import('./pages/VendorListPage'));
const VendorDetailPage = lazy(() => import('./pages/VendorDetailPage'));
const AuthPage = lazy(() => import('./pages/AuthPage'));
const UserDashboard = lazy(() => import('./pages/UserDashboard'));
const VendorDashboard = lazy(() => import('./pages/VendorDashboard'));
const CreateEventPage = lazy(() => import('./pages/CreateEventPage'));
const BookingCheckoutPage = lazy(() => import('./pages/BookingCheckoutPage'));
const ChatListPage = lazy(() => import('./pages/ChatListPage'));
const ChatWindow = lazy(() => import('./pages/ChatWindow'));
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'));
const NotificationListPage = lazy(() => import('./pages/NotificationListPage'));
const AdminLogin = lazy(() => import('./pages/admin/AdminLogin'));
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const AdminVendors = lazy(() => import('./pages/admin/AdminVendors'));
const AdminUsers = lazy(() => import('./pages/admin/AdminUsers'));
const AdminBookings = lazy(() => import('./pages/admin/AdminBookings'));
const AdminOrders = lazy(() => import('./pages/admin/AdminOrders'));
const AdminPayments = lazy(() => import('./pages/admin/AdminPayments'));
const AdminPayouts = lazy(() => import('./pages/admin/AdminPayouts'));
const AdminAuditLogs = lazy(() => import('./pages/admin/AdminAuditLogs'));
const AdminPlatformAuditLogs = lazy(() => import('./pages/admin/AdminPlatformAuditLogs'));
const AdminReport = lazy(() => import('./pages/admin/AdminReport'));
const AdminAutomation = lazy(() => import('./pages/admin/AdminAutomation'));
const VendorRegisterPage = lazy(() => import('./pages/VendorRegisterPage'));
const VendorComparison = lazy(() => import('./pages/VendorComparison'));
const PlannerMode = lazy(() => import('./pages/PlannerMode'));
const AdminEmergencyDashboard = lazy(() => import('./pages/admin/AdminEmergencyDashboard'));
const DesignSystemShowcase = lazy(() => import('./pages/DesignSystemShowcase'));
const CreatePackagePage = lazy(() => import('./pages/CreatePackagePage'));
const EditPackagePage = lazy(() => import('./pages/EditPackagePage'));
const VendorOnboardingPage = lazy(() => import('./pages/VendorOnboardingPage'));
const VendorQuoteRespondPage = lazy(() => import('./pages/VendorQuoteRespondPage'));
const GroceryCartPage = lazy(() => import('./pages/GroceryCartPage'));
const GroceryCheckoutPage = lazy(() => import('./pages/GroceryCheckoutPage'));
const GroceryOrderTrackingPage = lazy(() => import('./pages/GroceryOrderTrackingPage'));
const PlanMyEventPage = lazy(() => import('./pages/PlanMyEvent'));
const DynamicBookingPage = lazy(() => import('./pages/DynamicBookingPage'));
const BookingTrackingPage = lazy(() => import('./pages/BookingTrackingPage'));
const ServiceBookingPage = lazy(() => import('./pages/booking/ServiceBookingPage'));
const RentalBookingPage = lazy(() => import('./pages/booking/RentalBookingPage'));

function RouteFallback() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="h-12 w-12 rounded-full border-2 border-stone-200 border-t-amber-500 animate-spin" aria-label="Loading" />
    </div>
  );
}

const AppContent = memo(function AppContent() {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');
  const isAdminLogin = location.pathname === '/admin/login';
  const isDesignShowcase = location.pathname === '/design-system';

  return (
    <div className="App min-h-screen bg-stone-50 flex flex-col">
      {!isAdmin && !isDesignShowcase && <Navbar />}
      {!isAdmin && !isDesignShowcase && <VendorOnboardingBanner />}
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/vendors" element={<VendorListPage />} />
          <Route path="/packages" element={<VendorListPage />} />
          <Route path="/vendors/:id" element={<VendorDetailPage />} />
          <Route path="/compare" element={<VendorComparison />} />
          <Route path="/plan" element={<PlannerMode />} />
          <Route path="/plan-my-event" element={<PlanMyEventPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/dashboard" element={<UserDashboard />} />
          <Route path="/vendor-dashboard" element={<VendorDashboard />} />
          <Route path="/vendor-onboarding" element={<VendorOnboardingPage />} />
          <Route path="/quotes/:id/respond" element={<VendorQuoteRespondPage />} />
          <Route path="/create-package" element={<CreatePackagePage />} />
          <Route path="/packages/:id/edit" element={<EditPackagePage />} />
          <Route path="/create-event" element={<CreateEventPage />} />
          <Route path="/checkout" element={<BookingCheckoutPage />} />
          <Route path="/grocery/cart" element={<GroceryCartPage />} />
          <Route path="/grocery/checkout" element={<GroceryCheckoutPage />} />
          <Route path="/grocery/orders/:id" element={<GroceryOrderTrackingPage />} />
          <Route path="/book/:vendorId" element={<DynamicBookingPage />} />
          <Route path="/book/:vendorId/service" element={<ServiceBookingPage />} />
          <Route path="/book/:vendorId/rental" element={<RentalBookingPage />} />
          <Route path="/bookings/:bookingId/tracking" element={<BookingTrackingPage />} />
          <Route path="/chats" element={<ChatListPage />} />
          <Route path="/chat/:chatId" element={<ChatWindow />} />
          <Route path="/vendor-register" element={<VendorRegisterPage />} />
          <Route path="/notifications/all" element={<NotificationListPage />} />
          <Route path="/design-system" element={<DesignSystemShowcase />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="emergencies" element={<AdminEmergencyDashboard />} />
            <Route path="vendors" element={<AdminVendors />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="bookings" element={<AdminBookings />} />
            <Route path="orders" element={<AdminOrders />} />
            <Route path="payments" element={<AdminPayments />} />
            <Route path="payouts" element={<AdminPayouts />} />
            <Route path="audit-logs" element={<AdminAuditLogs />} />
            <Route path="platform-audit-logs" element={<AdminPlatformAuditLogs />} />
            <Route path="automation" element={<AdminAutomation />} />
            <Route path="report" element={<AdminReport />} />
          </Route>
        </Routes>
      </main>
      {!isAdmin && !isAdminLogin && !isDesignShowcase && <Footer />}
      <GlobalAssistant />
      <Toaster position="top-right" />
    </div>
  );
});

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <GroceryCartProvider>
          <ErrorBoundary>
            <Suspense fallback={<RouteFallback />}>
              <AppContent />
            </Suspense>
          </ErrorBoundary>
        </GroceryCartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
