import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGroceryCart } from '../contexts/GroceryCartContext';
import { vendors as vendorsApi } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Minus, Plus, ShoppingBag } from 'lucide-react';

const GroceryCartPage = () => {
  const navigate = useNavigate();
  const { cart, updateQty, removeItem, subtotal } = useGroceryCart();
  const [vendor, setVendor] = useState(null);

  useEffect(() => {
    const loadVendor = async () => {
      if (!cart.vendorId) return;
      try {
        const res = await vendorsApi.getById(cart.vendorId);
        setVendor(res.data || null);
      } catch (e) {
        setVendor(null);
      }
    };
    loadVendor();
  }, [cart.vendorId]);

  if (!cart.items.length) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <Card className="p-10 text-center bg-white rounded-2xl">
          <ShoppingBag className="mx-auto mb-4 text-stone-300" size={48} />
          <p className="text-stone-600">Your cart is empty.</p>
          <Button className="mt-4" onClick={() => navigate('/vendors')}>Browse Grocery Vendors</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <div className="max-w-5xl mx-auto w-full px-4 md:px-8 py-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-semibold">Your Grocery Cart</h1>
            {vendor && <p className="text-stone-500">From {vendor.business_name}</p>}
          </div>
          <Button variant="outline" onClick={() => navigate(-1)}>Continue Shopping</Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[1fr_320px] gap-6">
          <Card className="p-6 bg-white rounded-2xl border border-stone-100">
            <div className="space-y-4">
              {cart.items.map((item) => (
                <div key={item.item_id} className="flex items-center justify-between border-b border-stone-100 pb-4">
                  <div>
                    <p className="font-medium text-stone-900">{item.name}</p>
                    <p className="text-sm text-stone-500">{item.unit} ? ?{item.unit_price}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="icon" onClick={() => updateQty(item.item_id, item.qty - 1)}>
                        <Minus size={14} />
                      </Button>
                      <span className="w-8 text-center">{item.qty}</span>
                      <Button variant="outline" size="icon" onClick={() => updateQty(item.item_id, item.qty + 1)}>
                        <Plus size={14} />
                      </Button>
                    </div>
                    <span className="font-semibold text-stone-900">?{item.total_price.toLocaleString()}</span>
                    <Button variant="ghost" onClick={() => removeItem(item.item_id)} className="text-rose-600">
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6 bg-white rounded-2xl border border-stone-100 h-fit">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
            <div className="flex items-center justify-between text-stone-600 mb-2">
              <span>Subtotal</span>
              <span>?{subtotal.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between text-stone-600 mb-4">
              <span>Delivery</span>
              <span>Calculated at checkout</span>
            </div>
            <div className="border-t border-stone-200 pt-4 flex items-center justify-between text-lg font-semibold">
              <span>Total</span>
              <span>?{subtotal.toLocaleString()}</span>
            </div>
            <Button className="w-full mt-6" onClick={() => navigate('/grocery/checkout')}>
              Proceed to Checkout
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default GroceryCartPage;
