import React, { useState, useEffect } from 'react';
import { Calendar, Users, Building2, Clock, DollarSign, AlertTriangle, ChevronDown, ChevronRight, Check, X, FileText, BarChart3 } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════
// UNS 勤怠管理システム - Complete React Application
// ═══════════════════════════════════════════════════════════════

const API_BASE = 'http://localhost:8080/api';

// Sample data for demo (when API is not available)
const DEMO_DATA = {
  dashboard: {
    employees: { total: 50, active: 48, visa_expiring: 5 },
    by_company: [
      { company_name: '加藤木材工業株式会社', plant_name: '本社工場', count: 18 },
      { company_name: '加藤木材工業株式会社', plant_name: '春日井工場', count: 7 },
      { company_name: '高雄工業株式会社', plant_name: '岡山工場', count: 10 },
      { company_name: 'コーリツ株式会社', plant_name: '本社工場', count: 7 },
      { company_name: 'ユアサ工機株式会社', plant_name: '本社工場', count: 5 },
      { company_name: 'ピーエムアイ有限会社', plant_name: '本社工場', count: 3 },
    ],
    kintai_this_month: { employees_worked: 45, total_records: 850, total_hours: 6200, total_overtime: 420 },
    period: '2025年12月'
  },
  employees: [
    { employee_id: 'E200801', name_kanji: 'グエン・ヴァン・ミン', hakensaki_id: 'KATO-HON', company_name: '加藤木材工業株式会社', plant_name: '本社工場', department: '生産1部', hourly_wage: 1700, status: '在職中', visa_expiry: '2026-03-15' },
    { employee_id: 'E200802', name_kanji: 'チャン・ティ・ラン', hakensaki_id: 'KATO-HON', company_name: '加藤木材工業株式会社', plant_name: '本社工場', department: '生産1部', hourly_wage: 1700, status: '在職中', visa_expiry: '2025-12-20' },
    { employee_id: 'E200803', name_kanji: 'レ・ヴァン・ドゥック', hakensaki_id: 'TAKAO-OKA', company_name: '高雄工業株式会社', plant_name: '岡山工場', department: '製作課', hourly_wage: 1650, status: '在職中', visa_expiry: '2026-06-30' },
    { employee_id: 'E200804', name_kanji: 'ファム・ティ・フォン', hakensaki_id: 'KATO-KAS', company_name: '加藤木材工業株式会社', plant_name: '春日井工場', department: '生産2部', hourly_wage: 1700, status: '在職中', visa_expiry: '2026-01-15' },
    { employee_id: 'E200805', name_kanji: 'ホアン・ヴァン・フン', hakensaki_id: 'KORITSU-HON', company_name: 'コーリツ株式会社', plant_name: '本社工場', department: '製造部', hourly_wage: 1650, status: '在職中', visa_expiry: '2025-09-30' },
  ],
  hakensaki: [
    { hakensaki_id: 'KATO-HON', company_name: '加藤木材工業株式会社', plant_name: '本社工場', closing_day: 20, payment_day: '翌月20日', base_rate: 1700, employee_count: 18 },
    { hakensaki_id: 'KATO-KAS', company_name: '加藤木材工業株式会社', plant_name: '春日井工場', closing_day: 20, payment_day: '翌月20日', base_rate: 1700, employee_count: 7 },
    { hakensaki_id: 'TAKAO-OKA', company_name: '高雄工業株式会社', plant_name: '岡山工場', closing_day: 15, payment_day: '当月末日', base_rate: 1650, employee_count: 10 },
    { hakensaki_id: 'KORITSU-HON', company_name: 'コーリツ株式会社', plant_name: '本社工場', closing_day: 20, payment_day: '翌月15日', base_rate: 1650, employee_count: 7 },
    { hakensaki_id: 'YUASA-HON', company_name: 'ユアサ工機株式会社', plant_name: '本社工場', closing_day: 20, payment_day: '翌月20日', base_rate: 1700, employee_count: 5 },
    { hakensaki_id: 'PMI-HON', company_name: 'ピーエムアイ有限会社', plant_name: '本社工場', closing_day: 20, payment_day: '翌月15日', base_rate: 1600, employee_count: 3 },
  ],
  salary: [
    { employee_id: 'E200801', name: 'グエン・ヴァン・ミン', work_days: 20, regular_hours: 153.3, overtime_hours: 18.5, night_hours: 8.2, base_salary: 260610, overtime_pay: 39313, night_pay: 3485, holiday_pay: 0, transport_allowance: 5000, gross_salary: 308408, health_insurance: 15420, pension: 28219, employment_insurance: 1850, income_tax: 11020, resident_tax: 10000, housing_rent: 25000, utilities: 5000, meal_deduction: 8000, total_deductions: 104509, net_salary: 203899 },
    { employee_id: 'E200802', name: 'チャン・ティ・ラン', work_days: 19, regular_hours: 145.6, overtime_hours: 12.3, night_hours: 5.1, base_salary: 247520, overtime_pay: 26138, night_pay: 2168, holiday_pay: 0, transport_allowance: 5000, gross_salary: 280826, health_insurance: 14041, pension: 25696, employment_insurance: 1685, income_tax: 9641, resident_tax: 10000, housing_rent: 25000, utilities: 5000, meal_deduction: 7600, total_deductions: 98663, net_salary: 182163 },
    { employee_id: 'E200803', name: 'レ・ヴァン・ドゥック', work_days: 21, regular_hours: 157.5, overtime_hours: 22.0, night_hours: 15.8, base_salary: 259875, overtime_pay: 45375, night_pay: 6518, holiday_pay: 0, transport_allowance: 8000, gross_salary: 319768, health_insurance: 15988, pension: 29259, employment_insurance: 1919, income_tax: 11588, resident_tax: 10000, housing_rent: 28000, utilities: 5000, meal_deduction: 8400, total_deductions: 110154, net_salary: 209614 },
  ]
};

