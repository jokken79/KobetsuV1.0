const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  const results = {
    homepage: {},
    companies: {},
    factories: {},
    login: {},
    errors: []
  };

  try {
    console.log('=== VERIFICACIÓN COMPLETA DEL SISTEMA ===\n');

    // 1. Check Homepage
    console.log('1. HOMEPAGE (/)...');
    await page.goto('http://localhost:3010/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const homepageTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      return h1 ? h1.textContent.trim() : 'Not found';
    });

    const quickActionsCount = await page.evaluate(() => {
      const actions = document.querySelectorAll('[href*="/"]');
      return actions.length;
    });

    // Check if Building icon exists in quick actions
    const hasBuildingIcon = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('派遣先企業');
    });

    results.homepage = {
      title: homepageTitle,
      quickActionsCount,
      hasBuildingIcon,
      url: page.url(),
      status: 'loaded'
    };

    console.log(`   ✅ Title: "${homepageTitle}"`);
    console.log(`   ✅ Quick actions: ${quickActionsCount}`);
    console.log(`   ✅ Building icon present: ${hasBuildingIcon}`);

    await page.screenshot({ path: 'screenshots/01-homepage.png', fullPage: true });
    console.log('   📸 Screenshot saved: 01-homepage.png\n');

    // 2. Check Companies Page
    console.log('2. COMPANIES PAGE (/companies)...');
    await page.goto('http://localhost:3010/companies', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const companiesTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      return h1 ? h1.textContent.trim() : 'Not found';
    });

    const companiesCount = await page.evaluate(() => {
      // Count company cards or list items
      const items = document.querySelectorAll('[class*="cursor-pointer"]');
      return items.length;
    });

    const companiesHasIndigo = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('indigo') || body.includes('bg-blue');
    });

    results.companies = {
      title: companiesTitle,
      count: companiesCount,
      hasIndigoTheme: companiesHasIndigo,
      url: page.url(),
      status: 'loaded'
    };

    console.log(`   ✅ Title: "${companiesTitle}"`);
    console.log(`   ✅ Companies count: ${companiesCount}`);
    console.log(`   ✅ Indigo theme: ${companiesHasIndigo}`);

    await page.screenshot({ path: 'screenshots/02-companies.png', fullPage: true });
    console.log('   📸 Screenshot saved: 02-companies.png\n');

    // 3. Check Factories Page
    console.log('3. FACTORIES PAGE (/factories)...');
    await page.goto('http://localhost:3010/factories', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    const factoriesTitle = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      if (h1) return h1.textContent.trim();

      const breadcrumb = document.querySelector('nav[aria-label="breadcrumb"]');
      if (breadcrumb) return breadcrumb.textContent.trim();

      return 'Not found';
    });

    const factoriesTreeVisible = await page.evaluate(() => {
      // Check if FactoryTree is visible
      const tree = document.querySelector('[class*="FactoryTree"]') ||
                   document.querySelector('input[placeholder*="検索"]');
      return !!tree;
    });

    const factoriesHasIndigo = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('indigo') || body.includes('bg-blue');
    });

    const syncButtonVisible = await page.evaluate(() => {
      const syncBtn = Array.from(document.querySelectorAll('button')).find(btn =>
        btn.textContent.includes('社員') || btn.textContent.includes('工場同期')
      );
      return !!syncBtn;
    });

    results.factories = {
      title: factoriesTitle,
      treeVisible: factoriesTreeVisible,
      hasIndigoTheme: factoriesHasIndigo,
      syncButtonVisible,
      url: page.url(),
      status: 'loaded'
    };

    console.log(`   ✅ Title: "${factoriesTitle}"`);
    console.log(`   ✅ Factory tree visible: ${factoriesTreeVisible}`);
    console.log(`   ✅ Indigo theme: ${factoriesHasIndigo}`);
    console.log(`   ✅ Sync button visible: ${syncButtonVisible}`);

    await page.screenshot({ path: 'screenshots/03-factories.png', fullPage: true });
    console.log('   📸 Screenshot saved: 03-factories.png\n');

    // 4. Click on a factory to see details
    console.log('4. FACTORY DETAILS...');
    const factoryClicked = await page.evaluate(() => {
      const firstFactory = document.querySelector('[class*="cursor-pointer"]');
      if (firstFactory) {
        firstFactory.click();
        return true;
      }
      return false;
    });

    if (factoryClicked) {
      await page.waitForTimeout(2000);

      const detailsVisible = await page.evaluate(() => {
        const details = document.querySelector('[class*="会社情報"]') ||
                       document.querySelector('h2');
        return !!details;
      });

      console.log(`   ✅ Factory clicked: ${factoryClicked}`);
      console.log(`   ✅ Details visible: ${detailsVisible}`);

      await page.screenshot({ path: 'screenshots/04-factory-details.png', fullPage: true });
      console.log('   📸 Screenshot saved: 04-factory-details.png\n');
    }

    // 5. Check Sidebar Navigation
    console.log('5. SIDEBAR NAVIGATION...');
    const sidebarItems = await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll('nav a, aside a'));
      return items.map(item => ({
        text: item.textContent.trim(),
        href: item.getAttribute('href')
      })).filter(item => item.text && item.href);
    });

    const hasBothPages = sidebarItems.some(item => item.text.includes('派遣先企業')) &&
                        sidebarItems.some(item => item.text.includes('派遣先工場'));

    console.log(`   ✅ Sidebar items found: ${sidebarItems.length}`);
    console.log(`   ✅ Has both 企業 and 工場: ${hasBothPages}`);
    console.log('   Sidebar items:');
    sidebarItems.slice(0, 10).forEach(item => {
      console.log(`      - ${item.text} (${item.href})`);
    });

    // 6. Console Errors Check
    console.log('\n6. CONSOLE ERRORS CHECK...');
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      consoleErrors.push(error.message);
    });

    // Navigate one more time to catch any errors
    await page.goto('http://localhost:3010/');
    await page.waitForTimeout(2000);

    console.log(`   ${consoleErrors.length === 0 ? '✅' : '❌'} Console errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('   Errors:');
      consoleErrors.slice(0, 5).forEach(err => console.log(`      - ${err}`));
    }

    results.errors = consoleErrors;

    // 7. Network Check
    console.log('\n7. API HEALTH CHECK...');
    const apiHealthy = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:3010/api/v1/health');
        return response.ok;
      } catch {
        return false;
      }
    });

    console.log(`   ${apiHealthy ? '✅' : '❌'} Backend API: ${apiHealthy ? 'Healthy' : 'Unreachable'}`);

    // Final Summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 RESUMEN FINAL');
    console.log('='.repeat(50));
    console.log(`✅ Homepage: ${results.homepage.status}`);
    console.log(`✅ Companies: ${results.companies.status} (${results.companies.count} companies)`);
    console.log(`✅ Factories: ${results.factories.status}`);
    console.log(`${results.errors.length === 0 ? '✅' : '❌'} Console errors: ${results.errors.length}`);
    console.log(`${apiHealthy ? '✅' : '❌'} Backend API: ${apiHealthy ? 'Healthy' : 'Unreachable'}`);
    console.log(`${hasBothPages ? '✅' : '❌'} Sidebar: Both pages visible`);

    // Save detailed results
    fs.writeFileSync('verification-complete-results.json', JSON.stringify(results, null, 2));
    console.log('\n📄 Detailed results saved to: verification-complete-results.json');

    console.log('\n⏱️  Keeping browser open for 20 seconds for manual inspection...');
    await page.waitForTimeout(20000);

  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    results.errors.push(error.message);
  } finally {
    await browser.close();
    console.log('\n✓ Verification complete. Check screenshots/ folder for visual proof.');
  }
})();
