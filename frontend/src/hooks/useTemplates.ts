/**
 * Template management hooks for SQL-Guard frontend
 * React hooks for managing SQL templates and their execution
 */
import { useState, useCallback } from 'react';
import { apiService, API_ENDPOINTS } from '../services/api';

export interface SQLTemplate {
  id: string;
  name: string;
  description?: string;
  sql_content: string;
  parameters: Record<string, ParameterDefinition>;
  version: number;
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED';
  require_approval: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
}

export interface ParameterDefinition {
  type: 'string' | 'integer' | 'float' | 'boolean' | 'date' | 'datetime' | 'uuid';
  required: boolean;
  default?: any;
  description?: string;
  validation?: Record<string, any>;
}

export interface TemplateCreateRequest {
  name: string;
  description?: string;
  sql_content: string;
  parameters?: Record<string, ParameterDefinition>;
  require_approval?: boolean;
}

export interface TemplateUpdateRequest {
  name?: string;
  description?: string;
  sql_content?: string;
  parameters?: Record<string, ParameterDefinition>;
  require_approval?: boolean;
}

export interface TemplateExecutionRequest {
  template_id: string;
  database_id: string;
  parameters: Record<string, any>;
  timeout?: number;
}

export interface TemplateExecutionResult {
  query_id: string;
  results: any[];
  columns: string[];
  row_count: number;
  execution_time: number;
  warnings: string[];
}

export interface TemplateValidationResult {
  is_valid: boolean;
  sql_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
    estimated_cost: number;
  };
  parameter_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  security_checks: Record<string, any>;
}

export interface TemplateVersion {
  id: string;
  version: number;
  status: string;
  created_at: string;
  changes?: string;
}

export interface TemplateUsageStats {
  template_id: string;
  total_executions: number;
  last_executed?: string;
  average_execution_time: number;
  success_rate: number;
  most_common_parameters: Record<string, any>;
}

/**
 * Hook for managing templates list
 */
