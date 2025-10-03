/**
 * API service for SQL-Guard frontend
 * Centralized HTTP client with authentication and error handling
 */
import { authService } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  total?: number;
  limit?: number;
  offset?: number;
}

export interface ApiError {
  detail: string;
  status: number;
}

class ApiService {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Make authenticated API request
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    // Add authentication headers
    const authHeaders = authService.getAuthHeaders();
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      // Handle 401 Unauthorized
      if (response.status === 401) {
        try {
          // Try to refresh token
          await authService.refreshAccessToken();
          
          // Retry request with new token
          const retryConfig = {
            ...config,
            headers: {
              ...config.headers,
              ...authService.getAuthHeaders(),
            },
          };
          
          const retryResponse = await fetch(url, retryConfig);
          return this.handleResponse(retryResponse);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          authService.logout();
          throw new ApiError('Authentication failed', 401);
        }
      }

      return this.handleResponse(response);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      console.error('API request error:', error);
      throw new ApiError('Network error', 0);
    }
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}`,
        response.status
      );
    }

    const data = await response.json();
    return data;
  }

  /**
   * GET request
   */
  async get<T = any>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const url = params ? this.buildUrlWithParams(endpoint, params) : endpoint;
    return this.request<T>(url, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * PATCH request
   */
  async patch<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Upload file
   */
  async upload<T = any>(endpoint: string, file: File, additionalData?: Record<string, any>): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const authHeaders = authService.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: {
        ...authHeaders,
        // Don't set Content-Type for FormData, let browser set it with boundary
      },
      body: formData,
    });

    return this.handleResponse(response);
  }

  /**
   * Download file
   */
  async download(endpoint: string, filename?: string): Promise<void> {
    const authHeaders = authService.getAuthHeaders();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: authHeaders,
    });

    if (!response.ok) {
      throw new ApiError(`Download failed: ${response.statusText}`, response.status);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Build URL with query parameters
   */
  private buildUrlWithParams(endpoint: string, params: Record<string, any>): string {
    const url = new URL(endpoint, this.baseURL);
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => url.searchParams.append(key, String(item)));
        } else {
          url.searchParams.append(key, String(value));
        }
      }
    });

    return url.pathname + url.search;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  public status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// Create singleton instance
export const apiService = new ApiService();
export default apiService;

/**
 * API endpoints
 */
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    ME: '/auth/me',
    PERMISSIONS: '/auth/permissions',
    OIDC_LOGIN: '/auth/oidc/login',
    OIDC_CALLBACK: '/auth/oidc/callback',
  },
  
  // Queries
  QUERIES: {
    EXECUTE: '/api/queries/execute',
    VALIDATE: '/api/queries/validate',
    STATUS: '/api/queries/status',
    TEMPLATE_EXECUTE: '/api/queries/template/execute',
    DATABASES: '/api/queries/databases',
    SCHEMAS: '/api/queries/schemas',
    TABLES: '/api/queries/tables',
  },
  
  // Templates
  TEMPLATES: {
    LIST: '/api/templates',
    CREATE: '/api/templates',
    GET: '/api/templates',
    UPDATE: '/api/templates',
    DELETE: '/api/templates',
    EXECUTE: '/api/templates',
    VALIDATE: '/api/templates/validate',
    VERSIONS: '/api/templates',
    USAGE: '/api/templates',
  },
  
  // Approvals
  APPROVALS: {
    LIST: '/api/approvals',
    CREATE: '/api/approvals',
    GET: '/api/approvals',
    UPDATE: '/api/approvals',
    PROCESS: '/api/approvals',
    PREVIEW: '/api/approvals',
    BULK_PROCESS: '/api/approvals/bulk-process',
    STATS: '/api/approvals/stats',
    QUEUE: '/api/approvals/queue',
    HISTORY: '/api/approvals/history',
  },
  
  // Audit
  AUDIT: {
    LIST: '/api/audit',
    SEARCH: '/api/audit/search',
    EXPORT: '/api/audit/export',
    STATS: '/api/audit/stats',
    SECURITY_EVENTS: '/api/audit/security-events',
    MY_LOGS: '/api/audit/my-logs',
    RECENT_ACTIVITY: '/api/audit/recent-activity',
    VIOLATIONS: '/api/audit/violations',
  },
  
  // Users
  USERS: {
    LIST: '/api/users',
    CREATE: '/api/users',
    GET: '/api/users',
    UPDATE: '/api/users',
    DELETE: '/api/users',
    STATS: '/api/users/stats',
    ROLES: '/api/users/roles',
    PERMISSIONS: '/api/users',
    ACTIVITY: '/api/users',
  },
  
  // Policies
  POLICIES: {
    LIST: '/api/policies',
    CREATE: '/api/policies',
    GET: '/api/policies',
    UPDATE: '/api/policies',
    DELETE: '/api/policies',
    EVALUATE: '/api/policies/evaluate',
    STATS: '/api/policies/stats',
    TYPES: '/api/policies/types',
    TARGETS: '/api/policies/targets',
    PRIORITIES: '/api/policies/priorities',
    TEMPLATES: '/api/policies/templates',
    VIOLATIONS: '/api/policies/violations',
  },
} as const;