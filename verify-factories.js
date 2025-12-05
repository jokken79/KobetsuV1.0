const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Login first
    console.log('1. Logging in...');
    await page.goto('http://localhost:3010/login');
    await page.fill('input[type="email"]', 'admin@local.dev');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Check /factories page
    console.log('\n2. Checking /factories page...');
    await page.goto('http://localhost:3010/factories');
    await page.waitForTimeout(3000);

    // Try to get the page title from h1 or any heading
    const pageTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      if (h1) return h1.textContent.trim();

      const h2 = document.querySelector('h2');
      if (h2) return h2.textContent.trim();

      // Check for any text containing 工場
      const allText = document.body.innerText;
      const match = allText.match(/派遣先[^\n]*/);
      return match ? match[0] : 'Not found';
    });

    console.log(`   Page title/heading: ${pageTitle}`);

    // Take screenshot
    await page.screenshot({ path: 'factories-page.png', fullPage: true });
    console.log('   Screenshot saved: factories-page.png');

    console.log('\n3. Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
    console.log('\n✓ Done. Check factories-page.png');
  }
})();