export function useTemplates() {
  const [templates, setTemplates] = useState<SQLTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchTemplates = useCallback(async (
    statusFilter?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{ templates: SQLTemplate[]; total: number }> => {
    try {
      setIsLoading(true);
      setError(null);

      const params: Record<string, any> = { limit, offset };
      if (statusFilter) {
        params.status_filter = statusFilter;
      }

      const response = await apiService.get<{
        templates: SQLTemplate[];
        total: number;
        limit: number;
        offset: number;
      }>(API_ENDPOINTS.TEMPLATES.LIST, params);

      setTemplates(response.data.templates);
      setTotal(response.data.total);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch templates';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch templates on mount
  React.useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  return {
    templates,
    isLoading,
    error,
    total,
    fetchTemplates,
  };
}

/**
 * Hook for creating templates
 */
export function useTemplateCreation() {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createTemplate = useCallback(async (data: TemplateCreateRequest): Promise<SQLTemplate> => {
    try {
      setIsCreating(true);
      setError(null);

      const response = await apiService.post<SQLTemplate>(
        API_ENDPOINTS.TEMPLATES.CREATE,
        data
      );

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create template';
      setError(errorMessage);
      throw err;
    } finally {
      setIsCreating(false);
    }
  }, []);

  return {
    createTemplate,
    isCreating,
    error,
  };
}

/**
 * Hook for updating templates
 */
export function useTemplateUpdate() {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateTemplate = useCallback(async (
    templateId: string,
    data: TemplateUpdateRequest
  ): Promise<SQLTemplate> => {
    try {
      setIsUpdating(true);
      setError(null);

      const response = await apiService.put<SQLTemplate>(
        `${API_ENDPOINTS.TEMPLATES.UPDATE}/${templateId}`,
        data
      );

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update template';
      setError(errorMessage);
      throw err;
    } finally {
      setIsUpdating(false);
    }
  }, []);

  return {
    updateTemplate,
    isUpdating,
    error,
  };
}

/**
 * Hook for deleting templates
 */
export function useTemplateDeletion() {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteTemplate = useCallback(async (templateId: string): Promise<void> => {
    try {
      setIsDeleting(true);
      setError(null);

      await apiService.delete(`${API_ENDPOINTS.TEMPLATES.DELETE}/${templateId}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete template';
      setError(errorMessage);
      throw err;
    } finally {
      setIsDeleting(false);
    }
  }, []);

  return {
    deleteTemplate,
    isDeleting,
    error,
  };
}

/**
 * Hook for getting a single template
 */
export function useTemplate(templateId: string | null) {
  const [template, setTemplate] = useState<SQLTemplate | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTemplate = useCallback(async (): Promise<SQLTemplate> => {
    if (!templateId) {
      setTemplate(null);
      return null as any;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<SQLTemplate>(
        `${API_ENDPOINTS.TEMPLATES.GET}/${templateId}`
      );

      setTemplate(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch template';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [templateId]);

  // Fetch template when templateId changes
  React.useEffect(() => {
    fetchTemplate();
  }, [fetchTemplate]);

  return {
    template,
    isLoading,
    error,
    refetch: fetchTemplate,
  };
}

/**
 * Hook for executing templates
 */
export function useTemplateExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<TemplateExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeTemplate = useCallback(async (
    request: TemplateExecutionRequest
  ): Promise<TemplateExecutionResult> => {
    try {
      setIsExecuting(true);
      setError(null);
      setResult(null);

      const response = await apiService.post<TemplateExecutionResult>(
        `${API_ENDPOINTS.TEMPLATES.EXECUTE}/${request.template_id}`,
        request
      );

      setResult(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Template execution failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsExecuting(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    executeTemplate,
    isExecuting,
    result,
    error,
    clearResult,
  };
}

/**
 * Hook for validating templates
 */
export function useTemplateValidation() {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<TemplateValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateTemplate = useCallback(async (data: TemplateCreateRequest): Promise<TemplateValidationResult> => {
    try {
      setIsValidating(true);
      setError(null);
      setValidationResult(null);

      const response = await apiService.post<TemplateValidationResult>(
        API_ENDPOINTS.TEMPLATES.VALIDATE,
        data
      );

      setValidationResult(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Template validation failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsValidating(false);
    }
  }, []);

  const clearValidation = useCallback(() => {
    setValidationResult(null);
    setError(null);
  }, []);

  return {
    validateTemplate,
    isValidating,
    validationResult,
    error,
    clearValidation,
  };
}

/**
 * Hook for template version history
 */
export function useTemplateVersions(templateId: string | null) {
  const [versions, setVersions] = useState<TemplateVersion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVersions = useCallback(async (): Promise<TemplateVersion[]> => {
    if (!templateId) {
      setVersions([]);
      return [];
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<{ versions: TemplateVersion[] }>(
        `${API_ENDPOINTS.TEMPLATES.VERSIONS}/${templateId}`
      );

      setVersions(response.data.versions);
      return response.data.versions;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch template versions';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [templateId]);

  // Fetch versions when templateId changes
  React.useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  return {
    versions,
    isLoading,
    error,
    refetch: fetchVersions,
  };
}

/**
 * Hook for template usage statistics
 */
export function useTemplateUsageStats(templateId: string | null) {
  const [stats, setStats] = useState<TemplateUsageStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async (): Promise<TemplateUsageStats> => {
    if (!templateId) {
      setStats(null);
      return null as any;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<TemplateUsageStats>(
        `${API_ENDPOINTS.TEMPLATES.USAGE}/${templateId}`
      );

      setStats(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch template usage stats';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [templateId]);

  // Fetch stats when templateId changes
  React.useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    isLoading,
    error,
    refetch: fetchStats,
  };
}

/**
 * Hook for approved templates only
 */
export function useApprovedTemplates() {
  const { templates, isLoading, error, fetchTemplates } = useTemplates();

  const approvedTemplates = React.useMemo(() => {
    return templates.filter(template => template.status === 'APPROVED');
  }, [templates]);

  const fetchApprovedTemplates = useCallback(() => {
    return fetchTemplates('APPROVED');
  }, [fetchTemplates]);

  return {
    templates: approvedTemplates,
    isLoading,
    error,
    fetchTemplates: fetchApprovedTemplates,
  };
}