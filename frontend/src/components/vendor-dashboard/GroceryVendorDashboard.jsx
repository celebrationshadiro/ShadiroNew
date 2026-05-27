import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Package, MessageSquare, TrendingUp, Star } from 'lucide-react';

const formatCurrency = (amount) => {
  const value = Number(amount || 0);
  return `₹${value.toLocaleString('en-IN')}`;
};

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

const GroceryVendorDashboard = ({
  vendor,
  groceryItems,
  groceryOrders,
  groceryLoading,
  newItem,
  earnings,
  payouts,
  payoutAmount,
  payoutSubmitting,
  onNewItemChange,
  onAddItem,
  onUpdateStock,
  onPayoutAmountChange,
  onRequestPayout,
}) => (
  <div className="min-h-screen bg-stone-50">
    <div className="max-w-7xl mx-auto w-full px-4 md:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-4xl md:text-5xl font-semibold tracking-tight mb-2 font-heading">
          Grocery Vendor Dashboard
        </h1>
        <p className="text-lg text-stone-600">Manage items and fulfill grocery orders</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard icon={Package} value={groceryItems.length} label="Active Items" bgColor="bg-primary/10" />
        <StatCard icon={MessageSquare} value={groceryOrders.length} label="Orders" bgColor="bg-secondary/10" />
        <StatCard icon={TrendingUp} value={groceryOrders.filter(o => o.status === 'out_for_delivery').length} label="Out for Delivery" bgColor="bg-accent/10" />
      </div>
      {earnings && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard icon={TrendingUp} value={formatCurrency(earnings.commission_deducted)} label="Commission Deducted" bgColor="bg-amber-100" />
          <StatCard icon={Star} value={formatCurrency(earnings.net_earnings)} label="Net Earnings" bgColor="bg-emerald-100" />
          <StatCard icon={Package} value={formatCurrency(earnings.payout_balance)} label="Payout Balance" bgColor="bg-primary/10" />
          <StatCard icon={MessageSquare} value={formatCurrency(earnings.withdrawn_total)} label="Withdrawn Total" bgColor="bg-secondary/10" />
        </div>
      )}

      <Tabs defaultValue="inventory" className="w-full">
        <TabsList className="w-full justify-start bg-white rounded-xl p-1 mb-8">
          <TabsTrigger value="inventory" className="rounded-lg">Inventory</TabsTrigger>
          <TabsTrigger value="orders" className="rounded-lg">Orders</TabsTrigger>
          <TabsTrigger value="payouts" className="rounded-lg">Payouts</TabsTrigger>
        </TabsList>

        <TabsContent value="inventory">
          <Card className="p-6 bg-white rounded-2xl border border-stone-100 mb-6">
            <h2 className="text-xl font-semibold mb-4">Add Item</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              <Input placeholder="Name" value={newItem.name} onChange={(e) => onNewItemChange({ ...newItem, name: e.target.value })} />
              <Input placeholder="Category" value={newItem.category} onChange={(e) => onNewItemChange({ ...newItem, category: e.target.value })} />
              <Input placeholder="Unit" value={newItem.unit} onChange={(e) => onNewItemChange({ ...newItem, unit: e.target.value })} />
              <Input type="number" placeholder="Price" value={newItem.unit_price} onChange={(e) => onNewItemChange({ ...newItem, unit_price: e.target.value })} />
              <Input type="number" placeholder="Stock" value={newItem.stock_qty} onChange={(e) => onNewItemChange({ ...newItem, stock_qty: e.target.value })} />
            </div>
            <Button className="mt-4" onClick={onAddItem}>Add Item</Button>
          </Card>

          {groceryLoading ? (
            <div className="p-6 text-stone-600">Loading items...</div>
          ) : (
            <div className="space-y-4">
              {groceryItems.map((item) => (
                <Card key={item.id} className="p-4 bg-white rounded-2xl border border-stone-100">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold">{item.name}</p>
                      <p className="text-sm text-stone-500">{item.category || 'Grocery'} / {item.unit} / INR {item.unit_price}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Input type="number" className="w-24" value={item.stock_qty ?? 0} onChange={(e) => onUpdateStock(item.id, e.target.value)} />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="orders">
          {groceryOrders.length === 0 ? (
            <Card className="p-12 text-center bg-white rounded-2xl">
              <p className="text-stone-500">No grocery orders yet.</p>
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
                    <div className="font-semibold">INR {order.total_amount.toLocaleString()}</div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="payouts">
          <Card className="p-6 bg-white rounded-2xl border border-stone-100 mb-6">
            <h2 className="text-xl font-semibold mb-2">Request Payout</h2>
            <p className="text-sm text-stone-600 mb-4">
              Available balance: {formatCurrency(earnings?.payout_balance || 0)} · Withdrawn total: {formatCurrency(earnings?.withdrawn_total || 0)}
            </p>
            <div className="flex flex-col md:flex-row gap-3">
              <Input type="number" placeholder="Enter amount" value={payoutAmount} onChange={(e) => onPayoutAmountChange(e.target.value)} />
              <Button onClick={onRequestPayout} disabled={payoutSubmitting}>
                {payoutSubmitting ? 'Submitting...' : 'Request Payout'}
              </Button>
            </div>
          </Card>
          <Card className="p-6 bg-white rounded-2xl border border-stone-100">
            <h3 className="text-lg font-semibold mb-4">Payout History</h3>
            {payouts.length === 0 ? (
              <p className="text-sm text-stone-500">No payout requests yet.</p>
            ) : (
              <div className="space-y-3">
                {payouts.map((p) => (
                  <div key={p.id} className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <div>
                      <p className="font-medium">{formatCurrency(p.amount)}</p>
                      <p className="text-xs text-stone-500">{new Date(p.requested_at || Date.now()).toLocaleString()}</p>
                    </div>
                    <span className="text-xs uppercase tracking-wide text-stone-600">{p.status}</span>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  </div>
);

export default GroceryVendorDashboard;
