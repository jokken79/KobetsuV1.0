const axios = require('axios');

const API_BASE = 'http://localhost:8010/api/v1';

async function loginAndGetToken() {
  try {
    const response = await axios.post(`${API_BASE}/auth/login`, {
      email: 'admin@local.dev',
      password: 'admin123'
    });
    return response.data.access_token;
  } catch (error) {
    console.error('❌ Login failed:', error.response?.data || error.message);
    throw error;
  }
}

async function createKainanFactory(token) {
  const factoryData = {
    company_name: '海南テクノロジー株式会社',
    factory_name: '海南第一工場',
    department: '物流部',
    line: 'リフト作業',
    company_address: '〒642-0001 和歌山県海南市船尾1234',
    factory_address: '〒642-0001 和歌山県海南市船尾1234',
    work_content: 'フォークリフト運転および倉庫内物流作業。パレット積載、入出庫管理、在庫整理等。',
    work_location: '海南第一工場　倉庫エリア（第1倉庫～第3倉庫）',
    responsibility_level: '補助作業（指示に従った作業実施）',
    safety_measures: '・フォークリフト免許（要資格確認）\n・安全靴、ヘルメット、作業服の着用義務\n・作業前車両点検の実施\n・安全通路の遵守\n・毎朝のKY活動参加',
    supervisor_name: '田中太郎',
    supervisor_title: '倉庫管理責任者',
    supervisor_phone: '073-1234-5678',
    complaint_contact_name: '人事部　山田花子',
    complaint_contact_phone: '073-1234-5679',
    complaint_contact_email: 'hr@kainan-tech.co.jp'
  };

  try {
    console.log('\n📝 Creating factory with data:');
    console.log(`   Company: ${factoryData.company_name}`);
    console.log(`   Factory: ${factoryData.factory_name}`);
    console.log(`   Department: ${factoryData.department}`);
    console.log(`   Line: ${factoryData.line}`);

    const response = await axios.post(`${API_BASE}/factories`, factoryData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    console.log('\n✅ FACTORY CREATED SUCCESSFULLY!');
    console.log(`   Factory ID: ${response.data.id}`);
    console.log(`   Company: ${response.data.company_name}`);
    console.log(`   Factory: ${response.data.factory_name}`);
    console.log(`   Department: ${response.data.department}`);
    console.log(`   Line: ${response.data.line}`);
    console.log(`\n📄 View at: http://localhost:3010/factories/${response.data.id}`);

    return response.data;
  } catch (error) {
    console.error('\n❌ Failed to create factory:');
    if (error.response?.data) {
      console.error('   Error details:', JSON.stringify(error.response.data, null, 2));
    } else {
      console.error('   Error:', error.message);
    }
    throw error;
  }
}

async function createShiftsForFactory(token, factoryId) {
  const shifts = [
    {
      shift_name: '昼勤',
      shift_start: '08:00',
      shift_end: '17:00',
      shift_premium: '0',
      shift_premium_type: '時給',
      description: '通常昼間勤務（8:00～17:00）休憩60分',
      display_order: 1,
      is_active: true
    },
    {
      shift_name: '夜勤',
      shift_start: '20:00',
      shift_end: '05:00',
      shift_premium: '300',
      shift_premium_type: '時給',
      description: '夜間勤務（20:00～翌5:00）深夜割増あり',
      display_order: 2,
      is_active: true
    }
  ];

  console.log('\n📊 Creating shifts for factory...');

  for (const shift of shifts) {
    try {
      const response = await axios.post(
        `${API_BASE}/factories/${factoryId}/shifts`,
        shift,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      console.log(`   ✅ Created shift: ${shift.shift_name}`);
    } catch (error) {
      console.error(`   ⚠️  Failed to create shift ${shift.shift_name}:`, error.response?.data || error.message);
    }
  }
}

async function createBreaksForFactory(token, factoryId) {
  const breaks = [
    {
      break_name: '昼休憩',
      break_start: '12:00',
      break_end: '13:00',
      duration_minutes: 60,
      description: '昼食休憩',
      display_order: 1,
      is_active: true
    },
    {
      break_name: '午前小休憩',
      break_start: '10:00',
      break_end: '10:15',
      duration_minutes: 15,
      description: '午前の小休憩',
      display_order: 2,
      is_active: true
    },
    {
      break_name: '午後小休憩',
      break_start: '15:00',
      break_end: '15:15',
      duration_minutes: 15,
      description: '午後の小休憩',
      display_order: 3,
      is_active: true
    }
  ];

  console.log('\n☕ Creating breaks for factory...');

  for (const breakData of breaks) {
    try {
      const response = await axios.post(
        `${API_BASE}/factories/${factoryId}/breaks`,
        breakData,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      console.log(`   ✅ Created break: ${breakData.break_name}`);
    } catch (error) {
      console.error(`   ⚠️  Failed to create break ${breakData.break_name}:`, error.response?.data || error.message);
    }
  }
}

async function main() {
  console.log('='.repeat(60));
  console.log('🏭 Creating 海南第一工場 Factory Configuration');
  console.log('='.repeat(60));

  try {
    // Step 1: Login
    console.log('\n1️⃣ Logging in...');
    const token = await loginAndGetToken();
    console.log('   ✅ Login successful');

    // Step 2: Create factory
    console.log('\n2️⃣ Creating factory...');
    const factory = await createKainanFactory(token);

    // Step 3: Create shifts
    console.log('\n3️⃣ Creating shifts...');
    await createShiftsForFactory(token, factory.id);

    // Step 4: Create breaks
    console.log('\n4️⃣ Creating breaks...');
    await createBreaksForFactory(token, factory.id);

    console.log('\n' + '='.repeat(60));
    console.log('✅ Factory setup completed successfully!');
    console.log('='.repeat(60));
    console.log(`\n📄 Now you can create contracts using factory ID: ${factory.id}`);
    console.log(`   Run: node create-kainan-contract.js`);

  } catch (error) {
    console.error('\n' + '='.repeat(60));
    console.error('❌ Error occurred:', error.message);
    console.error('='.repeat(60));
  }
}

main();
