import { test, expect } from '@playwright/test';

test.describe('Shadiro Enterprise Core Workflows', () => {
  
  test('Authentication: Login with all roles', async ({ page }) => {
    const roles = [
      { email: 'superadmin@shadiro.com', expectedUrl: '/admin/dashboard' },
      { email: 'vendor@shadiro.com', expectedUrl: '/vendor/dashboard' },
      { email: 'customer@shadiro.com', expectedUrl: '/' },
    ];

    for (const role of roles) {
      await page.goto('/login');
      await page.fill('input[name="email"]', role.email);
      await page.fill('input[name="password"]', 'Test@1234');
      await page.click('button[type="submit"]');
      
      // Validate RBAC redirection
      await expect(page).toHaveURL(new RegExp(role.expectedUrl));
      await page.locator('button:has-text("Logout")').click();
    }
  });

  test('Customer Flow: Search, Filter, and Book a Service', async ({ page }) => {
    // 1. Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'customer@shadiro.com');
    await page.fill('input[name="password"]', 'Test@1234');
    await page.click('button[type="submit"]');

    // 2. Search & Filter
    await page.goto('/services');
    await page.fill('input[placeholder*="Search"]', 'Photography');
    await page.selectOption('select[name="city"]', 'Mumbai');
    await page.click('button:has-text("Apply Filters")');
    
    // 3. Select and Book
    await page.locator('.service-card').first().click();
    await page.click('button:has-text("Book Now")');
    
    // 4. Fill Event Details
    await page.fill('input[name="event_date"]', '2026-10-15');
    await page.fill('textarea[name="requirements"]', 'E2E Testing automated booking requirement.');
    await page.click('button:has-text("Proceed to Payment")');

    // 5. Assert Checkout Render
    await expect(page.locator('text=Order Summary')).toBeVisible();
  });

  test('Vendor Flow: Dashboard Analytics Render', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'vendor@shadiro.com');
    await page.fill('input[name="password"]', 'Test@1234');
    await page.click('button[type="submit"]');

    // Verify Analytics charts loaded (not empty)
    await expect(page.locator('.revenue-chart')).toBeVisible();
    await expect(page.locator('text=Total Earnings')).toBeVisible();
    await expect(page.locator('text=Recent Bookings')).toBeVisible();
  });

  test('Admin Flow: Moderation and Analytics', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'superadmin@shadiro.com');
    await page.fill('input[name="password"]', 'Test@1234');
    await page.click('button[type="submit"]');

    // Check Admin Dashboard Loads
    await expect(page.locator('text=Platform Overview')).toBeVisible();
    
    // Navigate to Users and Ban a Vendor
    await page.click('a:has-text("User Management")');
    await page.locator('.user-row:has-text("vendor")').first().locator('button:has-text("Suspend")').click();
    await expect(page.locator('text=User suspended successfully')).toBeVisible();
  });

  test('Security: RBAC Bypass Attempt Fails', async ({ page }) => {
    // Login as Customer
    await page.goto('/login');
    await page.fill('input[name="email"]', 'customer@shadiro.com');
    await page.fill('input[name="password"]', 'Test@1234');
    await page.click('button[type="submit"]');

    // Attempt to access Admin Route directly
    await page.goto('/admin/dashboard');
    
    // Should be redirected or shown 403 Access Denied
    await expect(page.locator('text=Access Denied').or(page.locator('text=Unauthorized'))).toBeVisible();
  });

  test('System Flow: Mock Razorpay Payment Completion', async ({ request }) => {
    // Trigger backend mock directly to simulate async payment fulfillment
    const response = await request.post('/mocks/trigger-razorpay-webhook', {
      data: {
        order_id: 'order_testing123',
        amount: 50000
      }
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('simulated');
  });
});