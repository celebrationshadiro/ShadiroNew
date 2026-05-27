export const VENDOR_TYPES = {
  SERVICE: 'service_vendor',
  PRODUCT: 'product_vendor',
};

const PRODUCT_CATEGORY_IDS = new Set(['cat-grocery', 'grocery']);
const PRODUCT_VALUES = new Set(['product_vendor', 'product', 'grocery']);
const SERVICE_VALUES = new Set(['service_vendor', 'service']);

export function resolveVendorType(vendor) {
  if (!vendor) return VENDOR_TYPES.SERVICE;
  const explicit = String(vendor.vendor_type || '').toLowerCase();
  if (PRODUCT_CATEGORY_IDS.has(vendor.category_id)) {
    if (explicit && !PRODUCT_VALUES.has(explicit)) {
      console.warn('Vendor type mismatch for grocery category; forcing PRODUCT_VENDOR', vendor);
    }
    return VENDOR_TYPES.PRODUCT;
  }
  if (vendor.category_id) {
    if (PRODUCT_VALUES.has(explicit)) {
      console.warn('Vendor type mismatch for service category; forcing SERVICE_VENDOR', vendor);
    }
    return VENDOR_TYPES.SERVICE;
  }
  if (PRODUCT_VALUES.has(explicit)) {
    return VENDOR_TYPES.PRODUCT;
  }
  if (SERVICE_VALUES.has(explicit)) {
    return VENDOR_TYPES.SERVICE;
  }
  if (!vendor.category_id) {
    console.warn('Vendor type unclear; defaulting to SERVICE_VENDOR', vendor);
  }
  return VENDOR_TYPES.SERVICE;
}

export function isProductVendor(vendor) {
  return resolveVendorType(vendor) === VENDOR_TYPES.PRODUCT;
}
