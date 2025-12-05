const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Listen for console messages
  page.on('console', msg => {
    const type = msg.type();
    if (type === 'error' || type === 'warning') {
      console.log(`[${type.toUpperCase()}] ${msg.text()}`);
    }
  });

  // Listen for page errors
  page.on('pageerror', error => {
    console.log('[PAGE ERROR]', error.message);
  });

  // Listen for network responses
  page.on('response', response => {
    if (response.url().includes('/companies')) {
      console.log(`[NETWORK] ${response.status()} ${response.url()}`);
    }
  });

  try {
    // Navigate to login page first
    console.log('Navigating to login page...');
    await page.goto('http://localhost:3010/login');
    await page.waitForLoadState('networkidle');

    // Login (adjust credentials if needed)
    console.log('Logging in...');
    await page.fill('input[type="email"]', 'admin@example.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Navigate to companies page
    console.log('Navigating to companies page...');
    await page.goto('http://localhost:3010/companies');
    await page.waitForTimeout(3000);

    // Check for errors in the page
    const errorElements = await page.$$('[class*="error"]');
    if (errorElements.length > 0) {
      console.log(`Found ${errorElements.length} error elements`);
    }

    console.log('Test complete. Browser will stay open for 30 seconds...');
    await page.waitForTimeout(30000);

  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();
