import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

const USER_TOKEN = __ENV.USER_TOKEN || '';
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || '';
const USER_AUTH_SCHEME = __ENV.USER_AUTH_SCHEME || 'Bearer';
const ADMIN_AUTH_SCHEME = __ENV.ADMIN_AUTH_SCHEME || 'Bearer';

const VENDOR_LIST_PATH = __ENV.VENDOR_LIST_PATH || '/api/vendors?limit=20';
const BOOKING_CREATE_PATH = __ENV.BOOKING_CREATE_PATH || '/api/bookings';
const PAYMENT_CONFIRM_PATH = __ENV.PAYMENT_CONFIRM_PATH || '/api/payments/verify';
const ADMIN_PATH = __ENV.ADMIN_PATH || '/api/admin/analytics';

const BOOKING_VENDOR_ID = __ENV.BOOKING_VENDOR_ID || '';
const BOOKING_EVENT_ID = __ENV.BOOKING_EVENT_ID || '';
const BOOKING_EVENT_DATE = __ENV.BOOKING_EVENT_DATE || '2026-12-31';
const BOOKING_CITY = __ENV.BOOKING_CITY || 'Mumbai';
const BOOKING_LOCATION = __ENV.BOOKING_LOCATION || 'Mumbai';

const PAYMENT_ORDER_ID = __ENV.PAYMENT_ORDER_ID || '';
const RAZORPAY_ORDER_ID = __ENV.RAZORPAY_ORDER_ID || '';
const RAZORPAY_PAYMENT_ID = __ENV.RAZORPAY_PAYMENT_ID || '';
const RAZORPAY_SIGNATURE = __ENV.RAZORPAY_SIGNATURE || '';

const MODE = (__ENV.LOAD_MODE || 'all').toLowerCase(); // steady|spike|soak|all

const STEADY_RPS = Number(__ENV.STEADY_RPS || 50);
const STEADY_DURATION = __ENV.STEADY_DURATION || '10m';

const SPIKE_BASE_RPS = Number(__ENV.SPIKE_BASE_RPS || 30);
const SPIKE_PEAK_RPS = Number(__ENV.SPIKE_PEAK_RPS || 180);
const SPIKE_HOLD = __ENV.SPIKE_HOLD || '2m';

const SOAK_RPS = Number(__ENV.SOAK_RPS || 40);
const SOAK_DURATION = __ENV.SOAK_DURATION || '2h';

const RATIOS = {
  vendor_listing: 0.60,
  booking_create: 0.25,
  payment_confirm: 0.12,
  admin: 0.03,
};

function weightedRate(totalRps, ratio) {
  return Math.max(1, Math.floor(totalRps * ratio));
}

function buildSteadyScenarios() {
  return {
    steady_vendor_listing: {
      executor: 'constant-arrival-rate',
      exec: 'vendorListing',
      rate: weightedRate(STEADY_RPS, RATIOS.vendor_listing),
      timeUnit: '1s',
      duration: STEADY_DURATION,
      preAllocatedVUs: 50,
      maxVUs: 200,
      tags: { phase: 'steady', endpoint: 'vendor_listing' },
    },
    steady_booking_create: {
      executor: 'constant-arrival-rate',
      exec: 'bookingCreate',
      rate: weightedRate(STEADY_RPS, RATIOS.booking_create),
      timeUnit: '1s',
      duration: STEADY_DURATION,
      preAllocatedVUs: 40,
      maxVUs: 160,
      tags: { phase: 'steady', endpoint: 'booking_create' },
    },
    steady_payment_confirm: {
      executor: 'constant-arrival-rate',
      exec: 'paymentConfirm',
      rate: weightedRate(STEADY_RPS, RATIOS.payment_confirm),
      timeUnit: '1s',
      duration: STEADY_DURATION,
      preAllocatedVUs: 30,
      maxVUs: 120,
      tags: { phase: 'steady', endpoint: 'payment_confirm' },
    },
    steady_admin: {
      executor: 'constant-arrival-rate',
      exec: 'adminAnalytics',
      rate: weightedRate(STEADY_RPS, RATIOS.admin),
      timeUnit: '1s',
      duration: STEADY_DURATION,
      preAllocatedVUs: 5,
      maxVUs: 20,
      tags: { phase: 'steady', endpoint: 'admin' },
    },
  };
}

function buildSpikeScenarios() {
  const stagesFor = (ratio) => {
    const base = weightedRate(SPIKE_BASE_RPS, ratio);
    const peak = weightedRate(SPIKE_PEAK_RPS, ratio);
    return [
      { target: base, duration: '1m' },
      { target: peak, duration: '30s' },
      { target: peak, duration: SPIKE_HOLD },
      { target: base, duration: '1m' },
    ];
  };

  return {
    spike_vendor_listing: {
      executor: 'ramping-arrival-rate',
      exec: 'vendorListing',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 80,
      maxVUs: 300,
      stages: stagesFor(RATIOS.vendor_listing),
      tags: { phase: 'spike', endpoint: 'vendor_listing' },
    },
    spike_booking_create: {
      executor: 'ramping-arrival-rate',
      exec: 'bookingCreate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 60,
      maxVUs: 240,
      stages: stagesFor(RATIOS.booking_create),
      tags: { phase: 'spike', endpoint: 'booking_create' },
    },
    spike_payment_confirm: {
      executor: 'ramping-arrival-rate',
      exec: 'paymentConfirm',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 40,
      maxVUs: 180,
      stages: stagesFor(RATIOS.payment_confirm),
      tags: { phase: 'spike', endpoint: 'payment_confirm' },
    },
    spike_admin: {
      executor: 'ramping-arrival-rate',
      exec: 'adminAnalytics',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 8,
      maxVUs: 30,
      stages: stagesFor(RATIOS.admin),
      tags: { phase: 'spike', endpoint: 'admin' },
    },
  };
}

