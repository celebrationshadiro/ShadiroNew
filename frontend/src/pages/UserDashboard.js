import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { events as eventsApi, orders as ordersApi, quotes as quotesApi, groceryApi } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Calendar, ShoppingBag, MessageSquare, Plus } from 'lucide-react';
import { toast } from 'sonner';

const StatCard = ({ icon: Icon, value, label, bgColor }) => (
  <Card className="p-6 bg-white rounded-2xl border border-stone-100">
    <div className="flex items-center gap-4">
      <div className={`w-12 h-12 ${bgColor} rounded-xl flex items-center justify-center`}>
        <Icon className={bgColor.replace('/10', '').replace('bg-', 'text-')} size={24} />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-stone-600 text-sm">{label}</p>
      </div>
    </div>
  </Card>
);

const EventCard = ({ event, onView }) => {
  return (
    <Card className="p-6 bg-white rounded-2xl border border-stone-100 hover:shadow-lg transition-all">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold mb-1">{event.title}</h3>
          <p className="text-stone-500 text-sm capitalize">{event.event_type}</p>
        </div>
        <div className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm font-medium">
          Active
        </div>
      </div>
      <div className="space-y-2 text-sm text-stone-600 mb-4">
        <p><strong>Date:</strong> {event.date}</p>
        {event.location && <p><strong>Location:</strong> {event.location}</p>}
        {event.guest_count && <p><strong>Guests:</strong> {event.guest_count}</p>}
      </div>
      <Button onClick={() => onView(event.id)} variant="outline" className="w-full rounded-lg">
        View Details
      </Button>
    </Card>
  );
};

const OrderCard = ({ order, onView }) => {
  const getStatusColor = (status) => {
    if (status === 'confirmed') return 'bg-green-100 text-green-700';
    if (status === 'pending') return 'bg-yellow-100 text-yellow-700';
    return 'bg-stone-100 text-stone-700';
  };
  const orderId = String(order?.id || order?.booking_id || '');
  const status = String(order?.status || 'pending').toLowerCase();
  const services = Array.isArray(order?.services)
    ? order.services
    : Array.isArray(order?.items)
      ? order.items.map((item) => item?.title).filter(Boolean)
      : [];
  const totalAmount =
    Number(order?.total_amount) ||
    (Number(order?.total_amount_paise || 0) / 100) ||
    Number(order?.amount || 0);

  return (
    <Card className="p-6 bg-white rounded-2xl border border-stone-100">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-xl font-semibold">Order #{orderId.slice(0, 8) || 'NA'}</h3>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
          </div>
          <p className="text-stone-600 mb-2">Services: {services.length ? services.join(', ') : 'N/A'}</p>
          <p className="text-2xl font-bold text-primary">Rs {Number(totalAmount || 0).toLocaleString()}</p>
        </div>
        <Button onClick={() => onView(orderId)} variant="outline" className="rounded-lg" disabled={!orderId}>
          View Details
        </Button>
      </div>
    </Card>
  );
};

const QuoteCard = ({ quote }) => {
  const getStatusColor = (status) => {
    if (status === 'responded') return 'bg-green-100 text-green-700';
    if (status === 'pending') return 'bg-yellow-100 text-yellow-700';
    if (status === 'accepted') return 'bg-blue-100 text-blue-700';
    return 'bg-stone-100 text-stone-700';
  };
  const status = String(quote?.status || 'pending').toLowerCase();
  const requestedServices = Array.isArray(quote?.requested_services) ? quote.requested_services : [];

  return (
    <Card className="p-6 bg-white rounded-2xl border border-stone-100">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-xl font-semibold">Quote Request</h3>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </div>
          </div>
          <p className="text-stone-600 mb-2">Services: {requestedServices.length ? requestedServices.join(', ') : 'N/A'}</p>
          {quote.quoted_price && (
            <p className="text-2xl font-bold text-primary">₹{quote.quoted_price.toLocaleString()}</p>
          )}
        </div>
      </div>
    </Card>
  );
};