// ═══════════════════════════════════════════════════════════════
// Components
// ═══════════════════════════════════════════════════════════════

const Card = ({ children, className = '' }) => (
  <div className={`bg-white rounded-xl shadow-sm border border-gray-100 ${className}`}>
    {children}
  </div>
);

const StatCard = ({ icon: Icon, label, value, subValue, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  
  return (
    <Card className="p-4">
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon size={20} />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
        </div>
      </div>
    </Card>
  );
};

const NavButton = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
      active 
        ? 'bg-blue-600 text-white shadow-lg shadow-blue-200' 
        : 'text-gray-600 hover:bg-gray-100'
    }`}
  >
    <Icon size={18} />
    <span className="font-medium">{label}</span>
  </button>
);

// ═══════════════════════════════════════════════════════════════
// Dashboard View
// ═══════════════════════════════════════════════════════════════

const DashboardView = ({ data }) => {
  const { employees, by_company, kintai_this_month, period } = data;
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">ダッシュボード</h2>
          <p className="text-gray-500">{period}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="在職社員数" value={employees.active} subValue={`全${employees.total}名`} color="blue" />
        <StatCard icon={Clock} label="今月の総労働時間" value={`${kintai_this_month.total_hours.toLocaleString()}h`} subValue={`残業${kintai_this_month.total_overtime}h含む`} color="green" />
        <StatCard icon={Building2} label="派遣先数" value={by_company.length} subValue="工場" color="purple" />
        <StatCard icon={AlertTriangle} label="ビザ期限注意" value={employees.visa_expiring} subValue="90日以内" color="red" />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-5">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Building2 size={18} className="text-blue-600" />
            派遣先別 社員数
          </h3>
          <div className="space-y-3">
            {by_company.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{item.company_name}</p>
                  <p className="text-sm text-gray-500">{item.plant_name}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(item.count / 20) * 100}%` }}
                    />
                  </div>
                  <span className="font-bold text-gray-900 w-8 text-right">{item.count}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
        
        <Card className="p-5">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-emerald-600" />
            今月の勤怠サマリー
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">出勤者数</p>
              <p className="text-2xl font-bold text-gray-900">{kintai_this_month.employees_worked}名</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500">勤怠レコード</p>
              <p className="text-2xl font-bold text-gray-900">{kintai_this_month.total_records}件</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">所定内労働</p>
              <p className="text-2xl font-bold text-blue-700">{(kintai_this_month.total_hours - kintai_this_month.total_overtime).toLocaleString()}h</p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-600">残業時間</p>
              <p className="text-2xl font-bold text-orange-700">{kintai_this_month.total_overtime.toLocaleString()}h</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Employees View
