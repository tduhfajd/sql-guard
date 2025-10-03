/**
 * Policy Config component for SQL-Guard frontend
 * Manages security policies and their enforcement
 */
import React, { useState, useCallback } from 'react';
import { Plus, Edit, Trash2, Shield, AlertTriangle, CheckCircle, Settings, Filter, Search } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../hooks/useAuth';

interface SecurityPolicy {
  id: string;
  name: string;
  description: string;
  policy_type: 'STATEMENT_TIMEOUT' | 'MAX_ROWS' | 'AUTO_LIMIT' | 'DDL_BLOCK' | 'DML_BLOCK' | 'WHERE_CLAUSE_REQUIRED' | 'PII_MASKING' | 'CUSTOM';
  target: 'GLOBAL' | 'DATABASE' | 'SCHEMA' | 'TABLE' | 'USER' | 'ROLE';
  target_id?: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  is_enabled: boolean;
  conditions: Record<string, any>;
  actions: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface PolicyConfigProps {
  className?: string;
}

export function PolicyConfig({ className }: PolicyConfigProps) {
  const { user, hasPermission } = useAuth();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [targetFilter, setTargetFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [selectedPolicy, setSelectedPolicy] = useState<SecurityPolicy | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const canConfigurePolicies = hasPermission('configure_security_policies');

  // Mock data - in real implementation, this would come from API
  const mockPolicies: SecurityPolicy[] = [
    {
      id: '1',
      name: 'Global Query Timeout',
      description: 'Enforce maximum query execution time for all users',
      policy_type: 'STATEMENT_TIMEOUT',
      target: 'GLOBAL',
      priority: 'HIGH',
      is_enabled: true,
      conditions: { timeout_seconds: 300 },
      actions: { block_query: true, log_violation: true },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      created_by: 'admin@company.com',
    },
    {
      id: '2',
      name: 'Viewer Row Limit',
      description: 'Limit result rows for VIEWER role',
      policy_type: 'MAX_ROWS',
      target: 'ROLE',
      target_id: 'VIEWER',
      priority: 'MEDIUM',
      is_enabled: true,
      conditions: { max_rows: 1000 },
      actions: { auto_limit: true, log_violation: true },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      created_by: 'admin@company.com',
    },
    {
      id: '3',
      name: 'DDL Operations Block',
      description: 'Block DDL operations for non-admin users',
      policy_type: 'DDL_BLOCK',
      target: 'ROLE',
      target_id: 'VIEWER',
      priority: 'CRITICAL',
      is_enabled: true,
      conditions: { blocked_operations: ['CREATE', 'DROP', 'ALTER', 'TRUNCATE'] },
      actions: { block_query: true, log_violation: true, notify_admin: true },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      created_by: 'admin@company.com',
    },
    {
      id: '4',
      name: 'UPDATE/DELETE WHERE Clause',
      description: 'Require WHERE clause for UPDATE and DELETE operations',
      policy_type: 'WHERE_CLAUSE_REQUIRED',
      target: 'GLOBAL',
      priority: 'HIGH',
      is_enabled: true,
      conditions: { required_operations: ['UPDATE', 'DELETE'] },
      actions: { block_query: true, log_violation: true },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      created_by: 'admin@company.com',
    },
    {
      id: '5',
      name: 'PII Data Masking',
      description: 'Mask personally identifiable information in query results',
      policy_type: 'PII_MASKING',
      target: 'GLOBAL',
      priority: 'MEDIUM',
      is_enabled: true,
      conditions: { 
        pii_columns: ['email', 'phone', 'ssn', 'credit_card'],
        masking_type: 'partial'
      },
      actions: { mask_data: true, log_access: true },
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      created_by: 'admin@company.com',
    },
  ];

  // Filter policies based on search and filters
  const filteredPolicies = mockPolicies.filter(policy => {
    const matchesSearch = policy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         policy.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || policy.policy_type === typeFilter;
    const matchesTarget = targetFilter === 'all' || policy.target === targetFilter;
    const matchesPriority = priorityFilter === 'all' || policy.priority === priorityFilter;
    return matchesSearch && matchesType && matchesTarget && matchesPriority;
  });

  const handleCreatePolicy = useCallback(async (policyData: Partial<SecurityPolicy>) => {
    setIsCreating(true);
    try {
      // TODO: Implement actual policy creation API call
      console.log('Creating policy:', policyData);
    } catch (error) {
      console.error('Policy creation failed:', error);
    } finally {
      setIsCreating(false);
    }
  }, []);

  const handleUpdatePolicy = useCallback(async (policyId: string, policyData: Partial<SecurityPolicy>) => {
    setIsEditing(true);
    try {
      // TODO: Implement actual policy update API call
      console.log('Updating policy:', policyId, policyData);
    } catch (error) {
      console.error('Policy update failed:', error);
    } finally {
      setIsEditing(false);
    }
  }, []);

  const handleDeletePolicy = useCallback(async (policyId: string) => {
    if (!confirm('Are you sure you want to delete this policy?')) {
      return;
    }

    try {
      // TODO: Implement actual policy deletion API call
      console.log('Deleting policy:', policyId);
    } catch (error) {
      console.error('Policy deletion failed:', error);
    }
  }, []);

  const handleTogglePolicy = useCallback(async (policyId: string, isEnabled: boolean) => {
    try {
      // TODO: Implement actual policy toggle API call
      console.log('Toggling policy:', policyId, isEnabled);
    } catch (error) {
      console.error('Policy toggle failed:', error);
    }
  }, []);

  const getPriorityBadge = (priority: string) => {
    const priorityConfig = {
      LOW: { variant: 'secondary' as const, color: 'text-gray-600' },
      MEDIUM: { variant: 'outline' as const, color: 'text-blue-600' },
      HIGH: { variant: 'default' as const, color: 'text-orange-600' },
      CRITICAL: { variant: 'destructive' as const, color: 'text-red-600' },
    };

    const config = priorityConfig[priority as keyof typeof priorityConfig] || priorityConfig.LOW;

    return (
      <Badge variant={config.variant} className={config.color}>
        {priority}
      </Badge>
    );
  };

  const getTypeBadge = (type: string) => {
    const typeColors = {
      'STATEMENT_TIMEOUT': 'bg-red-100 text-red-800',
      'MAX_ROWS': 'bg-blue-100 text-blue-800',
      'AUTO_LIMIT': 'bg-green-100 text-green-800',
      'DDL_BLOCK': 'bg-purple-100 text-purple-800',
      'DML_BLOCK': 'bg-orange-100 text-orange-800',
      'WHERE_CLAUSE_REQUIRED': 'bg-yellow-100 text-yellow-800',
      'PII_MASKING': 'bg-pink-100 text-pink-800',
      'CUSTOM': 'bg-gray-100 text-gray-800',
    };

    const colorClass = typeColors[type as keyof typeof typeColors] || 'bg-gray-100 text-gray-800';

    return (
      <Badge className={colorClass}>
        {type.replace(/_/g, ' ')}
      </Badge>
    );
  };

  const getStatusBadge = (isEnabled: boolean) => {
    return (
      <Badge variant={isEnabled ? 'default' : 'secondary'}>
        {isEnabled ? 'Enabled' : 'Disabled'}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!canConfigurePolicies) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to configure security policies.
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
          <h2 className="text-2xl font-bold">Security Policies</h2>
          <p className="text-muted-foreground">
            Configure and manage security policies
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {filteredPolicies.length} policies
          </Badge>
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Policy
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl">
              <DialogHeader>
                <DialogTitle>Create New Security Policy</DialogTitle>
              </DialogHeader>
              <PolicyForm
                onSubmit={handleCreatePolicy}
                isSubmitting={isCreating}
              />
            </DialogContent>
          </Dialog>
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
                  placeholder="Search policies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="STATEMENT_TIMEOUT">Statement Timeout</SelectItem>
                <SelectItem value="MAX_ROWS">Max Rows</SelectItem>
                <SelectItem value="AUTO_LIMIT">Auto Limit</SelectItem>
                <SelectItem value="DDL_BLOCK">DDL Block</SelectItem>
                <SelectItem value="DML_BLOCK">DML Block</SelectItem>
                <SelectItem value="WHERE_CLAUSE_REQUIRED">WHERE Clause Required</SelectItem>
                <SelectItem value="PII_MASKING">PII Masking</SelectItem>
                <SelectItem value="CUSTOM">Custom</SelectItem>
              </SelectContent>
            </Select>
            <Select value={targetFilter} onValueChange={setTargetFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Target" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Targets</SelectItem>
                <SelectItem value="GLOBAL">Global</SelectItem>
                <SelectItem value="DATABASE">Database</SelectItem>
                <SelectItem value="SCHEMA">Schema</SelectItem>
                <SelectItem value="TABLE">Table</SelectItem>
                <SelectItem value="USER">User</SelectItem>
                <SelectItem value="ROLE">Role</SelectItem>
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="CRITICAL">Critical</SelectItem>
                <SelectItem value="HIGH">High</SelectItem>
                <SelectItem value="MEDIUM">Medium</SelectItem>
                <SelectItem value="LOW">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Policies List */}
      <div className="space-y-4">
        {filteredPolicies.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No policies found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || typeFilter !== 'all' || targetFilter !== 'all' || priorityFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria'
                    : 'No security policies have been configured yet'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredPolicies.map((policy) => (
            <Card key={policy.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{policy.name}</h3>
                      {getTypeBadge(policy.policy_type)}
                      {getPriorityBadge(policy.priority)}
                      {getStatusBadge(policy.is_enabled)}
                    </div>

                    <p className="text-sm text-muted-foreground">{policy.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        <span>Target: {policy.target}</span>
                        {policy.target_id && <span>({policy.target_id})</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" />
                        <span>Priority: {policy.priority}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        <span>Status: {policy.is_enabled ? 'Enabled' : 'Disabled'}</span>
                      </div>
                    </div>

                    {/* Conditions Preview */}
                    {Object.keys(policy.conditions).length > 0 && (
                      <div className="bg-muted p-3 rounded-lg">
                        <p className="text-sm font-medium mb-2">Conditions:</p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                          {Object.entries(policy.conditions).map(([key, value]) => (
                            <div key={key}>
                              <span className="font-medium">{key}:</span> {String(value)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions Preview */}
                    {Object.keys(policy.actions).length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
                        <p className="text-sm font-medium mb-2 text-blue-800">Actions:</p>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(policy.actions).map(([key, value]) => (
                            <Badge key={key} variant="outline" className="text-xs text-blue-700">
                              {key}: {String(value)}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl">
                        <DialogHeader>
                          <DialogTitle>Edit Policy: {policy.name}</DialogTitle>
                        </DialogHeader>
                        <PolicyForm
                          policy={policy}
                          onSubmit={(data) => handleUpdatePolicy(policy.id, data)}
                          isSubmitting={isEditing}
                        />
                      </DialogContent>
                    </Dialog>

                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDeletePolicy(policy.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
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

// Policy Form Component
interface PolicyFormProps {
  policy?: SecurityPolicy;
  onSubmit: (data: Partial<SecurityPolicy>) => void;
  isSubmitting: boolean;
}

function PolicyForm({ policy, onSubmit, isSubmitting }: PolicyFormProps) {
  const [formData, setFormData] = useState({
    name: policy?.name || '',
    description: policy?.description || '',
    policy_type: policy?.policy_type || 'STATEMENT_TIMEOUT',
    target: policy?.target || 'GLOBAL',
    target_id: policy?.target_id || '',
    priority: policy?.priority || 'MEDIUM',
    is_enabled: policy?.is_enabled ?? true,
    conditions: policy?.conditions || {},
    actions: policy?.actions || {},
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleConditionChange = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      conditions: {
        ...prev.conditions,
        [key]: value,
      }
    }));
  };

  const handleActionChange = (key: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      actions: {
        ...prev.actions,
        [key]: value,
      }
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 mt-4">
      <Tabs defaultValue="basic" className="space-y-4">
        <TabsList>
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="conditions">Conditions</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Policy Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </div>
            <div>
              <Label htmlFor="policy_type">Policy Type</Label>
              <Select value={formData.policy_type} onValueChange={(value) => setFormData(prev => ({ ...prev, policy_type: value as any }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="STATEMENT_TIMEOUT">Statement Timeout</SelectItem>
                  <SelectItem value="MAX_ROWS">Max Rows</SelectItem>
                  <SelectItem value="AUTO_LIMIT">Auto Limit</SelectItem>
                  <SelectItem value="DDL_BLOCK">DDL Block</SelectItem>
                  <SelectItem value="DML_BLOCK">DML Block</SelectItem>
                  <SelectItem value="WHERE_CLAUSE_REQUIRED">WHERE Clause Required</SelectItem>
                  <SelectItem value="PII_MASKING">PII Masking</SelectItem>
                  <SelectItem value="CUSTOM">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="target">Target</Label>
              <Select value={formData.target} onValueChange={(value) => setFormData(prev => ({ ...prev, target: value as any }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GLOBAL">Global</SelectItem>
                  <SelectItem value="DATABASE">Database</SelectItem>
                  <SelectItem value="SCHEMA">Schema</SelectItem>
                  <SelectItem value="TABLE">Table</SelectItem>
                  <SelectItem value="USER">User</SelectItem>
                  <SelectItem value="ROLE">Role</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="target_id">Target ID</Label>
              <Input
                id="target_id"
                value={formData.target_id}
                onChange={(e) => setFormData(prev => ({ ...prev, target_id: e.target.value }))}
                placeholder="Optional target identifier"
              />
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <Select value={formData.priority} onValueChange={(value) => setFormData(prev => ({ ...prev, priority: value as any }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="LOW">Low</SelectItem>
                  <SelectItem value="MEDIUM">Medium</SelectItem>
                  <SelectItem value="HIGH">High</SelectItem>
                  <SelectItem value="CRITICAL">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="is_enabled"
              checked={formData.is_enabled}
              onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_enabled: checked }))}
            />
            <Label htmlFor="is_enabled">Enabled</Label>
          </div>
        </TabsContent>

        <TabsContent value="conditions" className="space-y-4">
          <div>
            <Label>Policy Conditions</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Define the conditions under which this policy applies
            </p>
            {/* TODO: Implement dynamic condition configuration based on policy type */}
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm text-muted-foreground">
                Condition configuration will be implemented based on policy type
              </p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="actions" className="space-y-4">
          <div>
            <Label>Policy Actions</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Define the actions to take when this policy is triggered
            </p>
            {/* TODO: Implement dynamic action configuration based on policy type */}
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm text-muted-foreground">
                Action configuration will be implemented based on policy type
              </p>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : policy ? 'Update Policy' : 'Create Policy'}
        </Button>
      </div>
    </form>
  );
}