#!/usr/bin/env python3
"""
UNS Kintai Management System - FastAPI Backend
==============================================
API REST para gestión de勤怠, empleados y給与計算
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
import os
import calendar

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "../database/uns_kintai.db")

app = FastAPI(
    title="UNS 勤怠管理システム API",
    description="派遣社員の勤怠管理・給与計算API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════

class Employee(BaseModel):
    employee_id: str
    name_kanji: str
    name_kana: Optional[str]
    gender: Optional[str]
    nationality: Optional[str]
    visa_type: Optional[str]
    visa_expiry: Optional[str]
    hakensaki_id: Optional[str]
    company_name: Optional[str]
    plant_name: Optional[str]
    department: Optional[str]
    line: Optional[str]
    hourly_wage: float
    status: str

class KintaiRecord(BaseModel):
    employee_id: str
    work_date: str
    clock_in: Optional[str]
    clock_out: Optional[str]
    break_minutes: int = 60
    actual_hours: Optional[float]
    overtime_hours: float = 0
    night_hours: float = 0
    holiday_flag: int = 0
    paid_leave_flag: int = 0

class KintaiInput(BaseModel):
    employee_id: str
    work_date: str
    clock_in: str
    clock_out: str
    break_minutes: int = 60

class SalaryCalculation(BaseModel):
    employee_id: str
    name: str
    year: int
    month: int
    work_days: int
    regular_hours: float
    overtime_hours: float
    night_hours: float
    holiday_hours: float
    base_salary: float
    overtime_pay: float
    night_pay: float
    holiday_pay: float
    transport_allowance: float
    gross_salary: float
    health_insurance: float
    pension: float
    employment_insurance: float
    income_tax: float
    resident_tax: float
    housing_rent: float
    utilities: float
    meal_deduction: float
    total_deductions: float
    net_salary: float

class Hakensaki(BaseModel):
    hakensaki_id: str
    company_name: str
    plant_name: str
    address: Optional[str]
    phone: Optional[str]
    closing_day: int
    payment_day: str
    base_rate: float
    employee_count: Optional[int]

# ═══════════════════════════════════════════════════════════════
# Database Connection
# ═══════════════════════════════════════════════════════════════

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {
        "system": "UNS 勤怠管理システム",
        "version": "1.0.0",
        "company": "ユニバーサル企画株式会社",
        "permit": "派23-303669"
    }

# ─────────────────────────────────────────────────────────────────
# 従業員 (Employees)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/employees", response_model=List[Employee])
async def get_employees(
    hakensaki_id: Optional[str] = None,
    status: Optional[str] = "在職中"
):
    """Get all employees, optionally filtered by hakensaki or status"""
    conn = get_db()
    query = '''
        SELECT e.*, h.company_name, h.plant_name
        FROM employees e
        LEFT JOIN hakensaki h ON e.hakensaki_id = h.hakensaki_id
        WHERE 1=1
    '''
    params = []
    
    if status:
        query += " AND e.status = ?"
        params.append(status)
    if hakensaki_id:
        query += " AND e.hakensaki_id = ?"
        params.append(hakensaki_id)
    
    query += " ORDER BY e.employee_id"
    
    cursor = conn.execute(query, params)
    employees = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return employees

@app.get("/api/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """Get single employee by ID"""
    conn = get_db()
    cursor = conn.execute('''
        SELECT e.*, h.company_name, h.plant_name
        FROM employees e
        LEFT JOIN hakensaki h ON e.hakensaki_id = h.hakensaki_id
        WHERE e.employee_id = ?
    ''', (employee_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)

# ─────────────────────────────────────────────────────────────────
# 派遣先 (Hakensaki / Client Companies)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/hakensaki", response_model=List[Hakensaki])
async def get_hakensaki():
    """Get all client companies with employee counts"""
    conn = get_db()
    cursor = conn.execute('''
        SELECT h.*, COUNT(e.employee_id) as employee_count
        FROM hakensaki h
        LEFT JOIN employees e ON h.hakensaki_id = e.hakensaki_id AND e.status = '在職中'
        GROUP BY h.hakensaki_id
        ORDER BY h.company_name, h.plant_name
    ''')
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

# ─────────────────────────────────────────────────────────────────
# 勤怠 (Attendance)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/kintai")
async def get_kintai(
    employee_id: Optional[str] = None,
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
    hakensaki_id: Optional[str] = None
):
    """Get attendance records for a month"""
    conn = get_db()
    
    start_date = date(year, month, 1)
    _, days_in_month = calendar.monthrange(year, month)
    end_date = date(year, month, days_in_month)
    
    query = '''
        SELECT k.*, e.name_kanji, e.hakensaki_id, h.company_name
        FROM kintai k
        JOIN employees e ON k.employee_id = e.employee_id
        LEFT JOIN hakensaki h ON e.hakensaki_id = h.hakensaki_id
        WHERE k.work_date BETWEEN ? AND ?
    '''
    params = [start_date.isoformat(), end_date.isoformat()]
    
    if employee_id:
        query += " AND k.employee_id = ?"
        params.append(employee_id)
    if hakensaki_id:
        query += " AND e.hakensaki_id = ?"
        params.append(hakensaki_id)
    
    query += " ORDER BY k.employee_id, k.work_date"
    
    cursor = conn.execute(query, params)
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records

@app.post("/api/kintai")
async def add_kintai(record: KintaiInput):
    """Add or update attendance record"""
    conn = get_db()
    
    # Calculate actual hours
    try:
        clock_in = datetime.strptime(record.clock_in, "%H:%M")
        clock_out = datetime.strptime(record.clock_out, "%H:%M")
        
        # Handle overnight shifts
        if clock_out < clock_in:
            clock_out += timedelta(days=1)
        
        total_minutes = (clock_out - clock_in).seconds // 60
        actual_hours = (total_minutes - record.break_minutes) / 60
        
        # Calculate overtime (over 8 hours)
        overtime_hours = max(0, actual_hours - 8)
        
        # Calculate night hours (22:00 - 05:00)
        night_hours = 0
        # Simplified: if clock_out is after midnight, count some as night
        if clock_out.hour < 6 or clock_in.hour >= 22:
            night_hours = min(actual_hours, 4)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {e}")
    
    conn.execute('''
        INSERT OR REPLACE INTO kintai 
        (employee_id, work_date, clock_in, clock_out, break_minutes,
         actual_hours, overtime_hours, night_hours, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (
        record.employee_id, record.work_date, record.clock_in, record.clock_out,
        record.break_minutes, round(actual_hours, 2), round(overtime_hours, 2),
        round(night_hours, 2)
    ))
    conn.commit()
    conn.close()
    
    return {"status": "success", "actual_hours": round(actual_hours, 2)}

# ─────────────────────────────────────────────────────────────────
# 給与計算 (Salary Calculation)
# ─────────────────────────────────────────────────────────────────

@app.get("/api/salary/calculate")
async def calculate_salary(
    employee_id: Optional[str] = None,
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
    hakensaki_id: Optional[str] = None
):
    """Calculate salary for employees"""
    conn = get_db()
    
    # Get employees
    emp_query = '''
        SELECT e.*, h.base_rate
        FROM employees e
        LEFT JOIN hakensaki h ON e.hakensaki_id = h.hakensaki_id
        WHERE e.status = '在職中'
    '''
    params = []
    if employee_id:
        emp_query += " AND e.employee_id = ?"
        params.append(employee_id)
    if hakensaki_id:
        emp_query += " AND e.hakensaki_id = ?"
        params.append(hakensaki_id)
    
    cursor = conn.execute(emp_query, params)
    employees = [dict(row) for row in cursor.fetchall()]
    
    results = []
    start_date = date(year, month, 1)
    _, days_in_month = calendar.monthrange(year, month)
    end_date = date(year, month, days_in_month)
    
    for emp in employees:
        # Get attendance summary
        cursor = conn.execute('''
            SELECT 
                COUNT(*) as work_days,
                COALESCE(SUM(actual_hours), 0) as total_hours,
                COALESCE(SUM(overtime_hours), 0) as overtime_hours,
                COALESCE(SUM(night_hours), 0) as night_hours,
                COALESCE(SUM(CASE WHEN holiday_flag = 1 THEN actual_hours ELSE 0 END), 0) as holiday_hours,
                COALESCE(SUM(CASE WHEN paid_leave_flag = 1 THEN 1 ELSE 0 END), 0) as paid_leave_days
            FROM kintai
            WHERE employee_id = ?
              AND work_date BETWEEN ? AND ?
        ''', (emp["employee_id"], start_date.isoformat(), end_date.isoformat()))
        
        kintai = dict(cursor.fetchone())
        
        # Calculate salary
        hourly_wage = emp["hourly_wage"] or emp["base_rate"] or 1700
        
        regular_hours = max(0, kintai["total_hours"] - kintai["overtime_hours"])
        
        base_salary = regular_hours * hourly_wage
        overtime_pay = kintai["overtime_hours"] * hourly_wage * 1.25
        night_pay = kintai["night_hours"] * hourly_wage * 0.25  # Additional 25%
        holiday_pay = kintai["holiday_hours"] * hourly_wage * 0.35  # Additional 35%
        paid_leave_pay = kintai["paid_leave_days"] * 8 * hourly_wage
        transport_allowance = emp["transport_allowance"] or 5000
        
        gross_salary = base_salary + overtime_pay + night_pay + holiday_pay + paid_leave_pay + transport_allowance
        
        # Deductions
        health_insurance = round(gross_salary * 0.05)
        pension = round(gross_salary * 0.0915)
        employment_insurance = round(gross_salary * 0.006)
        
        # Simplified income tax (actual is complex)
        taxable = max(0, gross_salary - 88000)
        income_tax = round(taxable * 0.05) if taxable > 0 else 0
        
        resident_tax = 10000  # Fixed monthly
        housing_rent = emp["housing_rent"] if emp["has_housing"] == "有" else 0
        utilities = 5000 if emp["has_housing"] == "有" else 0
        meal_deduction = kintai["work_days"] * 400  # ¥400/day for meals
        
        total_deductions = (health_insurance + pension + employment_insurance + 
                          income_tax + resident_tax + housing_rent + utilities + meal_deduction)
        
        net_salary = gross_salary - total_deductions
        
        results.append({
            "employee_id": emp["employee_id"],
            "name": emp["name_kanji"],
            "year": year,
            "month": month,
            "work_days": kintai["work_days"],
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(kintai["overtime_hours"], 2),
            "night_hours": round(kintai["night_hours"], 2),
            "holiday_hours": round(kintai["holiday_hours"], 2),
            "base_salary": round(base_salary),
            "overtime_pay": round(overtime_pay),
            "night_pay": round(night_pay),
            "holiday_pay": round(holiday_pay),
            "transport_allowance": transport_allowance,
            "gross_salary": round(gross_salary),
            "health_insurance": health_insurance,
            "pension": pension,
            "employment_insurance": employment_insurance,
            "income_tax": income_tax,
            "resident_tax": resident_tax,
            "housing_rent": housing_rent,
            "utilities": utilities,
            "meal_deduction": meal_deduction,
            "total_deductions": round(total_deductions),
            "net_salary": round(net_salary)
        })
    
    conn.close()
    return results

# ─────────────────────────────────────────────────────────────────
# Dashboard / Statistics
# ─────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard statistics"""
    conn = get_db()
    
    # Employee counts
    cursor = conn.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = '在職中' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN visa_expiry <= date('now', '+90 days') THEN 1 ELSE 0 END) as visa_expiring
        FROM employees
    ''')
    emp_stats = dict(cursor.fetchone())
    
    # By hakensaki
    cursor = conn.execute('''
        SELECT h.company_name, h.plant_name, COUNT(e.employee_id) as count
        FROM hakensaki h
        LEFT JOIN employees e ON h.hakensaki_id = e.hakensaki_id AND e.status = '在職中'
        GROUP BY h.hakensaki_id
        ORDER BY count DESC
    ''')
    by_company = [dict(row) for row in cursor.fetchall()]
    
    # This month attendance summary
    today = datetime.now()
    start_date = date(today.year, today.month, 1)
    cursor = conn.execute('''
        SELECT 
            COUNT(DISTINCT employee_id) as employees_worked,
            COUNT(*) as total_records,
            COALESCE(SUM(actual_hours), 0) as total_hours,
            COALESCE(SUM(overtime_hours), 0) as total_overtime
        FROM kintai
        WHERE work_date >= ?
    ''', (start_date.isoformat(),))
    kintai_stats = dict(cursor.fetchone())
    
    conn.close()
    
    return {
        "employees": emp_stats,
        "by_company": by_company,
        "kintai_this_month": kintai_stats,
        "period": f"{today.year}年{today.month}月"
    }

@app.get("/api/visa-alerts")
async def get_visa_alerts():
    """Get employees with expiring visas"""
    conn = get_db()
    cursor = conn.execute('''
        SELECT e.*, h.company_name, h.plant_name,
               julianday(e.visa_expiry) - julianday('now') as days_remaining
        FROM employees e
        LEFT JOIN hakensaki h ON e.hakensaki_id = h.hakensaki_id
        WHERE e.status = '在職中'
          AND e.visa_expiry <= date('now', '+180 days')
        ORDER BY e.visa_expiry
    ''')
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

# ─────────────────────────────────────────────────────────────────
# Run Server
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
