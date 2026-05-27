import React, { createContext, useContext, useMemo, useState } from 'react';
import { toast } from 'sonner';

const GroceryCartContext = createContext(null);
const STORAGE_KEY = 'shadiro_grocery_cart';

const loadCart = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { vendorId: null, items: [] };
  } catch (e) {
    return { vendorId: null, items: [] };
  }
};

export const GroceryCartProvider = ({ children }) => {
  const [cart, setCart] = useState(loadCart);

  const persist = (next) => {
    setCart(next);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (e) {}
  };

  const addItem = (vendorId, item) => {
    if (!vendorId) return;
    if (cart.vendorId && cart.vendorId !== vendorId && cart.items.length > 0) {
      toast.error('Cart cleared. You can only order from one grocery vendor at a time.');
      persist({ vendorId, items: [] });
    }
    const existing = cart.items.find((i) => i.item_id === item.item_id);
    let nextItems;
    if (existing) {
      nextItems = cart.items.map((i) =>
        i.item_id === item.item_id
          ? { ...i, qty: i.qty + 1, total_price: (i.qty + 1) * i.unit_price }
          : i
      );
    } else {
      nextItems = [...cart.items, { ...item, qty: 1, total_price: item.unit_price }];
    }
    persist({ vendorId, items: nextItems });
  };

  const addBundle = (vendorId, items = []) => {
    if (!Array.isArray(items) || items.length === 0) return;
    let nextCart = cart;
    if (cart.vendorId && cart.vendorId !== vendorId && cart.items.length > 0) {
      toast.error('Cart cleared. You can only order from one grocery vendor at a time.');
      nextCart = { vendorId, items: [] };
    }
    let working = { ...nextCart, vendorId: vendorId, items: [...nextCart.items] };
    items.forEach((itm) => {
      const existing = working.items.find((i) => i.item_id === itm.item_id);
      if (existing) {
        existing.qty += itm.qty || 1;
        existing.total_price = existing.qty * existing.unit_price;
      } else {
        working.items.push({ ...itm, qty: itm.qty || 1, total_price: (itm.qty || 1) * itm.unit_price });
      }
    });
    persist(working);
  };

  const updateQty = (itemId, qty) => {
    if (qty <= 0) {
      removeItem(itemId);
      return;
    }
    const nextItems = cart.items.map((i) =>
      i.item_id === itemId ? { ...i, qty, total_price: qty * i.unit_price } : i
    );
    persist({ ...cart, items: nextItems });
  };

  const removeItem = (itemId) => {
    const nextItems = cart.items.filter((i) => i.item_id !== itemId);
    persist({ ...cart, items: nextItems });
  };

  const clearCart = () => persist({ vendorId: null, items: [] });

  const subtotal = useMemo(
    () => cart.items.reduce((sum, item) => sum + item.total_price, 0),
    [cart.items]
  );

  const value = {
    cart,
    addItem,
    addBundle,
    updateQty,
    removeItem,
    clearCart,
    subtotal,
  };

  return (
    <GroceryCartContext.Provider value={value}>
      {children}
    </GroceryCartContext.Provider>
  );
};

export const useGroceryCart = () => {
  const ctx = useContext(GroceryCartContext);
  if (!ctx) throw new Error('useGroceryCart must be used within GroceryCartProvider');
  return ctx;
};