function buildSoakScenarios() {
  return {
    soak_vendor_listing: {
      executor: 'constant-arrival-rate',
      exec: 'vendorListing',
      rate: weightedRate(SOAK_RPS, RATIOS.vendor_listing),
      timeUnit: '1s',
      duration: SOAK_DURATION,
      preAllocatedVUs: 70,
      maxVUs: 220,
      tags: { phase: 'soak', endpoint: 'vendor_listing' },
    },
    soak_booking_create: {
      executor: 'constant-arrival-rate',
      exec: 'bookingCreate',
      rate: weightedRate(SOAK_RPS, RATIOS.booking_create),
      timeUnit: '1s',
      duration: SOAK_DURATION,
      preAllocatedVUs: 50,
      maxVUs: 180,
      tags: { phase: 'soak', endpoint: 'booking_create' },
    },
    soak_payment_confirm: {
      executor: 'constant-arrival-rate',
      exec: 'paymentConfirm',
      rate: weightedRate(SOAK_RPS, RATIOS.payment_confirm),
      timeUnit: '1s',
      duration: SOAK_DURATION,
      preAllocatedVUs: 35,
      maxVUs: 140,
      tags: { phase: 'soak', endpoint: 'payment_confirm' },
    },
    soak_admin: {
      executor: 'constant-arrival-rate',
      exec: 'adminAnalytics',
      rate: weightedRate(SOAK_RPS, RATIOS.admin),
      timeUnit: '1s',
      duration: SOAK_DURATION,
      preAllocatedVUs: 6,
      maxVUs: 24,
      tags: { phase: 'soak', endpoint: 'admin' },
    },
  };
}

function scenarioSet() {
  if (MODE === 'steady') return buildSteadyScenarios();
  if (MODE === 'spike') return buildSpikeScenarios();
  if (MODE === 'soak') return buildSoakScenarios();
  return {
    ...buildSteadyScenarios(),
    ...buildSpikeScenarios(),
    ...buildSoakScenarios(),
  };
}

export const options = {
  scenarios: scenarioSet(),
  thresholds: {
    http_req_failed: ['rate<0.01'],

    'http_req_duration{endpoint:vendor_listing}': ['p(95)<500'],
    'http_req_duration{endpoint:booking_create}': ['p(95)<700'],
    'http_req_duration{endpoint:payment_confirm}': ['p(95)<900'],
    'http_req_duration{endpoint:admin}': ['p(95)<1000'],

    'checks{endpoint:vendor_listing}': ['rate>0.99'],
    'checks{endpoint:booking_create}': ['rate>0.99'],
    'checks{endpoint:payment_confirm}': ['rate>0.99'],
    'checks{endpoint:admin}': ['rate>0.99'],
  },
};

function authHeaders(token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `${USER_AUTH_SCHEME} ${token}`;
  return headers;
}

function adminHeaders(token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `${ADMIN_AUTH_SCHEME} ${token}`;
  return headers;
}

export function vendorListing() {
  const res = http.get(`${BASE_URL}${VENDOR_LIST_PATH}`, {
    headers: authHeaders(USER_TOKEN),
    tags: { endpoint: 'vendor_listing' },
  });

  check(
    res,
    {
      'vendor listing status is 200': (r) => r.status === 200,
    },
    { endpoint: 'vendor_listing' }
  );

  sleep(0.2);
}

export function bookingCreate() {
  const payload = {
    user_id: 'ignored-by-server',
    vendor_id: BOOKING_VENDOR_ID,
    event_id: BOOKING_EVENT_ID || undefined,
    event_date: BOOKING_EVENT_DATE,
    event_city: BOOKING_CITY,
    location: BOOKING_LOCATION,
    items: [],
    total_amount: 1000,
  };

  const res = http.post(`${BASE_URL}${BOOKING_CREATE_PATH}`, JSON.stringify(payload), {
    headers: authHeaders(USER_TOKEN),
    tags: { endpoint: 'booking_create' },
  });

  check(
    res,
    {
      'booking create status is 200': (r) => r.status === 200,
    },
    { endpoint: 'booking_create' }
  );

  sleep(0.2);
}

export function paymentConfirm() {
  const form = {
    razorpay_order_id: RAZORPAY_ORDER_ID,
    razorpay_payment_id: RAZORPAY_PAYMENT_ID,
    razorpay_signature: RAZORPAY_SIGNATURE,
    order_id: PAYMENT_ORDER_ID,
  };

  const res = http.post(`${BASE_URL}${PAYMENT_CONFIRM_PATH}`, form, {
    headers: {
      ...(USER_TOKEN ? { Authorization: `${USER_AUTH_SCHEME} ${USER_TOKEN}` } : {}),
    },
    tags: { endpoint: 'payment_confirm' },
  });

  check(
    res,
    {
      'payment confirm status is 200': (r) => r.status === 200,
    },
    { endpoint: 'payment_confirm' }
  );

  sleep(0.2);
}

export function adminAnalytics() {
  const res = http.get(`${BASE_URL}${ADMIN_PATH}`, {
    headers: adminHeaders(ADMIN_TOKEN),
    tags: { endpoint: 'admin' },
  });

  check(
    res,
    {
      'admin analytics status is 200': (r) => r.status === 200,
    },
    { endpoint: 'admin' }
  );

  sleep(0.3);
}

export function handleSummary(data) {
  const summaryPath = __ENV.K6_SUMMARY_PATH || 'backend/loadtests/k6/output/summary.json';
  return {
    [summaryPath]: JSON.stringify(data, null, 2),
    stdout: `\nK6 run complete. Summary written to ${summaryPath}\n`,
  };
}
