/**
 * Template Catalog component for SQL-Guard frontend
 * Displays and manages SQL templates with execution capabilities
 */
import React, { useState, useCallback } from 'react';
import { Play, Eye, Clock, CheckCircle, XCircle, Filter, Search, Download, BarChart3 } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { useTemplates, useApprovedTemplates, useTemplateExecution } from '../../hooks/useTemplates';
import { useDatabases } from '../../hooks/useQueries';
import { useAuth } from '../../hooks/useAuth';
import { SQLTemplate, TemplateExecutionRequest } from '../../hooks/useTemplates';

interface TemplateCatalogProps {
  className?: string;
}

export function TemplateCatalog({ className }: TemplateCatalogProps) {
  const { user, hasPermission } = useAuth();
  const { databases } = useDatabases();
  const { templates, isLoading, fetchTemplates } = useTemplates();
  const { templates: approvedTemplates } = useApprovedTemplates();
  const { executeTemplate, isExecuting, result, error } = useTemplateExecution();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<SQLTemplate | null>(null);
  const [executionParams, setExecutionParams] = useState<Record<string, any>>({});
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');

  const canExecuteTemplates = hasPermission('execute_approved_templates');
  const canManageTemplates = hasPermission('manage_templates');

  // Filter templates based on search and status
  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || template.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleExecuteTemplate = useCallback(async (template: SQLTemplate) => {
    if (!selectedDatabase) {
      alert('Please select a database first');
      return;
    }

    try {
      const request: TemplateExecutionRequest = {
        template_id: template.id,
        database_id: selectedDatabase,
        parameters: executionParams,
        timeout: 30,
      };

      await executeTemplate(request);
    } catch (err) {
      console.error('Template execution failed:', err);
    }
  }, [selectedDatabase, executionParams, executeTemplate]);

  const handleParameterChange = useCallback((paramName: string, value: any) => {
    setExecutionParams(prev => ({
      ...prev,
      [paramName]: value,
    }));
  }, []);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      DRAFT: { variant: 'secondary' as const, icon: Clock, label: 'Draft' },
      PENDING_APPROVAL: { variant: 'outline' as const, icon: Clock, label: 'Pending' },
      APPROVED: { variant: 'default' as const, icon: CheckCircle, label: 'Approved' },
      REJECTED: { variant: 'destructive' as const, icon: XCircle, label: 'Rejected' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.DRAFT;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Template Catalog</h2>
          <p className="text-muted-foreground">
            Browse and execute approved SQL templates
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {templates.length} templates
          </Badge>
          {canManageTemplates && (
            <Button variant="outline">
              Create Template
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search templates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="PENDING_APPROVAL">Pending Approval</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Database Selection for Execution */}
      {canExecuteTemplates && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Execution Settings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium mb-2 block">Target Database</label>
                <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select database for execution" />
                  </SelectTrigger>
                  <SelectContent>
                    {databases.map((db) => (
                      <SelectItem key={db.id} value={db.id}>
                        {db.name} ({db.type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-3/4"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-3 bg-muted rounded"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : filteredTemplates.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">No templates found</h3>
            <p className="text-muted-foreground">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filter criteria'
                : 'No templates have been created yet'
              }
            </p>
          </div>
        ) : (
          filteredTemplates.map((template) => (
            <Card key={template.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-2">{template.name}</CardTitle>
                    <div className="flex items-center gap-2 mb-2">
                      {getStatusBadge(template.status)}
                      <Badge variant="outline">
                        v{template.version}
                      </Badge>
                    </div>
                  </div>
                </div>
                {template.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {template.description}
                  </p>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Parameters Preview */}
                  {Object.keys(template.parameters).length > 0 && (
                    <div>
                      <p className="text-sm font-medium mb-2">Parameters:</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(template.parameters).map(([name, param]) => (
                          <Badge key={name} variant="secondary" className="text-xs">
                            {name}: {param.type}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm" className="flex-1">
                          <Eye className="h-4 w-4 mr-2" />
                          View
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl">
                        <DialogHeader>
                          <DialogTitle>{template.name}</DialogTitle>
                        </DialogHeader>
                        <Tabs defaultValue="sql" className="mt-4">
                          <TabsList>
                            <TabsTrigger value="sql">SQL Content</TabsTrigger>
                            <TabsTrigger value="parameters">Parameters</TabsTrigger>
                            <TabsTrigger value="execute">Execute</TabsTrigger>
                          </TabsList>
                          
                          <TabsContent value="sql" className="mt-4">
                            <div className="bg-muted p-4 rounded-lg">
                              <pre className="text-sm font-mono whitespace-pre-wrap">
                                {template.sql_content}
                              </pre>
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="parameters" className="mt-4">
                            <div className="space-y-4">
                              {Object.entries(template.parameters).map(([name, param]) => (
                                <div key={name} className="space-y-2">
                                  <label className="text-sm font-medium">
                                    {name} ({param.type})
                                    {param.required && <span className="text-red-500 ml-1">*</span>}
                                  </label>
                                  <Input
                                    placeholder={param.description || `Enter ${name}`}
                                    onChange={(e) => handleParameterChange(name, e.target.value)}
                                  />
                                  {param.description && (
                                    <p className="text-xs text-muted-foreground">
                                      {param.description}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          </TabsContent>
                          
                          <TabsContent value="execute" className="mt-4">
                            <div className="space-y-4">
                              <div className="flex items-center gap-4">
                                <div className="flex-1">
                                  <label className="text-sm font-medium mb-2 block">Target Database</label>
                                  <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select database" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {databases.map((db) => (
                                        <SelectItem key={db.id} value={db.id}>
                                          {db.name} ({db.type})
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                              
                              {Object.keys(template.parameters).length > 0 && (
                                <div className="space-y-4">
                                  <h4 className="font-medium">Parameters</h4>
                                  {Object.entries(template.parameters).map(([name, param]) => (
                                    <div key={name} className="space-y-2">
                                      <label className="text-sm font-medium">
                                        {name} ({param.type})
                                        {param.required && <span className="text-red-500 ml-1">*</span>}
                                      </label>
                                      <Input
                                        placeholder={param.description || `Enter ${name}`}
                                        onChange={(e) => handleParameterChange(name, e.target.value)}
                                      />
                                    </div>
                                  ))}
                                </div>
                              )}
                              
                              <Button
                                onClick={() => handleExecuteTemplate(template)}
                                disabled={!canExecuteTemplates || !selectedDatabase || isExecuting}
                                className="w-full"
                              >
                                <Play className="h-4 w-4 mr-2" />
                                {isExecuting ? 'Executing...' : 'Execute Template'}
                              </Button>
                            </div>
                          </TabsContent>
                        </Tabs>
                      </DialogContent>
                    </Dialog>

                    {template.status === 'APPROVED' && canExecuteTemplates && (
                      <Button
                        size="sm"
                        onClick={() => {
                          setSelectedTemplate(template);
                          setExecutionParams({});
                        }}
                        disabled={!selectedDatabase}
                        className="flex-1"
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Execute
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Execution Results */}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Execution Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>Rows: {result.row_count}</span>
                <span>Execution time: {result.execution_time.toFixed(2)}s</span>
                <span>Query ID: {result.query_id}</span>
              </div>

              {result.warnings.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-800 mb-2">Warnings:</h4>
                  <ul className="list-disc list-inside text-sm text-yellow-700">
                    {result.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

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
                      {result.results.slice(0, 10).map((row, index) => (
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
                {result.results.length > 10 && (
                  <div className="px-4 py-2 bg-muted text-sm text-muted-foreground">
                    Showing first 10 rows of {result.row_count} total rows
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Execution Error */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-800">
              <XCircle className="h-4 w-4" />
              <span className="font-medium">Execution Error</span>
            </div>
            <p className="text-red-700 mt-2">{error}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}