/**
 * Authentication hooks for SQL-Guard frontend
 * React hooks for managing authentication state and operations
 */
import { useState, useEffect, useCallback } from 'react';
import { authService, AuthState } from '../services/auth';
import { UserProfile, UserLogin, UserToken } from '../types/auth';

export interface UseAuthReturn {
  // State
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: UserLogin) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  
  // OIDC
  initiateOIDCLogin: () => Promise<string>;
  handleOIDCCallback: (code: string, state: string) => Promise<void>;
  
  // Permissions
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

/**
 * Main authentication hook
 */
export function useAuth(): UseAuthReturn {
  const [authState, setAuthState] = useState<AuthState>(authService.getAuthState());
  const [error, setError] = useState<string | null>(null);

  // Subscribe to auth state changes
  useEffect(() => {
    const unsubscribe = authService.subscribe(setAuthState);
    return unsubscribe;
  }, []);

  // Login function
  const login = useCallback(async (credentials: UserLogin) => {
    try {
      setError(null);
      await authService.login(credentials);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      setError(null);
      await authService.logout();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Logout failed');
    }
  }, []);

  // Refresh token function
  const refreshToken = useCallback(async () => {
    try {
      setError(null);
      await authService.refreshAccessToken();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Token refresh failed');
      throw err;
    }
  }, []);

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // OIDC login initiation
  const initiateOIDCLogin = useCallback(async (): Promise<string> => {
    try {
      setError(null);
      return await authService.initiateOIDCLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OIDC login initiation failed');
      throw err;
    }
  }, []);

  // OIDC callback handling
  const handleOIDCCallback = useCallback(async (code: string, state: string) => {
    try {
      setError(null);
      await authService.handleOIDCCallback(code, state);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OIDC authentication failed');
      throw err;
    }
  }, []);

  // Permission checking functions
  const hasPermission = useCallback((permission: string): boolean => {
    if (!authState.user) return false;
    return authState.user.permissions?.includes(permission) || false;
  }, [authState.user]);

  const hasRole = useCallback((role: string): boolean => {
    if (!authState.user) return false;
    return authState.user.role === role;
  }, [authState.user]);

  const hasAnyRole = useCallback((roles: string[]): boolean => {
    if (!authState.user) return false;
    return roles.includes(authState.user.role);
  }, [authState.user]);

  return {
    // State
    user: authState.user,
    token: authState.token,
    isAuthenticated: authState.isAuthenticated,
    isLoading: authState.isLoading,
    error,

    // Actions
    login,
    logout,
    refreshToken,
    clearError,
    
    // OIDC
    initiateOIDCLogin,
    handleOIDCCallback,
    
    // Permissions
    hasPermission,
    hasRole,
    hasAnyRole,
  };
}

/**
 * Hook for checking specific permissions
 */
export function usePermission(permission: string): boolean {
  const { hasPermission } = useAuth();
  return hasPermission(permission);
}

/**
 * Hook for checking specific roles
 */
export function useRole(role: string): boolean {
  const { hasRole } = useAuth();
  return hasRole(role);
}

/**
 * Hook for checking multiple roles
 */
export function useAnyRole(roles: string[]): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(roles);
}

/**
 * Hook for admin-only functionality
 */
export function useAdmin(): boolean {
  return useRole('ADMIN');
}

/**
 * Hook for approver functionality
 */
export function useApprover(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['APPROVER', 'ADMIN']);
}

/**
 * Hook for operator functionality
 */
export function useOperator(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['OPERATOR', 'APPROVER', 'ADMIN']);
}

/**
 * Hook for viewer functionality
 */
export function useViewer(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['VIEWER', 'OPERATOR', 'APPROVER', 'ADMIN']);
}

/**
 * Hook for getting user permissions
 */
export function useUserPermissions(): string[] {
  const { user } = useAuth();
  return user?.permissions || [];
}

/**
 * Hook for getting user role
 */
export function useUserRole(): string | null {
  const { user } = useAuth();
  return user?.role || null;
}

/**
 * Hook for checking if user can execute queries
 */
export function useCanExecuteQueries(): boolean {
  return usePermission('execute_select_queries');
}

/**
 * Hook for checking if user can manage templates
 */
export function useCanManageTemplates(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['OPERATOR', 'APPROVER', 'ADMIN']);
}

/**
 * Hook for checking if user can approve templates
 */
export function useCanApproveTemplates(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['APPROVER', 'ADMIN']);
}

/**
 * Hook for checking if user can manage users
 */
export function useCanManageUsers(): boolean {
  return usePermission('manage_users');
}

/**
 * Hook for checking if user can view audit logs
 */
export function useCanViewAuditLogs(): boolean {
  const { hasAnyRole } = useAuth();
  return hasAnyRole(['APPROVER', 'ADMIN']);
}

/**
 * Hook for checking if user can configure policies
 */
export function useCanConfigurePolicies(): boolean {
  return usePermission('configure_security_policies');
}

/**
 * Hook for checking if user can view all audit logs
 */
export function useCanViewAllAuditLogs(): boolean {
  return usePermission('view_all_audit_logs');
}

/**
 * Hook for checking if user can export audit logs
 */
export function useCanExportAuditLogs(): boolean {
  return usePermission('export_audit_logs');
}

/**
 * Hook for checking if user can view system statistics
 */
export function useCanViewSystemStatistics(): boolean {
  return usePermission('view_system_statistics');
}

/**
 * Hook for checking if user can perform system administration
 */
export function useCanPerformSystemAdministration(): boolean {
  return usePermission('system_administration');
}