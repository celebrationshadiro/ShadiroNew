import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import AssistantWidget from './AssistantWidget';
import { useAuth } from '../../contexts/AuthContext';
import { vendorProfile } from '../../lib/api';

const deriveBookingContext = (pathname, stateCtx) => {
  if (stateCtx?.booking_context) return stateCtx.booking_context;
  if (pathname.startsWith('/grocery')) return 'GROCERY';
  if (pathname.includes('/checkout') || pathname.includes('/booking')) return 'SERVICE';
  return undefined;
};

const deriveAddressType = (pathname, bookingContext) => {
  if (bookingContext === 'GROCERY') return 'delivery';
  if (bookingContext === 'SERVICE') return 'event';
  if (pathname.startsWith('/grocery')) return 'delivery';
  return undefined;
};

const deriveEntity = (pathname, params) => {
  const parts = pathname.split('/').filter(Boolean);
  const map = {};
  if (parts[0] === 'vendors' && parts[1]) map.vendor_id = parts[1];
  if (parts[0] === 'grocery' && parts[1] === 'orders' && parts[2]) map.order_id = parts[2];
  if (parts[0] === 'bookings' && parts[1]) map.booking_id = parts[1];
  if (parts[0] === 'quotes' && parts[1]) map.quote_id = parts[1];
  // fallback to params if provided
  return { ...map, ...params };
};

const GlobalAssistant = () => {
  const location = useLocation();
  const params = useParams();
  const { user } = useAuth();
  const [vendor, setVendor] = useState(null);

  const userRole = (user?.role) || 'guest';

  useEffect(() => {
    let isMounted = true;
    const loadVendor = async () => {
      if (!user || user.role !== 'vendor') {
        setVendor(null);
        return;
      }
      try {
        const res = await vendorProfile.getMyVendor();
        if (isMounted) setVendor(res.data);
      } catch {
        if (isMounted) setVendor(null);
      }
    };
    loadVendor();
    return () => { isMounted = false; };
  }, [user]);

  const context = useMemo(() => {
    const booking_context = deriveBookingContext(location.pathname, location.state);
    const current_entity = deriveEntity(location.pathname, params);
    const vendor_type = vendor?.vendor_type || (location.state && location.state.vendor_type);
    const category_slug = vendor?.category_slug || vendor?.category_id;
    const address_type = deriveAddressType(location.pathname, booking_context);
    return {
      user_role: userRole,
      vendor_type,
      category_slug,
      booking_context,
      address_type,
      current_page: location.pathname,
      current_entity,
      vendor,
    };
  }, [location.pathname, location.state, params, userRole, vendor]);

  return (
    <AssistantWidget
      role={userRole === 'admin' ? 'admin' : userRole === 'vendor' ? 'vendor' : 'user'}
      title="Shadiro Assistant"
      context={context}
    />
  );
};

export default GlobalAssistant;
