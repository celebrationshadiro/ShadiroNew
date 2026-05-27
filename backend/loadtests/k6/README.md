# k6 Backend Load Tests

## Folder
- `backend_mix.js`: weighted multi-endpoint load test script
- `.env.example`: sample environment variables
- `output/`: JSON summaries for CI

## Traffic mix
- Vendor listing: 60%
- Booking create: 25%
- Payment confirm: 12%
- Admin: 3%

## Modes
- `steady`: constant arrival-rate load
- `spike`: ramp-up spike profile
- `soak`: long-running sustained load
- `all`: runs all 3 in one run

## Required env vars
- `BASE_URL`
- `USER_TOKEN`
- `ADMIN_TOKEN`
- `BOOKING_VENDOR_ID`
- `PAYMENT_ORDER_ID`
- `RAZORPAY_ORDER_ID`
- `RAZORPAY_PAYMENT_ID`
- `RAZORPAY_SIGNATURE`

## Optional endpoint overrides
- `VENDOR_LIST_PATH` (default `/api/vendors?limit=20`)
- `BOOKING_CREATE_PATH` (default `/api/bookings`)
- `PAYMENT_CONFIRM_PATH` (default `/api/payments/verify`)
- `ADMIN_PATH` (default `/api/admin/analytics`)

## Run examples
```powershell
# steady-state
k6 run backend/loadtests/k6/backend_mix.js `
  -e LOAD_MODE=steady `
  -e BASE_URL=http://127.0.0.1:8000 `
  -e USER_TOKEN=<user_jwt> `
  -e ADMIN_TOKEN=<admin_jwt> `
  -e BOOKING_VENDOR_ID=<vendor_id> `
  -e PAYMENT_ORDER_ID=<order_id> `
  -e RAZORPAY_ORDER_ID=<rzp_order> `
  -e RAZORPAY_PAYMENT_ID=<rzp_payment> `
  -e RAZORPAY_SIGNATURE=<rzp_signature> `
  -e K6_SUMMARY_PATH=backend/loadtests/k6/output/steady_summary.json

# spike
k6 run backend/loadtests/k6/backend_mix.js `
  -e LOAD_MODE=spike `
  -e BASE_URL=http://127.0.0.1:8000 `
  -e USER_TOKEN=<user_jwt> `
  -e ADMIN_TOKEN=<admin_jwt> `
  -e BOOKING_VENDOR_ID=<vendor_id> `
  -e PAYMENT_ORDER_ID=<order_id> `
  -e RAZORPAY_ORDER_ID=<rzp_order> `
  -e RAZORPAY_PAYMENT_ID=<rzp_payment> `
  -e RAZORPAY_SIGNATURE=<rzp_signature> `
  -e K6_SUMMARY_PATH=backend/loadtests/k6/output/spike_summary.json

# soak (configurable duration)
k6 run backend/loadtests/k6/backend_mix.js `
  -e LOAD_MODE=soak `
  -e SOAK_DURATION=4h `
  -e BASE_URL=http://127.0.0.1:8000 `
  -e USER_TOKEN=<user_jwt> `
  -e ADMIN_TOKEN=<admin_jwt> `
  -e BOOKING_VENDOR_ID=<vendor_id> `
  -e PAYMENT_ORDER_ID=<order_id> `
  -e RAZORPAY_ORDER_ID=<rzp_order> `
  -e RAZORPAY_PAYMENT_ID=<rzp_payment> `
  -e RAZORPAY_SIGNATURE=<rzp_signature> `
  -e K6_SUMMARY_PATH=backend/loadtests/k6/output/soak_summary.json
```

## CI-friendly summary
The script writes JSON summary via `handleSummary()`.
Use `K6_SUMMARY_PATH` to control output file path.
