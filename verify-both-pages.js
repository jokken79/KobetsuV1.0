const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    companies: {},
    factories: {}
  };

  try {
    // Login first
    console.log('1. Logging in...');
    await page.goto('http://localhost:3010/login');
    await page.fill('input[type="email"]', 'admin@local.dev');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    console.log('   ✅ Login successful');

    // Check /companies page
    console.log('\n2. Checking /companies page...');
    await page.goto('http://localhost:3010/companies');
    await page.waitForTimeout(3000);

    const companiesTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      return h1 ? h1.textContent.trim() : 'Not found';
    });

    const companiesCount = await page.evaluate(() => {
      // Count company items in the list
      const items = document.querySelectorAll('[class*="cursor-pointer"]');
      return items.length;
    });

    results.companies = {
      title: companiesTitle,
      count: companiesCount,
      url: page.url()
    };

    console.log(`   Title: "${companiesTitle}"`);
    console.log(`   Companies count: ${companiesCount}`);
    console.log(`   URL: ${page.url()}`);

    // Take screenshot
    await page.screenshot({ path: 'companies-page-final.png', fullPage: true });
    console.log('   Screenshot: companies-page-final.png');

    // Check /factories page
    console.log('\n3. Checking /factories page...');
    await page.goto('http://localhost:3010/factories');
    await page.waitForTimeout(3000);

    const factoriesTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      if (h1) return h1.textContent.trim();

      const breadcrumb = document.querySelector('nav[aria-label="breadcrumb"]');
      if (breadcrumb) return breadcrumb.textContent.trim();

      return 'Not found';
    });

    const factoriesCount = await page.evaluate(() => {
      // Count factories in the tree
      const factoryItems = document.querySelectorAll('[class*="text-sm"]');
      return factoryItems.length;
    });

    // Check for indigo styling
    const hasIndigoStyling = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('indigo') || body.includes('bg-blue-50');
    });

    results.factories = {
      title: factoriesTitle,
      count: factoriesCount,
      hasIndigoStyling,
      url: page.url()
    };

    console.log(`   Title: "${factoriesTitle}"`);
    console.log(`   Factory items visible: ${factoriesCount}`);
    console.log(`   Has indigo styling: ${hasIndigoStyling ? '✅' : '❌'}`);
    console.log(`   URL: ${page.url()}`);

    // Take screenshot
    await page.screenshot({ path: 'factories-page-final.png', fullPage: true });
    console.log('   Screenshot: factories-page-final.png');

    // Final comparison
    console.log('\n4. VERIFICATION RESULTS:');
    console.log('   ========================');
    console.log(`   Companies page title: "${results.companies.title}"`);
    console.log(`   Companies count: ${results.companies.count}`);
    console.log(`   Factories page title: "${results.factories.title}"`);
    console.log(`   Factories has indigo: ${results.factories.hasIndigoStyling ? '✅' : '❌'}`);

    const success =
      results.companies.title.includes('企業') &&
      results.companies.count > 0 &&
      results.factories.title.length > 0 &&
      results.factories.hasIndigoStyling;

    if (success) {
      console.log('\n   ✅ SUCCESS: Both pages are working correctly!');
    } else {
      console.log('\n   ⚠️  WARNING: Some checks failed');
    }

    // Save results to JSON
    fs.writeFileSync('verification-results.json', JSON.stringify(results, null, 2));
    console.log('\n   Results saved to: verification-results.json');

    console.log('\n5. Keeping browser open for 15 seconds for manual inspection...');
    await page.waitForTimeout(15000);

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
    console.log('\n✓ Done. Check companies-page-final.png and factories-page-final.png');
  }
})();
