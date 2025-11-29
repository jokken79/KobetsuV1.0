'use client';

import { useEmployee } from '@/hooks/use-base-madre';

interface EmployeeDetailsCardProps {
  employeeId: number;
  className?: string;
}

export function EmployeeDetailsCard({ employeeId, className = '' }: EmployeeDetailsCardProps) {
  const { employee, loading, error } = useEmployee(employeeId);

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gray-200 rounded-full"></div>
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-3">
          <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div>
            <p className="font-medium text-red-800">Error al cargar empleado</p>
            <p className="text-sm text-red-600">{error || 'Empleado no encontrado'}</p>
          </div>
        </div>
      </div>
    );
  }

  const statusColors = {
    '在職中': 'bg-green-100 text-green-800 border-green-300',
    '退職': 'bg-red-100 text-red-800 border-red-300',
    '待機中': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  };

  const statusColor = statusColors[employee.status as keyof typeof statusColors] || 'bg-gray-100 text-gray-800 border-gray-300';

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 text-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white bg-opacity-20 backdrop-blur rounded-full flex items-center justify-center text-2xl font-bold">
            {employee.name.charAt(0)}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold">{employee.name}</h3>
            {employee.name_kana && <p className="text-blue-100 text-sm">{employee.name_kana}</p>}
            <p className="text-blue-100 text-sm mt-1">ID: {employee.employee_id || employee.id}</p>
          </div>
          <div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${statusColor}`}>
              {employee.status}
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-6">
        {/* Contact Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            Información de Contacto
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {employee.email && (
              <div className="flex items-center gap-2 text-sm">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <a href={`mailto:${employee.email}`} className="text-blue-600 hover:underline">
                  {employee.email}
                </a>
              </div>
            )}
            {employee.phone && (
              <div className="flex items-center gap-2 text-sm">
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                  />
                </svg>
                <a href={`tel:${employee.phone}`} className="text-blue-600 hover:underline">
                  {employee.phone}
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Company & Location */}
        {(employee.company_name || employee.plant_name) && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
              Empresa y Ubicación
            </h4>
            <div className="space-y-2">
              {employee.company_name && (
                <div className="flex items-start gap-2 text-sm">
                  <svg className="w-4 h-4 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                  <div>
                    <p className="font-medium text-gray-900">{employee.company_name}</p>
                    {employee.dispatch_company && employee.dispatch_company !== employee.company_name && (
                      <p className="text-xs text-gray-500">Enviado por: {employee.dispatch_company}</p>
                    )}
                  </div>
                </div>
              )}
              {employee.plant_name && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {employee.plant_name}
                  {employee.line_name && <span className="text-gray-400">• {employee.line_name}</span>}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Personal Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            Información Personal
          </h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {employee.nationality && (
              <div>
                <p className="text-gray-500">Nacionalidad</p>
                <p className="font-medium text-gray-900">{employee.nationality}</p>
              </div>
            )}
            {employee.gender && (
              <div>
                <p className="text-gray-500">Género</p>
                <p className="font-medium text-gray-900">{employee.gender}</p>
              </div>
            )}
            {employee.age && (
              <div>
                <p className="text-gray-500">Edad</p>
                <p className="font-medium text-gray-900">{employee.age} años</p>
              </div>
            )}
            {employee.hire_date && (
              <div>
                <p className="text-gray-500">Fecha de Contratación</p>
                <p className="font-medium text-gray-900">
                  {new Date(employee.hire_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Visa Information */}
        {(employee.visa_type || employee.visa_expiry) && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Información de Visa
            </h4>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {employee.visa_type && (
                <div>
                  <p className="text-gray-500">Tipo de Visa</p>
                  <p className="font-medium text-gray-900">{employee.visa_type}</p>
                </div>
              )}
              {employee.visa_expiry && (
                <div>
                  <p className="text-gray-500">Vencimiento</p>
                  <p className="font-medium text-gray-900">
                    {new Date(employee.visa_expiry).toLocaleDateString('ja-JP')}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Employment Details */}
        {employee.hourly_rate && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Detalles de Empleo
            </h4>
            <div className="text-sm">
              <p className="text-gray-500">Tarifa por Hora</p>
              <p className="font-medium text-gray-900 text-lg">¥{employee.hourly_rate.toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          <span className="font-medium">Fuente:</span> Super Base Madre (Sistema Central de Empleados)
        </p>
      </div>
    </div>
  );
}
