/**
 * Audit Log component for SQL-Guard frontend
 * Displays comprehensive audit logs with filtering and export capabilities
 */
import React, { useState, useCallback } from 'react';
import { Download, Filter, Search, Calendar, User, Database, AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../hooks/useAuth';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  message: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  database_id?: string;
  query_id?: string;
  template_id?: string;
  approval_id?: string;
}

interface AuditLogProps {
  className?: string;
}

export function AuditLog({ className }: AuditLogProps) {
  const { user, hasPermission } = useAuth();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [resourceFilter, setResourceFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const canViewAuditLogs = hasPermission('view_audit_logs');
  const canViewAllAuditLogs = hasPermission('view_all_audit_logs');
  const canExportAuditLogs = hasPermission('export_audit_logs');

  // Mock data - in real implementation, this would come from API
  const mockAuditLogs: AuditLogEntry[] = [
    {
      id: '1',
      timestamp: '2024-01-15T14:30:00Z',
      user_id: 'user1',
      user_email: 'john.doe@company.com',
      action: 'QUERY_EXECUTED',
      resource_type: 'QUERY',
      resource_id: 'q1',
      severity: 'INFO',
      message: 'SELECT query executed successfully',
      details: { row_count: 150, execution_time: 0.45 },
      ip_address: '192.168.1.100',
      database_id: 'db1',
      query_id: 'q1',
    },
    {
      id: '2',
      timestamp: '2024-01-15T14:25:00Z',
      user_id: 'user2',
      user_email: 'jane.smith@company.com',
      action: 'TEMPLATE_CREATED',
      resource_type: 'TEMPLATE',
      resource_id: 't1',
      severity: 'INFO',
      message: 'SQL template created',
      details: { template_name: 'User Report', version: 1 },
      ip_address: '192.168.1.101',
      template_id: 't1',
    },
    {
      id: '3',
      timestamp: '2024-01-15T14:20:00Z',
      user_id: 'user3',
      user_email: 'mike.wilson@company.com',
      action: 'SECURITY_VIOLATION',
      resource_type: 'SECURITY',
      resource_id: 's1',
      severity: 'WARNING',
      message: 'Attempted DDL operation blocked',
      details: { blocked_query: 'DROP TABLE users', reason: 'DDL not allowed for VIEWER role' },
      ip_address: '192.168.1.102',
    },
    {
      id: '4',
      timestamp: '2024-01-15T14:15:00Z',
      user_id: 'user1',
      user_email: 'john.doe@company.com',
      action: 'TEMPLATE_APPROVED',
      resource_type: 'APPROVAL',
      resource_id: 'a1',
      severity: 'INFO',
      message: 'Template approval processed',
      details: { template_name: 'Sales Report', action: 'APPROVED', reviewer: 'admin@company.com' },
      ip_address: '192.168.1.100',
      approval_id: 'a1',
    },
    {
      id: '5',
      timestamp: '2024-01-15T14:10:00Z',
      user_id: 'user4',
      user_email: 'sarah.jones@company.com',
      action: 'LOGIN_SUCCESS',
      resource_type: 'AUTH',
      resource_id: 'auth1',
      severity: 'INFO',
      message: 'User logged in successfully',
      details: { login_method: 'OIDC', provider: 'keycloak' },
      ip_address: '192.168.1.103',
    },
  ];

  // Filter audit logs based on search and filters
  const filteredLogs = mockAuditLogs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.user_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.action.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = severityFilter === 'all' || log.severity === severityFilter;
    const matchesAction = actionFilter === 'all' || log.action === actionFilter;
    const matchesResource = resourceFilter === 'all' || log.resource_type === resourceFilter;
    
    // Filter by user if not admin
    const matchesUser = canViewAllAuditLogs || log.user_id === user?.id;
    
    return matchesSearch && matchesSeverity && matchesAction && matchesResource && matchesUser;
  });

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    try {
      // TODO: Implement actual export API call
      console.log('Exporting audit logs...');
      
      // Simulate export
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create CSV content
      const csvContent = [
        ['Timestamp', 'User', 'Action', 'Resource Type', 'Severity', 'Message', 'IP Address'].join(','),
        ...filteredLogs.map(log => [
          log.timestamp,
          log.user_email,
          log.action,
          log.resource_type,
          log.severity,
          `"${log.message}"`,
          log.ip_address || '',
        ].join(','))
      ].join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  }, [filteredLogs]);

  const getSeverityBadge = (severity: string) => {
    const severityConfig = {
      INFO: { variant: 'secondary' as const, icon: Info, color: 'text-blue-600' },
      WARNING: { variant: 'outline' as const, icon: AlertTriangle, color: 'text-yellow-600' },
      ERROR: { variant: 'destructive' as const, icon: XCircle, color: 'text-red-600' },
      CRITICAL: { variant: 'destructive' as const, icon: AlertTriangle, color: 'text-red-800' },
    };

    const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.INFO;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className={`flex items-center gap-1 ${config.color}`}>
        <Icon className="h-3 w-3" />
        {severity}
      </Badge>
    );
  };

  const getActionBadge = (action: string) => {
    const actionColors = {
      'QUERY_EXECUTED': 'bg-green-100 text-green-800',
      'TEMPLATE_CREATED': 'bg-blue-100 text-blue-800',
      'TEMPLATE_APPROVED': 'bg-green-100 text-green-800',
      'TEMPLATE_REJECTED': 'bg-red-100 text-red-800',
      'SECURITY_VIOLATION': 'bg-red-100 text-red-800',
      'LOGIN_SUCCESS': 'bg-green-100 text-green-800',
      'LOGIN_FAILED': 'bg-red-100 text-red-800',
      'PERMISSION_DENIED': 'bg-yellow-100 text-yellow-800',
    };

    const colorClass = actionColors[action as keyof typeof actionColors] || 'bg-gray-100 text-gray-800';

    return (
      <Badge className={colorClass}>
        {action.replace(/_/g, ' ')}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!canViewAuditLogs) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Alert>
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to view audit logs.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Audit Log</h2>
          <p className="text-muted-foreground">
            Comprehensive audit trail of all system activities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {filteredLogs.length} entries
          </Badge>
          {canExportAuditLogs && (
            <Button
              onClick={handleExport}
              disabled={isExporting}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              {isExporting ? 'Exporting...' : 'Export CSV'}
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="CRITICAL">Critical</SelectItem>
                <SelectItem value="ERROR">Error</SelectItem>
                <SelectItem value="WARNING">Warning</SelectItem>
                <SelectItem value="INFO">Info</SelectItem>
              </SelectContent>
            </Select>
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="QUERY_EXECUTED">Query Executed</SelectItem>
                <SelectItem value="TEMPLATE_CREATED">Template Created</SelectItem>
                <SelectItem value="TEMPLATE_APPROVED">Template Approved</SelectItem>
                <SelectItem value="TEMPLATE_REJECTED">Template Rejected</SelectItem>
                <SelectItem value="SECURITY_VIOLATION">Security Violation</SelectItem>
                <SelectItem value="LOGIN_SUCCESS">Login Success</SelectItem>
                <SelectItem value="LOGIN_FAILED">Login Failed</SelectItem>
                <SelectItem value="PERMISSION_DENIED">Permission Denied</SelectItem>
              </SelectContent>
            </Select>
            <Select value={resourceFilter} onValueChange={setResourceFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Resource" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                <SelectItem value="QUERY">Query</SelectItem>
                <SelectItem value="TEMPLATE">Template</SelectItem>
                <SelectItem value="APPROVAL">Approval</SelectItem>
                <SelectItem value="AUTH">Authentication</SelectItem>
                <SelectItem value="SECURITY">Security</SelectItem>
                <SelectItem value="USER">User</SelectItem>
              </SelectContent>
            </Select>
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger>
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">Last 24 hours</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="all">All time</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs */}
      <div className="space-y-4">
        {filteredLogs.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No audit logs found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || severityFilter !== 'all' || actionFilter !== 'all' || resourceFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria'
                    : 'No audit logs are available for the selected time range'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredLogs.map((log) => (
            <Card key={log.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{log.message}</h3>
                      {getSeverityBadge(log.severity)}
                      {getActionBadge(log.action)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(log.timestamp)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        <span>{log.user_email}</span>
                      </div>
                      {log.ip_address && (
                        <div className="flex items-center gap-2">
                          <Database className="h-4 w-4" />
                          <span>{log.ip_address}</span>
                        </div>
                      )}
                    </div>

                    {log.details && Object.keys(log.details).length > 0 && (
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-sm font-medium mb-2">Details:</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                          {Object.entries(log.details).map(([key, value]) => (
                            <div key={key}>
                              <span className="font-medium">{key}:</span> {String(value)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Resource Links */}
                    <div className="flex items-center gap-2">
                      {log.query_id && (
                        <Badge variant="outline" className="text-xs">
                          Query: {log.query_id}
                        </Badge>
                      )}
                      {log.template_id && (
                        <Badge variant="outline" className="text-xs">
                          Template: {log.template_id}
                        </Badge>
                      )}
                      {log.approval_id && (
                        <Badge variant="outline" className="text-xs">
                          Approval: {log.approval_id}
                        </Badge>
                      )}
                      {log.database_id && (
                        <Badge variant="outline" className="text-xs">
                          Database: {log.database_id}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Info className="h-4 w-4 mr-2" />
                          Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Audit Log Details</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4 mt-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium mb-2">Basic Information</h4>
                              <div className="space-y-2 text-sm">
                                <div><span className="font-medium">ID:</span> {log.id}</div>
                                <div><span className="font-medium">Timestamp:</span> {formatDate(log.timestamp)}</div>
                                <div><span className="font-medium">User:</span> {log.user_email}</div>
                                <div><span className="font-medium">Action:</span> {log.action}</div>
                                <div><span className="font-medium">Resource Type:</span> {log.resource_type}</div>
                                <div><span className="font-medium">Resource ID:</span> {log.resource_id}</div>
                                <div><span className="font-medium">Severity:</span> {log.severity}</div>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-medium mb-2">Technical Details</h4>
                              <div className="space-y-2 text-sm">
                                {log.ip_address && (
                                  <div><span className="font-medium">IP Address:</span> {log.ip_address}</div>
                                )}
                                {log.user_agent && (
                                  <div><span className="font-medium">User Agent:</span> {log.user_agent}</div>
                                )}
                                {log.database_id && (
                                  <div><span className="font-medium">Database:</span> {log.database_id}</div>
                                )}
                                {log.query_id && (
                                  <div><span className="font-medium">Query ID:</span> {log.query_id}</div>
                                )}
                                {log.template_id && (
                                  <div><span className="font-medium">Template ID:</span> {log.template_id}</div>
                                )}
                                {log.approval_id && (
                                  <div><span className="font-medium">Approval ID:</span> {log.approval_id}</div>
                                )}
                              </div>
                            </div>
                          </div>
                          
                          <div>
                            <h4 className="font-medium mb-2">Message</h4>
                            <div className="bg-muted p-3 rounded-lg">
                              <p className="text-sm">{log.message}</p>
                            </div>
                          </div>
                          
                          {log.details && Object.keys(log.details).length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">Additional Details</h4>
                              <div className="bg-muted p-3 rounded-lg">
                                <pre className="text-sm whitespace-pre-wrap">
                                  {JSON.stringify(log.details, null, 2)}
                                </pre>
                              </div>
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}