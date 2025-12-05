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

async function findKainanFactory(token) {
  try {
    const response = await axios.get(`${API_BASE}/factories`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const factories = response.data;
    console.log(`\n📊 Total factories: ${factories.length}`);

    // Search for 海南第一工場
    const kainan = factories.find(f =>
      f.factory_name && f.factory_name.includes('海南第一工場')
    );

    if (kainan) {
      console.log('\n✅ Found 海南第一工場:');
      console.log(`   ID: ${kainan.id}`);
      console.log(`   Company: ${kainan.company_name}`);
      console.log(`   Factory: ${kainan.factory_name}`);
      console.log(`   Department: ${kainan.department || 'N/A'}`);
      console.log(`   Line: ${kainan.line || 'N/A'}`);
      return kainan;
    } else {
      console.log('\n⚠️  海南第一工場 not found. Available factories:');
      factories.slice(0, 10).forEach(f => {
        console.log(`   - ${f.company_name} / ${f.factory_name}`);
      });
      return null;
    }
  } catch (error) {
    console.error('❌ Failed to fetch factories:', error.response?.data || error.message);
    throw error;
  }
}

async function getAvailableEmployees(token) {
  try {
    const response = await axios.get(`${API_BASE}/employees`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    console.log(`\n👥 Available employees: ${response.data.length}`);

    // Show first 5 active employees
    const activeEmployees = response.data.filter(e => e.status === '在職中');
    console.log(`   Active employees: ${activeEmployees.length}`);

    if (activeEmployees.length > 0) {
      console.log('\n   Sample employees:');
      activeEmployees.slice(0, 5).forEach(e => {
        console.log(`   - ${e.full_name} (${e.employee_number})`);
      });
      return activeEmployees;
    }

    return [];
  } catch (error) {
    console.error('❌ Failed to fetch employees:', error.response?.data || error.message);
    return [];
  }
}

async function createContract(token, factoryId, employeeIds) {
  const today = new Date();
  const startDate = today.toISOString().split('T')[0];
  const endDate = new Date(today.setMonth(today.getMonth() + 3)).toISOString().split('T')[0];

  const contractData = {
    factory_id: factoryId,
    employee_ids: employeeIds,
    contract_start_date: startDate,
    contract_end_date: endDate,
    work_content: 'リフト作業（フォークリフト運転および倉庫内作業）',
    responsibility_level: '補助作業',
    work_location: '海南第一工場　倉庫エリア',
    work_days: ['月', '火', '水', '木', '金'],
    work_start_time: '08:00',
    work_end_time: '17:00',
    break_duration: 60,
    max_overtime_per_day: 2.0,
    max_overtime_per_month: 45.0,
    supervisor_name: '田中太郎',
    supervisor_title: '倉庫管理責任者',
    safety_measures: 'フォークリフト免許確認、安全靴・ヘルメット着用義務、作業前点検実施',
    complaint_contact_name: '人事部　山田花子',
    complaint_contact_phone: '03-1234-5678',
    status: 'active'
  };

  try {
    const response = await axios.post(`${API_BASE}/kobetsu`, contractData, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    console.log('\n✅ CONTRACT CREATED SUCCESSFULLY!');
    console.log(`   Contract Number: ${response.data.contract_number}`);
    console.log(`   Factory: ${response.data.factory?.factory_name}`);
    console.log(`   Work Content: ${response.data.work_content}`);
    console.log(`   Period: ${response.data.contract_start_date} → ${response.data.contract_end_date}`);
    console.log(`   Employees: ${response.data.employee_ids?.length || 0}`);
    console.log(`\n📄 View contract at: http://localhost:3010/kobetsu/${response.data.id}`);

    return response.data;
  } catch (error) {
    console.error('\n❌ Failed to create contract:');
    console.error(error.response?.data || error.message);
    throw error;
  }
}

async function main() {
  console.log('='.repeat(60));
  console.log('🏭 Creating Contract for 海南第一工場 - リフト作業');
  console.log('='.repeat(60));

  try {
    // Step 1: Login
    console.log('\n1️⃣ Logging in...');
    const token = await loginAndGetToken();
    console.log('   ✅ Login successful');

    // Step 2: Find factory
    console.log('\n2️⃣ Searching for 海南第一工場...');
    const factory = await findKainanFactory(token);

    if (!factory) {
      console.log('\n❌ Cannot proceed without factory data.');
      console.log('   Please check if 海南第一工場 exists in the database.');
      return;
    }

    // Step 3: Get employees
    console.log('\n3️⃣ Fetching available employees...');
    const employees = await getAvailableEmployees(token);

    if (employees.length === 0) {
      console.log('\n⚠️  No active employees found. Creating contract without employees.');
      // Proceed with empty employee list
    }

    // Step 4: Create contract
    console.log('\n4️⃣ Creating contract...');
    const employeeIds = employees.length > 0 ? [employees[0].id] : [];

    if (employeeIds.length > 0) {
      console.log(`   Assigning employee: ${employees[0].full_name}`);
    }

    await createContract(token, factory.id, employeeIds);

    console.log('\n' + '='.repeat(60));
    console.log('✅ Contract creation completed successfully!');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('\n' + '='.repeat(60));
    console.error('❌ Error occurred:', error.message);
    console.error('='.repeat(60));
  }
}

main();
