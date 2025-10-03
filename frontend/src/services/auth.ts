/**
 * Authentication service for SQL-Guard frontend
 * Handles login, logout, token management, and OIDC integration
 */
import { UserProfile, UserToken, UserLogin } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface AuthState {
  user: UserProfile | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

class AuthService {
  private token: string | null = null;
  private refreshToken: string | null = null;
  private user: UserProfile | null = null;
  private listeners: ((state: AuthState) => void)[] = [];

  constructor() {
    // Initialize from localStorage
    this.token = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    this.user = this.getStoredUser();
    
    // Set up automatic token refresh
    this.setupTokenRefresh();
  }

  /**
   * Login with username and password
   */
  async login(credentials: UserLogin): Promise<UserToken> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data: UserToken = await response.json();
      
      // Store tokens and user data
      this.setTokens(data.access_token, data.refresh_token);
      this.setUser(data.user);
      
      // Notify listeners
      this.notifyListeners();
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    try {
      if (this.token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API call success
      this.clearAuth();
    }
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      this.setTokens(data.access_token, this.refreshToken);
      this.notifyListeners();
      
      return data.access_token;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearAuth();
      throw error;
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<UserProfile> {
    if (!this.token) {
      throw new Error('No authentication token');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          const newToken = await this.refreshAccessToken();
          return this.getCurrentUser();
        }
        throw new Error('Failed to get user profile');
      }

      const user: UserProfile = await response.json();
      this.setUser(user);
      this.notifyListeners();
      
      return user;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(): Promise<any> {
    if (!this.token) {
      throw new Error('No authentication token');
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/permissions`, {
        headers: {
          'Authorization': `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get user permissions');
      }

      return await response.json();
    } catch (error) {
      console.error('Get user permissions error:', error);
      throw error;
    }
  }

  /**
   * Initiate OIDC login
   */
  async initiateOIDCLogin(): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/oidc/login`);
      
      if (!response.ok) {
        throw new Error('Failed to initiate OIDC login');
      }

      const data = await response.json();
      return data.auth_url;
    } catch (error) {
      console.error('OIDC login initiation error:', error);
      throw error;
    }
  }

  /**
   * Handle OIDC callback
   */
  async handleOIDCCallback(code: string, state: string): Promise<UserToken> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/oidc/callback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, state }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'OIDC authentication failed');
      }

      const data: UserToken = await response.json();
      
      // Store tokens and user data
      this.setTokens(data.access_token, data.refresh_token);
      this.setUser(data.user);
      
      // Notify listeners
      this.notifyListeners();
      
      return data;
    } catch (error) {
      console.error('OIDC callback error:', error);
      throw error;
    }
  }

  /**
   * Get authentication headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    if (!this.token) {
      return {};
    }
    
    return {
      'Authorization': `Bearer ${this.token}`,
    };
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.token && !!this.user;
  }

  /**
   * Get current user
   */
  getCurrentUserSync(): UserProfile | null {
    return this.user;
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Subscribe to auth state changes
   */
  subscribe(listener: (state: AuthState) => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Get current auth state
   */
  getAuthState(): AuthState {
    return {
      user: this.user,
      token: this.token,
      refreshToken: this.refreshToken,
      isAuthenticated: this.isAuthenticated(),
      isLoading: false,
    };
  }

  /**
   * Set authentication tokens
   */
  private setTokens(accessToken: string, refreshToken: string): void {
    this.token = accessToken;
    this.refreshToken = refreshToken;
    
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Set user data
   */
  private setUser(user: UserProfile): void {
    this.user = user;
    localStorage.setItem('user_profile', JSON.stringify(user));
  }

  /**
   * Get stored user from localStorage
   */
  private getStoredUser(): UserProfile | null {
    try {
      const stored = localStorage.getItem('user_profile');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  /**
   * Clear authentication data
   */
  private clearAuth(): void {
    this.token = null;
    this.refreshToken = null;
    this.user = null;
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_profile');
    
    this.notifyListeners();
  }

  /**
   * Notify all listeners of state changes
   */
  private notifyListeners(): void {
    const state = this.getAuthState();
    this.listeners.forEach(listener => listener(state));
  }

  /**
   * Set up automatic token refresh
   */
  private setupTokenRefresh(): void {
    if (!this.token || !this.refreshToken) {
      return;
    }

    // Check token expiration every 5 minutes
    setInterval(async () => {
      if (this.token && this.refreshToken) {
        try {
          // Try to refresh token
          await this.refreshAccessToken();
        } catch (error) {
          console.error('Automatic token refresh failed:', error);
          this.clearAuth();
        }
      }
    }, 5 * 60 * 1000); // 5 minutes
  }
}

// Create singleton instance
export const authService = new AuthService();
export default authService;