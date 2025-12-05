const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Opening factories page directly...\n');

    // Go directly to factories (should redirect to login if not authenticated)
    await page.goto('http://localhost:3010/factories', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);

    if (currentUrl.includes('/login')) {
      console.log('✅ Redirected to login (authentication working)');

      // Try to login
      const emailInput = await page.$('input[name="email"]');
      const passwordInput = await page.$('input[name="password"]');

      if (emailInput && passwordInput) {
        console.log('✅ Login form found');
        await page.fill('input[name="email"]', 'admin@local.dev');
        await page.fill('input[name="password"]', 'admin123');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(3000);

        console.log(`After login: ${page.url()}`);
      }
    }

    // Now check factories page
    if (!page.url().includes('/factories')) {
      await page.goto('http://localhost:3010/factories');
      await page.waitForTimeout(3000);
    }

    // Take screenshot
    await page.screenshot({ path: 'factories-check.png', fullPage: true });
    console.log('\n✅ Screenshot saved: factories-check.png');

    console.log('\nKeeping browser open for 20 seconds...');
    await page.waitForTimeout(20000);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
  }
})();
