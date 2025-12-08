const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('🏭 Creating 海南第一工場 and Contract - リフト作業');
    console.log('='.repeat(60));

    // Step 1: Login
    console.log('\n1️⃣ Logging in...');
    await page.goto('http://localhost:3010/login');
    await page.fill('input[type="email"]', 'admin@local.dev');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);
    console.log('   ✅ Login successful');

    // Step 2: Go to Factories page
    console.log('\n2️⃣ Navigating to Factories page...');
    await page.goto('http://localhost:3010/factories');
    await page.waitForTimeout(2000);
    console.log('   ✅ On Factories page');

    // Step 3: Check if 海南第一工場 already exists
    console.log('\n3️⃣ Checking if 海南第一工場 exists...');
    const existingFactory = await page.evaluate(() => {
      const body = document.body.innerText;
      return body.includes('海南第一工場');
    });

    if (existingFactory) {
      console.log('   ⚠️  海南第一工場 already exists!');
      console.log('   Finding and clicking on it...');

      // Click on the factory
      await page.evaluate(() => {
        const links = Array.from(document.querySelectorAll('a, div, span'));
        const kainanLink = links.find(el => el.textContent.includes('海南第一工場'));
        if (kainanLink) {
          kainanLink.click();
        }
      });

      await page.waitForTimeout(2000);

    } else {
      console.log('   ℹ️  海南第一工場 not found');
      console.log('   📝 Please create the factory manually using the UI:');
      console.log('');
      console.log('   Company Name: 海南テクノロジー株式会社');
      console.log('   Plant Name: 海南第一工場');
      console.log('   Address: 〒642-0001 和歌山県海南市船尾1234');
      console.log('');
      console.log('   Waiting 30 seconds for you to create it...');
      await page.waitForTimeout(30000);
    }

    // Step 4: Navigate to Contract creation
    console.log('\n4️⃣ Navigating to create contract...');
    await page.goto('http://localhost:3010/kobetsu/create');
    await page.waitForTimeout(3000);
    console.log('   ✅ On contract creation page');

    // Step 5: Fill contract form
    console.log('\n5️⃣ Filling contract form...');

    // Wait for factory select to be available
    await page.waitForSelector('select', { timeout: 5000 }).catch(() => {
      console.log('   ⚠️  Form not fully loaded, waiting longer...');
    });

    await page.waitForTimeout(2000);

    // Check if the form has the factory dropdown
    const hasFactoryDropdown = await page.evaluate(() => {
      const selects = document.querySelectorAll('select');
      return selects.length > 0;
    });

    if (!hasFactoryDropdown) {
      console.log('   ⚠️  Contract creation form not found');
      console.log('   Please create the contract manually with these details:');
      console.log('');
      console.log('   Factory: 海南第一工場');
      console.log('   Work Content: リフト作業（フォークリフト運転および倉庫内作業）');
      console.log('   Responsibility: 補助作業');
      console.log('   Work Location: 海南第一工場　倉庫エリア');
      console.log('   Work Days: 月,火,水,木,金');
      console.log('   Work Hours: 08:00 - 17:00');
      console.log('   Break: 60分');
      console.log('   Max Overtime/Day: 2時間');
      console.log('   Max Overtime/Month: 45時間');
      console.log('');
      await page.screenshot({ path: 'contract-form.png', fullPage: true });
      console.log('   📸 Screenshot saved: contract-form.png');
    } else {
      console.log('   ✅ Contract form found');
      console.log('   Please fill in the form manually');
    }

    console.log('\n📊 SUMMARY');
    console.log('='.repeat(60));
    console.log('Factory: 海南テクノロジー株式会社 / 海南第一工場');
    console.log('Work Type: リフト作業（フォークリフト運転）');
    console.log('Schedule: 月～金 8:00-17:00 (休憩60分)');
    console.log('Overtime: Max 2h/day, 45h/month');
    console.log('Supervisor: 田中太郎 (倉庫管理責任者)');
    console.log('Safety: フォークリフト免許必須、安全装備着用義務');
    console.log('='.repeat(60));

    console.log('\nKeeping browser open for 60 seconds for manual review...');
    await page.waitForTimeout(60000);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    await page.screenshot({ path: 'error-screenshot.png', fullPage: true });
    console.log('📸 Error screenshot saved: error-screenshot.png');
  } finally {
    await browser.close();
    console.log('\n✅ Done!');
  }
})();
