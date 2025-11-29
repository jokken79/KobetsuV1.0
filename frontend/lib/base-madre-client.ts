/**
 * Cliente para conectar con Super Base Madre (UNS-Shatak)
 *
 * Este cliente proporciona acceso a empleados, empresas y plantas
 * desde el sistema central de Base Madre.
 */

const BASE_URL = process.env.NEXT_PUBLIC_BASE_MADRE_API_URL || process.env.BASE_MADRE_API_URL || 'http://localhost:5000/api/v1';
const API_KEY = process.env.NEXT_PUBLIC_BASE_MADRE_API_KEY || process.env.BASE_MADRE_API_KEY;

export interface Employee {
  id: number;
  employee_id: string;
  name: string;
  name_kana?: string;
  email?: string;
  phone?: string;
  status: string;
  hire_date?: string;
  nationality?: string;
  gender?: string;
  age?: number;
  visa_type?: string;
  visa_expiry?: string;
  dispatch_company?: string;
  hourly_rate?: number;
  company_name?: string;
  company_id?: number;
  plant_name?: string;
  plant_id?: number;
  line_name?: string;
  production_line_id?: number;
}

export interface Company {
  id: number;
  company_name: string;
  address?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  contact_phone?: string;
  responsible_department?: string;
  plants_count: number;
  employees_count: number;
  jigyosho_count?: number;
}

export interface Plant {
  id: number;
  plant_name: string;
  plant_code?: string;
  plant_address?: string;
  plant_phone?: string;
  manager_name?: string;
  company_name: string;
  company_id: number;
  jigyosho_name?: string;
  production_lines_count: number;
  employees_count: number;
}

export interface PaginationInfo {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface EmployeesResponse {
  success: boolean;
  data: Employee[];
  pagination: PaginationInfo;
}

export interface EmployeeResponse {
  success: boolean;
  data: Employee;
}

export interface EmployeeSearchResponse {
  success: boolean;
  data: Employee[];
  count: number;
}

export interface CompaniesResponse {
  success: boolean;
  data: Company[];
}

export interface CompanyDetailResponse {
  success: boolean;
  data: {
    company: Company;
    plants: Plant[];
    employee_stats: Array<{
      status: string;
      count: number;
    }>;
  };
}

export interface PlantsResponse {
  success: boolean;
  data: Plant[];
}

export interface ErrorResponse {
  success: false;
  error: string;
}

class BaseMadreClient {
  private baseUrl: string;
  private apiKey: string | undefined;

  constructor() {
    this.baseUrl = BASE_URL;
    this.apiKey = API_KEY;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    if (!this.apiKey && !endpoint.includes('/health')) {
      throw new Error('API Key not configured. Please set BASE_MADRE_API_KEY in environment variables.');
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options?.headers,
    };

    if (this.apiKey && !endpoint.includes('/health')) {
      headers['X-API-Key'] = this.apiKey;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(error.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  /**
   * Health check endpoint (no authentication required)
   */
  async health(): Promise<{ status: string; service: string; version: string; timestamp: string }> {
    return this.request('/health');
  }

  /**
   * Get employees list with pagination and filters
   */
  async getEmployees(params?: {
    company_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<EmployeesResponse> {
    const queryParams = new URLSearchParams();

    if (params?.company_id) queryParams.append('company_id', params.company_id.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const query = queryParams.toString();
    return this.request(`/employees${query ? `?${query}` : ''}`);
  }

  /**
   * Get single employee by ID with full details
   */
  async getEmployee(id: number): Promise<EmployeeResponse> {
    return this.request(`/employees/${id}`);
  }

  /**
   * Search employees by name, email, or employee_id
   */
  async searchEmployees(query: string): Promise<EmployeeSearchResponse> {
    if (!query || query.trim().length < 2) {
      throw new Error('Search query must be at least 2 characters');
    }
    return this.request(`/employees/search?q=${encodeURIComponent(query)}`);
  }

  /**
   * Get all companies with statistics
   */
  async getCompanies(): Promise<CompaniesResponse> {
    return this.request('/companies');
  }

  /**
   * Get single company with detailed information
   */
  async getCompany(id: number): Promise<CompanyDetailResponse> {
    return this.request(`/companies/${id}`);
  }

  /**
   * Get plants list, optionally filtered by company
   */
  async getPlants(companyId?: number): Promise<PlantsResponse> {
    const query = companyId ? `?company_id=${companyId}` : '';
    return this.request(`/plants${query}`);
  }
}

// Singleton instance
export const baseMadreClient = new BaseMadreClient();

// Export class for testing
export { BaseMadreClient };
