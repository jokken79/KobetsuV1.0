'use client';

import { useState, useRef, useEffect } from 'react';
import { Employee } from '@/lib/base-madre-client';
import { useEmployeeSearch, useEmployees } from '@/hooks/use-base-madre';

interface EmployeeSelectorProps {
  value?: number | null;
  onChange: (employeeId: number, employee: Employee) => void;
  companyId?: number;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
}

export function EmployeeSelector({
  value,
  onChange,
  companyId,
  className = '',
  placeholder = 'Buscar empleado por nombre, email o ID...',
  disabled = false,
}: EmployeeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const { query, setQuery, results, loading: searchLoading } = useEmployeeSearch('', 300);
  const { employees, loading: listLoading } = useEmployees({
    company_id: companyId,
    status: '在職中', // Solo empleados activos
    limit: 20,
    enabled: isOpen && !query, // Cargar lista solo cuando está abierto y no hay búsqueda
  });

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load selected employee if value changes
  useEffect(() => {
    if (value && !selectedEmployee) {
      // Buscar en los resultados actuales primero
      const found = results.find((e) => e.id === value) || employees.find((e) => e.id === value);
      if (found) {
        setSelectedEmployee(found);
      }
    }
  }, [value, results, employees, selectedEmployee]);

  const handleSelect = (employee: Employee) => {
    setSelectedEmployee(employee);
    onChange(employee.id, employee);
    setQuery('');
    setIsOpen(false);
  };

  const handleClear = () => {
    setSelectedEmployee(null);
    setQuery('');
    inputRef.current?.focus();
  };

  const displayEmployees = query.trim().length >= 2 ? results : employees;
  const isLoading = query.trim().length >= 2 ? searchLoading : listLoading;

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* Input Field */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={selectedEmployee ? selectedEmployee.name : query}
          onChange={(e) => {
            setQuery(e.target.value);
            setSelectedEmployee(null);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          disabled={disabled}
          placeholder={placeholder}
          className={`
            w-full px-4 py-2 pr-10 border rounded-lg
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            disabled:bg-gray-100 disabled:cursor-not-allowed
            ${selectedEmployee ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-300'}
          `}
        />

        {/* Icons */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && (
            <svg
              className="animate-spin h-5 w-5 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          )}

          {selectedEmployee ? (
            <button
              onClick={handleClear}
              type="button"
              className="p-1 hover:bg-gray-200 rounded-full transition"
            >
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          ) : (
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          )}
        </div>
      </div>

      {/* Selected Employee Badge */}
      {selectedEmployee && (
        <div className="mt-2 p-2 bg-blue-100 border border-blue-300 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
              {selectedEmployee.name.charAt(0)}
            </div>
            <div>
              <p className="font-medium text-sm">{selectedEmployee.name}</p>
              <p className="text-xs text-gray-600">
                {selectedEmployee.employee_id} • {selectedEmployee.company_name}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dropdown List */}
      {isOpen && !selectedEmployee && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">
              <svg
                className="animate-spin h-8 w-8 mx-auto text-blue-500"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <p className="mt-2">Buscando...</p>
            </div>
          ) : displayEmployees.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              {query.trim().length >= 2 ? (
                <>
                  <svg
                    className="w-12 h-12 mx-auto text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="mt-2">No se encontraron empleados</p>
                  <p className="text-sm">Intenta con otro término de búsqueda</p>
                </>
              ) : (
                <>
                  <p>Escribe al menos 2 caracteres para buscar</p>
                  <p className="text-sm text-gray-400">O abre para ver empleados recientes</p>
                </>
              )}
            </div>
          ) : (
            <div className="py-1">
              {displayEmployees.map((employee) => (
                <button
                  key={employee.id}
                  onClick={() => handleSelect(employee)}
                  type="button"
                  className="w-full px-4 py-3 hover:bg-blue-50 flex items-center gap-3 transition text-left"
                >
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                    {employee.name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{employee.name}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span className="truncate">{employee.employee_id}</span>
                      <span>•</span>
                      <span className="truncate">{employee.company_name}</span>
                      {employee.plant_name && (
                        <>
                          <span>•</span>
                          <span className="truncate">{employee.plant_name}</span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          employee.status === '在職中'
                            ? 'bg-green-100 text-green-700'
                            : employee.status === '待機中'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {employee.status}
                      </span>
                      {employee.nationality && (
                        <span className="text-xs text-gray-500">{employee.nationality}</span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Footer with result count */}
          {displayEmployees.length > 0 && (
            <div className="border-t border-gray-200 px-4 py-2 bg-gray-50 text-xs text-gray-600">
              {displayEmployees.length} {displayEmployees.length === 1 ? 'resultado' : 'resultados'}
              {query.trim().length >= 2 && ` para "${query}"`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
