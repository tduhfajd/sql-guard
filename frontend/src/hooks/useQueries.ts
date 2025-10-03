/**
 * Query execution hooks for SQL-Guard frontend
 * React hooks for managing SQL query execution and validation
 */
import { useState, useCallback } from 'react';
import { apiService, API_ENDPOINTS } from '../services/api';
import { websocketService } from '../services/websocket';

export interface QueryExecutionRequest {
  sql_query: string;
  database_id: string;
  parameters?: Record<string, any>;
  timeout?: number;
}

export interface QueryExecutionResult {
  query_id: string;
  results: any[];
  columns: string[];
  row_count: number;
  execution_time: number;
  warnings: string[];
}

export interface QueryValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  estimated_cost: number;
  security_checks: Record<string, any>;
  complexity_score: number;
  table_names: string[];
  column_names: string[];
  modified_sql?: string;
}

export interface QueryStatus {
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
}

export interface Database {
  id: string;
  name: string;
  type: string;
  description: string;
  is_active: boolean;
  max_connections: number;
}

export interface Schema {
  name: string;
  description: string;
  table_count: number;
}

export interface Table {
  name: string;
  description: string;
  row_count: number;
}

/**
 * Hook for executing SQL queries
 */
export function useQueryExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<QueryExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeQuery = useCallback(async (request: QueryExecutionRequest): Promise<QueryExecutionResult> => {
    try {
      setIsExecuting(true);
      setError(null);
      setResult(null);

      const response = await apiService.post<QueryExecutionResult>(
        API_ENDPOINTS.QUERIES.EXECUTE,
        request
      );

      setResult(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query execution failed';
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
    executeQuery,
    isExecuting,
    result,
    error,
    clearResult,
  };
}

/**
 * Hook for validating SQL queries
 */
export function useQueryValidation() {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<QueryValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateQuery = useCallback(async (sql: string, databaseId: string): Promise<QueryValidationResult> => {
    try {
      setIsValidating(true);
      setError(null);
      setValidationResult(null);

      const response = await apiService.post<QueryValidationResult>(
        API_ENDPOINTS.QUERIES.VALIDATE,
        {
          sql_query: sql,
          database_id: databaseId,
        }
      );

      setValidationResult(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query validation failed';
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
    validateQuery,
    isValidating,
    validationResult,
    error,
    clearValidation,
  };
}

/**
 * Hook for monitoring query status
 */
export function useQueryStatus(queryId: string | null) {
  const [status, setStatus] = useState<QueryStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getStatus = useCallback(async (): Promise<QueryStatus> => {
    if (!queryId) {
      throw new Error('Query ID is required');
    }

    try {
      setError(null);

      const response = await apiService.get<QueryStatus>(
        `${API_ENDPOINTS.QUERIES.STATUS}/${queryId}`
      );

      setStatus(response.data);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get query status';
      setError(errorMessage);
      throw err;
    }
  }, [queryId]);

  // Subscribe to real-time updates
  React.useEffect(() => {
    if (!queryId) return;

    const unsubscribe = websocketService.onQueryUpdate((message) => {
      if (message.data.query_id === queryId) {
        setStatus({
          status: message.data.status,
          progress: message.data.progress || 100,
          message: message.data.status === 'completed' ? 'Query completed' : 
                   message.data.status === 'failed' ? message.data.error || 'Query failed' :
                   'Query running...',
        });
      }
    });

    return unsubscribe;
  }, [queryId]);

  return {
    getStatus,
    status,
    error,
  };
}

/**
 * Hook for getting available databases
 */
export function useDatabases() {
  const [databases, setDatabases] = useState<Database[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDatabases = useCallback(async (): Promise<Database[]> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<{ databases: Database[]; total: number }>(
        API_ENDPOINTS.QUERIES.DATABASES
      );

      setDatabases(response.data.databases);
      return response.data.databases;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch databases';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch databases on mount
  React.useEffect(() => {
    fetchDatabases();
  }, [fetchDatabases]);

  return {
    databases,
    isLoading,
    error,
    refetch: fetchDatabases,
  };
}

/**
 * Hook for getting schemas in a database
 */
export function useSchemas(databaseId: string | null) {
  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchemas = useCallback(async (): Promise<Schema[]> => {
    if (!databaseId) {
      setSchemas([]);
      return [];
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<{ schemas: Schema[]; total: number }>(
        `${API_ENDPOINTS.QUERIES.SCHEMAS}/${databaseId}`
      );

      setSchemas(response.data.schemas);
      return response.data.schemas;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch schemas';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [databaseId]);

  // Fetch schemas when databaseId changes
  React.useEffect(() => {
    fetchSchemas();
  }, [fetchSchemas]);

  return {
    schemas,
    isLoading,
    error,
    refetch: fetchSchemas,
  };
}

/**
 * Hook for getting tables in a schema
 */
export function useTables(databaseId: string | null, schemaName: string | null) {
  const [tables, setTables] = useState<Table[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTables = useCallback(async (): Promise<Table[]> => {
    if (!databaseId || !schemaName) {
      setTables([]);
      return [];
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await apiService.get<{ tables: Table[]; total: number }>(
        `${API_ENDPOINTS.QUERIES.TABLES}/${databaseId}/${schemaName}`
      );

      setTables(response.data.tables);
      return response.data.tables;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tables';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [databaseId, schemaName]);

  // Fetch tables when databaseId or schemaName changes
  React.useEffect(() => {
    fetchTables();
  }, [fetchTables]);

  return {
    tables,
    isLoading,
    error,
    refetch: fetchTables,
  };
}

/**
 * Hook for executing template queries
 */
export function useTemplateExecution() {
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<QueryExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeTemplate = useCallback(async (
    templateId: string,
    databaseId: string,
    parameters: Record<string, any>,
    timeout?: number
  ): Promise<QueryExecutionResult> => {
    try {
      setIsExecuting(true);
      setError(null);
      setResult(null);

      const response = await apiService.post<QueryExecutionResult>(
        API_ENDPOINTS.QUERIES.TEMPLATE_EXECUTE,
        {
          template_id: templateId,
          database_id: databaseId,
          parameters,
          timeout,
        }
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
 * Hook for query history
 */
export function useQueryHistory() {
  const [history, setHistory] = useState<QueryExecutionResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async (): Promise<QueryExecutionResult[]> => {
    try {
      setIsLoading(true);
      setError(null);

      // This would typically fetch from a query history endpoint
      // For now, we'll simulate with empty array
      const response = await apiService.get<{ queries: QueryExecutionResult[] }>(
        '/api/queries/history'
      );

      setHistory(response.data.queries || []);
      return response.data.queries || [];
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch query history';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addToHistory = useCallback((query: QueryExecutionResult) => {
    setHistory(prev => [query, ...prev.slice(0, 49)]); // Keep last 50 queries
  }, []);

  return {
    history,
    isLoading,
    error,
    fetchHistory,
    addToHistory,
  };
}