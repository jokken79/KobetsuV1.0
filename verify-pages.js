const { chromium } = require('playwright');
const fs = require('fs');

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

    // Check /companies page
    console.log('\n2. Checking /companies page...');
    await page.goto('http://localhost:3010/companies');
    await page.waitForTimeout(2000);

    const companiesTitle = await page.$eval('h1', el => el.textContent);
    const companiesCount = await page.$$eval('[class*="企業"]', els => els.length);
    console.log(`   Title: ${companiesTitle}`);
    console.log(`   Elements with 企業: ${companiesCount}`);

    // Take screenshot
    await page.screenshot({ path: 'companies-page.png', fullPage: true });
    console.log('   Screenshot saved: companies-page.png');

    // Check /factories page
    console.log('\n3. Checking /factories page...');
    await page.goto('http://localhost:3010/factories');
    await page.waitForTimeout(2000);

    const factoriesTitle = await page.textContent('nav[aria-label="breadcrumb"]');
    console.log(`   Breadcrumb: ${factoriesTitle}`);

    // Take screenshot
    await page.screenshot({ path: 'factories-page.png', fullPage: true });
    console.log('   Screenshot saved: factories-page.png');

    // Compare
    console.log('\n4. VERIFICATION RESULTS:');
    console.log('   ========================');
    console.log(`   /companies title: ${companiesTitle}`);
    console.log(`   /factories breadcrumb: ${factoriesTitle}`);

    if (companiesTitle.includes('派遣先企業') && factoriesTitle.includes('派遣先工場')) {
      console.log('   ✅ CORRECT: Both pages have different titles');
    } else {
      console.log('   ❌ ERROR: Pages may have same or incorrect titles');
    }

    console.log('\n5. Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
    console.log('\n✓ Done. Check companies-page.png and factories-page.png');
  }
})();