const extractList = (response) => {
  const payload = response?.data?.data ?? response?.data ?? response;
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.bookings)) return payload.bookings;
  if (Array.isArray(payload?.orders)) return payload.orders;
  return [];
};

const UserDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [orders, setOrders] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [groceryOrders, setGroceryOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [eventsRes, ordersRes, quotesRes, groceryRes] = await Promise.all([
        eventsApi.getAll(),
        ordersApi.getAll(),
        quotesApi.getAll(),
        groceryApi.listOrders(),
      ]);
      setEvents(extractList(eventsRes));
      setOrders(extractList(ordersRes));
      setQuotes(extractList(quotesRes));
      setGroceryOrders(extractList(groceryRes));
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) {
      navigate('/auth');
      return;
    }
    loadDashboardData();
  }, [user, navigate, loadDashboardData]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500 text-lg">Loading dashboard...</p>
      </div>
    );
  }
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-stone-500 text-lg">Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-2 font-heading">
            Welcome back, {user.name}!
          </h1>
          <p className="text-lg text-stone-600">Manage your events and bookings</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard icon={Calendar} value={events.length} label="Active Events" bgColor="bg-primary/10" />
          <StatCard icon={ShoppingBag} value={orders.length} label="Total Bookings" bgColor="bg-secondary/10" />
          <StatCard icon={MessageSquare} value={quotes.length} label="Quote Requests" bgColor="bg-accent/10" />
        </div>

        <Tabs defaultValue="events" className="w-full">
          <TabsList className="w-full justify-start bg-white rounded-xl p-1 mb-8">
            <TabsTrigger value="events" className="rounded-lg">My Events</TabsTrigger>
            <TabsTrigger value="bookings" className="rounded-lg">Bookings</TabsTrigger>
            <TabsTrigger value="quotes" className="rounded-lg">Quotes</TabsTrigger>
            <TabsTrigger value="grocery" className="rounded-lg">Grocery Orders</TabsTrigger>
          </TabsList>

          <TabsContent value="events">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold">My Events</h2>
              <Button
                onClick={() => navigate('/create-event')}
                className="bg-primary hover:bg-primary/90 rounded-full"
              >
                <Plus size={18} className="mr-2" /> Create Event
              </Button>
            </div>

            {events.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <Calendar className="mx-auto mb-4 text-stone-300" size={48} />
                <p className="text-stone-500 mb-4">No events yet</p>
                <Button onClick={() => navigate('/create-event')} className="bg-primary hover:bg-primary/90 rounded-full">
                  Create Your First Event
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {events.map((event) => (
                  <EventCard key={event.id} event={event} onView={(id) => navigate(`/events/${id}`)} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="bookings">
            <h2 className="text-2xl font-semibold mb-6">My Bookings</h2>
            {orders.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <ShoppingBag className="mx-auto mb-4 text-stone-300" size={48} />
                <p className="text-stone-500">No bookings yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {orders.map((order) => (
                  <OrderCard key={order.id} order={order} onView={(id) => navigate(`/orders/${id}`)} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="quotes">
            <h2 className="text-2xl font-semibold mb-6">Quote Requests</h2>
            {quotes.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <MessageSquare className="mx-auto mb-4 text-stone-300" size={48} />
                <p className="text-stone-500">No quote requests yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {quotes.map((quote) => (
                  <QuoteCard key={quote.id} quote={quote} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="grocery">
            <h2 className="text-2xl font-semibold mb-6">Grocery Orders</h2>
            {groceryOrders.length === 0 ? (
              <Card className="p-12 text-center bg-white rounded-2xl">
                <p className="text-stone-500">No grocery orders yet</p>
              </Card>
            ) : (
              <div className="space-y-4">
                {groceryOrders.map((order) => (
                  <Card key={order.id} className="p-6 bg-white rounded-2xl border border-stone-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">Order #{order.id.slice(0, 8)}</p>
                        <p className="text-sm text-stone-500">Status: {order.status}</p>
                      </div>
                      <Button variant="outline" onClick={() => navigate(`/grocery/orders/${order.id}`)}>Track</Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default UserDashboard;

