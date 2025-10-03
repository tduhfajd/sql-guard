/**
 * SQL Console component for SQL-Guard frontend
 * Interactive SQL query editor and execution interface
 */
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Play, Square, Download, History, Database, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { useQueryExecution, useQueryValidation, useDatabases, useQueryHistory } from '../../hooks/useQueries';
import { useAuth } from '../../hooks/useAuth';
import { QueryExecutionRequest, QueryExecutionResult } from '../../hooks/useQueries';

interface SQLConsoleProps {
  className?: string;
}

export function SQLConsole({ className }: SQLConsoleProps) {
  const { user, hasPermission } = useAuth();
  const { databases, isLoading: databasesLoading } = useDatabases();
  const { history, addToHistory } = useQueryHistory();
  
  const [sqlQuery, setSqlQuery] = useState('');
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [queryParameters, setQueryParameters] = useState<Record<string, any>>({});
  const [timeout, setTimeout] = useState<number>(30);
  const [activeTab, setActiveTab] = useState('query');
  
  const { executeQuery, isExecuting, result, error, clearResult } = useQueryExecution();
  const { validateQuery, isValidating, validationResult, clearValidation } = useQueryValidation();

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [sqlQuery]);

  // Check if user can execute queries
  const canExecuteQueries = hasPermission('execute_select_queries');

  const handleExecuteQuery = useCallback(async () => {
    if (!sqlQuery.trim() || !selectedDatabase) {
      return;
    }

    try {
      const request: QueryExecutionRequest = {
        sql_query: sqlQuery.trim(),
        database_id: selectedDatabase,
        parameters: queryParameters,
        timeout,
      };

      const executionResult = await executeQuery(request);
      addToHistory(executionResult);
      setActiveTab('results');
    } catch (err) {
      console.error('Query execution failed:', err);
    }
  }, [sqlQuery, selectedDatabase, queryParameters, timeout, executeQuery, addToHistory]);

  const handleValidateQuery = useCallback(async () => {
    if (!sqlQuery.trim() || !selectedDatabase) {
      return;
    }

    try {
      await validateQuery(sqlQuery.trim(), selectedDatabase);
    } catch (err) {
      console.error('Query validation failed:', err);
    }
  }, [sqlQuery, selectedDatabase, validateQuery]);

  const handleStopQuery = useCallback(() => {
    // TODO: Implement query cancellation
    console.log('Stop query requested');
  }, []);

  const handleExportResults = useCallback(() => {
    if (!result) return;

    const csvContent = [
      result.columns.join(','),
      ...result.results.map(row => 
        result.columns.map(col => 
          typeof row[col] === 'string' ? `"${row[col]}"` : row[col]
        ).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `query_results_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, [result]);

  const handleLoadFromHistory = useCallback((query: QueryExecutionResult) => {
    // TODO: Load query from history
    console.log('Load from history:', query);
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleExecuteQuery();
    }
  }, [handleExecuteQuery]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">SQL Console</h2>
          <p className="text-muted-foreground">
            Execute SQL queries against your databases
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {user?.role || 'Unknown'}
          </Badge>
        </div>
      </div>

      {/* Database Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Database Connection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Select
                value={selectedDatabase}
                onValueChange={setSelectedDatabase}
                disabled={databasesLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select database" />
                </SelectTrigger>
                <SelectContent>
                  {databases.map((db) => (
                    <SelectItem key={db.id} value={db.id}>
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4" />
                        <span>{db.name}</span>
                        <Badge variant="secondary" className="ml-2">
                          {db.type}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Timeout:</label>
              <Select value={timeout.toString()} onValueChange={(v) => setTimeout(Number(v))}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30s</SelectItem>
                  <SelectItem value="60">60s</SelectItem>
                  <SelectItem value="120">120s</SelectItem>
                  <SelectItem value="300">300s</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="query">Query Editor</TabsTrigger>
          <TabsTrigger value="results" disabled={!result}>
            Results
            {result && (
              <Badge variant="secondary" className="ml-2">
                {result.row_count} rows
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="history">
            History
            {history.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {history.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Query Editor Tab */}
        <TabsContent value="query" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">SQL Query</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                ref={textareaRef}
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter your SQL query here...&#10;&#10;Tip: Use Ctrl+Enter (Cmd+Enter on Mac) to execute"
                className="min-h-[200px] font-mono text-sm"
                disabled={!canExecuteQueries}
              />
              
              {/* Query Actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button
                    onClick={handleExecuteQuery}
                    disabled={!canExecuteQueries || !sqlQuery.trim() || !selectedDatabase || isExecuting}
                    className="flex items-center gap-2"
                  >
                    <Play className="h-4 w-4" />
                    {isExecuting ? 'Executing...' : 'Execute'}
                  </Button>
                  
                  {isExecuting && (
                    <Button
                      onClick={handleStopQuery}
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Square className="h-4 w-4" />
                      Stop
                    </Button>
                  )}
                  
                  <Button
                    onClick={handleValidateQuery}
                    disabled={!sqlQuery.trim() || !selectedDatabase || isValidating}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    {isValidating ? 'Validating...' : 'Validate'}
                  </Button>
                </div>
                
                <div className="text-sm text-muted-foreground">
                  {sqlQuery.length} characters
                </div>
              </div>

              {/* Validation Results */}
              {validationResult && (
                <Alert className={validationResult.is_valid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                  <div className="flex items-center gap-2">
                    {validationResult.is_valid ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    <AlertDescription>
                      {validationResult.is_valid ? 'Query is valid' : 'Query validation failed'}
                    </AlertDescription>
                  </div>
                  {validationResult.sql_validation.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium text-red-600">Errors:</p>
                      <ul className="list-disc list-inside text-sm text-red-600">
                        {validationResult.sql_validation.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {validationResult.sql_validation.warnings.length > 0 && (
                    <div className="mt-2">
                      <p className="font-medium text-yellow-600">Warnings:</p>
                      <ul className="list-disc list-inside text-sm text-yellow-600">
                        {validationResult.sql_validation.warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Alert>
              )}

              {/* Execution Error */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {result && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Query Results</CardTitle>
                  <div className="flex items-center gap-2">
                    <Button
                      onClick={handleExportResults}
                      variant="outline"
                      size="sm"
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Export CSV
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Execution Info */}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Rows: {result.row_count}</span>
                    <span>Execution time: {result.execution_time.toFixed(2)}s</span>
                    <span>Query ID: {result.query_id}</span>
                  </div>

                  {/* Warnings */}
                  {result.warnings.length > 0 && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <p className="font-medium">Warnings:</p>
                        <ul className="list-disc list-inside mt-1">
                          {result.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Results Table */}
                  <div className="border rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-muted">
                          <tr>
                            {result.columns.map((column) => (
                              <th key={column} className="px-4 py-2 text-left font-medium">
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {result.results.slice(0, 100).map((row, index) => (
                            <tr key={index} className="border-t">
                              {result.columns.map((column) => (
                                <td key={column} className="px-4 py-2 text-sm">
                                  {row[column]}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {result.results.length > 100 && (
                      <div className="px-4 py-2 bg-muted text-sm text-muted-foreground">
                        Showing first 100 rows of {result.row_count} total rows
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Query History</CardTitle>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No query history yet</p>
                  <p className="text-sm">Execute some queries to see them here</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {history.map((query, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                      onClick={() => handleLoadFromHistory(query)}
                    >
                      <div className="flex-1">
                        <div className="font-mono text-sm truncate">
                          {query.query_id}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {query.row_count} rows • {query.execution_time.toFixed(2)}s
                        </div>
                      </div>
                      <Badge variant="outline">
                        {query.columns.length} columns
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}