// ═══════════════════════════════════════════════════════════════

const EmployeesView = ({ employees, hakensaki }) => {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  
  const filtered = employees.filter(emp => {
    const matchFilter = filter === 'all' || emp.hakensaki_id === filter;
    const matchSearch = !search || 
      emp.name_kanji.includes(search) || 
      emp.employee_id.includes(search);
    return matchFilter && matchSearch;
  });
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">従業員一覧</h2>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="検索..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">全派遣先</option>
            {hakensaki.map(h => (
              <option key={h.hakensaki_id} value={h.hakensaki_id}>
                {h.company_name} - {h.plant_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">社員番号</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">氏名</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">派遣先</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">部署</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">時給</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase">在留期限</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase">状態</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((emp, idx) => {
                const visaDate = new Date(emp.visa_expiry);
                const daysUntil = Math.ceil((visaDate - new Date()) / (1000 * 60 * 60 * 24));
                const visaWarning = daysUntil <= 90;
                
                return (
                  <tr key={emp.employee_id} className={`border-b hover:bg-gray-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                    <td className="px-4 py-3 font-mono text-sm text-gray-600">{emp.employee_id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{emp.name_kanji}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      <div>{emp.company_name}</div>
                      <div className="text-xs text-gray-400">{emp.plant_name}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{emp.department}</td>
                    <td className="px-4 py-3 text-right font-medium">¥{emp.hourly_wage.toLocaleString()}</td>
                    <td className={`px-4 py-3 text-center text-sm ${visaWarning ? 'text-red-600 font-medium' : 'text-gray-600'}`}>
                      {emp.visa_expiry}
                      {visaWarning && <span className="ml-1">⚠️</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        emp.status === '在職中' ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {emp.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Hakensaki View
// ═══════════════════════════════════════════════════════════════

const HakensakiView = ({ hakensaki }) => {
  const [expanded, setExpanded] = useState(null);
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">派遣先一覧</h2>
      
      <div className="grid gap-4">
        {hakensaki.map((h) => (
          <Card key={h.hakensaki_id} className="overflow-hidden">
            <button
              onClick={() => setExpanded(expanded === h.hakensaki_id ? null : h.hakensaki_id)}
              className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Building2 className="text-blue-600" size={24} />
                </div>
                <div className="text-left">
                  <h3 className="font-bold text-gray-900">{h.company_name}</h3>
                  <p className="text-sm text-gray-500">{h.plant_name}</p>
                </div>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-right">
                  <p className="text-2xl font-bold text-blue-600">{h.employee_count}</p>
                  <p className="text-xs text-gray-500">名在籍</p>
                </div>
                {expanded === h.hakensaki_id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
              </div>
            </button>
            
            {expanded === h.hakensaki_id && (
              <div className="px-4 pb-4 border-t bg-gray-50">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
                  <div>
                    <p className="text-xs text-gray-500">締め日</p>
                    <p className="font-medium text-gray-900">{h.closing_day}日</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">支払日</p>
                    <p className="font-medium text-gray-900">{h.payment_day}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">基本時給</p>
                    <p className="font-medium text-gray-900">¥{h.base_rate.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">ID</p>
                    <p className="font-mono text-sm text-gray-600">{h.hakensaki_id}</p>
                  </div>
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Salary View
// ═══════════════════════════════════════════════════════════════

const SalaryView = ({ salary }) => {
  const [selectedEmp, setSelectedEmp] = useState(null);
  
  const formatCurrency = (val) => `¥${val.toLocaleString()}`;
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">給与計算</h2>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2">
            <FileText size={18} />
            給与明細出力
          </button>
        </div>
      </div>
      
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">社員</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">出勤日数</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">総労働h</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">残業h</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase bg-blue-50">支給合計</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase bg-red-50">控除合計</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase bg-emerald-50">差引支給額</th>
              </tr>
            </thead>
            <tbody>
              {salary.map((s, idx) => (
                <tr 
                  key={s.employee_id} 
                  className={`border-b hover:bg-blue-50 cursor-pointer ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}
                  onClick={() => setSelectedEmp(selectedEmp === s.employee_id ? null : s.employee_id)}
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{s.name}</div>
                    <div className="text-xs text-gray-500 font-mono">{s.employee_id}</div>
                  </td>
                  <td className="px-4 py-3 text-right">{s.work_days}日</td>
                  <td className="px-4 py-3 text-right">{(s.regular_hours + s.overtime_hours).toFixed(1)}h</td>
                  <td className="px-4 py-3 text-right text-orange-600">{s.overtime_hours.toFixed(1)}h</td>
                  <td className="px-4 py-3 text-right font-medium text-blue-700 bg-blue-50/50">{formatCurrency(s.gross_salary)}</td>
                  <td className="px-4 py-3 text-right font-medium text-red-600 bg-red-50/50">{formatCurrency(s.total_deductions)}</td>
                  <td className="px-4 py-3 text-right font-bold text-emerald-700 bg-emerald-50/50">{formatCurrency(s.net_salary)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="bg-gray-100 font-bold">
                <td className="px-4 py-3">合計</td>
                <td className="px-4 py-3 text-right">{salary.reduce((a, b) => a + b.work_days, 0)}日</td>
                <td className="px-4 py-3 text-right">{salary.reduce((a, b) => a + b.regular_hours + b.overtime_hours, 0).toFixed(1)}h</td>
                <td className="px-4 py-3 text-right">{salary.reduce((a, b) => a + b.overtime_hours, 0).toFixed(1)}h</td>
                <td className="px-4 py-3 text-right text-blue-700">{formatCurrency(salary.reduce((a, b) => a + b.gross_salary, 0))}</td>
                <td className="px-4 py-3 text-right text-red-600">{formatCurrency(salary.reduce((a, b) => a + b.total_deductions, 0))}</td>
                <td className="px-4 py-3 text-right text-emerald-700">{formatCurrency(salary.reduce((a, b) => a + b.net_salary, 0))}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </Card>
      
      {selectedEmp && (
        <Card className="p-5">
          <h3 className="font-bold text-gray-900 mb-4">給与明細詳細</h3>
          {(() => {
            const emp = salary.find(s => s.employee_id === selectedEmp);
            if (!emp) return null;
            
            return (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-semibold text-blue-600 mb-2 flex items-center gap-1">
                    <Check size={16} /> 支給
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span>基本給</span><span>{formatCurrency(emp.base_salary)}</span></div>
                    <div className="flex justify-between"><span>残業手当</span><span>{formatCurrency(emp.overtime_pay)}</span></div>
                    <div className="flex justify-between"><span>深夜手当</span><span>{formatCurrency(emp.night_pay)}</span></div>
                    <div className="flex justify-between"><span>休日手当</span><span>{formatCurrency(emp.holiday_pay)}</span></div>
                    <div className="flex justify-between"><span>交通費</span><span>{formatCurrency(emp.transport_allowance)}</span></div>
                    <div className="flex justify-between pt-2 border-t font-bold"><span>支給合計</span><span className="text-blue-600">{formatCurrency(emp.gross_salary)}</span></div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold text-red-600 mb-2 flex items-center gap-1">
                    <X size={16} /> 控除
                  </h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span>健康保険</span><span>{formatCurrency(emp.health_insurance)}</span></div>
                    <div className="flex justify-between"><span>厚生年金</span><span>{formatCurrency(emp.pension)}</span></div>
                    <div className="flex justify-between"><span>雇用保険</span><span>{formatCurrency(emp.employment_insurance)}</span></div>
                    <div className="flex justify-between"><span>所得税</span><span>{formatCurrency(emp.income_tax)}</span></div>
                    <div className="flex justify-between"><span>住民税</span><span>{formatCurrency(emp.resident_tax)}</span></div>
                    <div className="flex justify-between"><span>社宅家賃</span><span>{formatCurrency(emp.housing_rent)}</span></div>
                    <div className="flex justify-between"><span>水道光熱費</span><span>{formatCurrency(emp.utilities)}</span></div>
                    <div className="flex justify-between"><span>弁当代</span><span>{formatCurrency(emp.meal_deduction)}</span></div>
                    <div className="flex justify-between pt-2 border-t font-bold"><span>控除合計</span><span className="text-red-600">{formatCurrency(emp.total_deductions)}</span></div>
                  </div>
                </div>
                
                <div className="flex flex-col justify-center items-center bg-emerald-50 rounded-xl p-6">
                  <p className="text-sm text-emerald-600 mb-1">差引支給額</p>
                  <p className="text-4xl font-bold text-emerald-700">{formatCurrency(emp.net_salary)}</p>
                </div>
              </div>
            );
          })()}
        </Card>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// Main App
// ═══════════════════════════════════════════════════════════════

export default function KintaiApp() {
  const [view, setView] = useState('dashboard');
  const [data, setData] = useState(DEMO_DATA);
  const [loading, setLoading] = useState(false);
  
  // Try to fetch from API (falls back to demo data)
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashRes, empRes, hakRes, salRes] = await Promise.all([
          fetch(`${API_BASE}/dashboard`),
          fetch(`${API_BASE}/employees`),
          fetch(`${API_BASE}/hakensaki`),
          fetch(`${API_BASE}/salary/calculate`)
        ]);
        
        if (dashRes.ok && empRes.ok && hakRes.ok && salRes.ok) {
          setData({
            dashboard: await dashRes.json(),
            employees: await empRes.json(),
            hakensaki: await hakRes.json(),
            salary: await salRes.json()
          });
        }
      } catch (e) {
        console.log('Using demo data');
      }
    };
    fetchData();
  }, []);
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-200">
                <Clock className="text-white" size={22} />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">UNS 勤怠管理システム</h1>
                <p className="text-xs text-gray-500">ユニバーサル企画株式会社</p>
              </div>
            </div>
            
            <nav className="flex gap-2">
              <NavButton icon={BarChart3} label="ダッシュボード" active={view === 'dashboard'} onClick={() => setView('dashboard')} />
              <NavButton icon={Users} label="従業員" active={view === 'employees'} onClick={() => setView('employees')} />
              <NavButton icon={Building2} label="派遣先" active={view === 'hakensaki'} onClick={() => setView('hakensaki')} />
              <NavButton icon={DollarSign} label="給与計算" active={view === 'salary'} onClick={() => setView('salary')} />
            </nav>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {view === 'dashboard' && <DashboardView data={data.dashboard} />}
        {view === 'employees' && <EmployeesView employees={data.employees} hakensaki={data.hakensaki} />}
        {view === 'hakensaki' && <HakensakiView hakensaki={data.hakensaki} />}
        {view === 'salary' && <SalaryView salary={data.salary} />}
      </main>
      
      {/* Footer */}
      <footer className="border-t bg-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          UNS 勤怠管理システム v1.0 | ユニバーサル企画株式会社 | 派遣許可番号: 派23-303669
        </div>
      </footer>
    </div>
  );
}
