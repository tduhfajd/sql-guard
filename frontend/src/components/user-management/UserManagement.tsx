/**
 * User Management component for SQL-Guard frontend
 * Manages users, roles, and permissions
 */
import React, { useState, useCallback } from 'react';
import { Plus, Edit, Trash2, User, Shield, Mail, Calendar, Filter, Search, MoreVertical } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Alert, AlertDescription } from '../ui/alert';
import { useAuth } from '../../hooks/useAuth';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'VIEWER' | 'OPERATOR' | 'APPROVER' | 'ADMIN';
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
  permissions: string[];
  database_access: string[];
  schema_access: Record<string, string[]>;
}

interface UserManagementProps {
  className?: string;
}

export function UserManagement({ className }: UserManagementProps) {
  const { user, hasPermission } = useAuth();
  
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const canManageUsers = hasPermission('manage_users');
  const canCreateUsers = hasPermission('create_users');
  const canUpdateUsers = hasPermission('update_users');
  const canDeleteUsers = hasPermission('delete_users');

  // Mock data - in real implementation, this would come from API
  const mockUsers: User[] = [
    {
      id: '1',
      email: 'admin@company.com',
      full_name: 'System Administrator',
      role: 'ADMIN',
      is_active: true,
      last_login: '2024-01-15T14:30:00Z',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-15T14:30:00Z',
      permissions: ['*'],
      database_access: ['*'],
      schema_access: {},
    },
    {
      id: '2',
      email: 'john.doe@company.com',
      full_name: 'John Doe',
      role: 'OPERATOR',
      is_active: true,
      last_login: '2024-01-15T13:45:00Z',
      created_at: '2024-01-10T09:00:00Z',
      updated_at: '2024-01-15T13:45:00Z',
      permissions: ['execute_select_queries', 'manage_templates', 'execute_approved_templates'],
      database_access: ['db1', 'db2'],
      schema_access: { 'db1': ['public', 'analytics'], 'db2': ['public'] },
    },
    {
      id: '3',
      email: 'jane.smith@company.com',
      full_name: 'Jane Smith',
      role: 'APPROVER',
      is_active: true,
      last_login: '2024-01-15T12:20:00Z',
      created_at: '2024-01-12T14:30:00Z',
      updated_at: '2024-01-15T12:20:00Z',
      permissions: ['approve_templates', 'view_approval_requests', 'view_audit_logs'],
      database_access: ['db1'],
      schema_access: { 'db1': ['public'] },
    },
    {
      id: '4',
      email: 'mike.wilson@company.com',
      full_name: 'Mike Wilson',
      role: 'VIEWER',
      is_active: true,
      last_login: '2024-01-15T11:15:00Z',
      created_at: '2024-01-14T16:00:00Z',
      updated_at: '2024-01-15T11:15:00Z',
      permissions: ['execute_select_queries'],
      database_access: ['db1'],
      schema_access: { 'db1': ['public'] },
    },
    {
      id: '5',
      email: 'sarah.jones@company.com',
      full_name: 'Sarah Jones',
      role: 'VIEWER',
      is_active: false,
      last_login: '2024-01-10T15:30:00Z',
      created_at: '2024-01-08T10:00:00Z',
      updated_at: '2024-01-10T15:30:00Z',
      permissions: ['execute_select_queries'],
      database_access: ['db1'],
      schema_access: { 'db1': ['public'] },
    },
  ];

  // Filter users based on search and filters
  const filteredUsers = mockUsers.filter(user => {
    const matchesSearch = user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         user.full_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && user.is_active) ||
                         (statusFilter === 'inactive' && !user.is_active);
    return matchesSearch && matchesRole && matchesStatus;
  });

  const handleCreateUser = useCallback(async (userData: Partial<User>) => {
    setIsCreating(true);
    try {
      // TODO: Implement actual user creation API call
      console.log('Creating user:', userData);
    } catch (error) {
      console.error('User creation failed:', error);
    } finally {
      setIsCreating(false);
    }
  }, []);

  const handleUpdateUser = useCallback(async (userId: string, userData: Partial<User>) => {
    setIsEditing(true);
    try {
      // TODO: Implement actual user update API call
      console.log('Updating user:', userId, userData);
    } catch (error) {
      console.error('User update failed:', error);
    } finally {
      setIsEditing(false);
    }
  }, []);

  const handleDeleteUser = useCallback(async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      // TODO: Implement actual user deletion API call
      console.log('Deleting user:', userId);
    } catch (error) {
      console.error('User deletion failed:', error);
    }
  }, []);

  const handleToggleUserStatus = useCallback(async (userId: string, isActive: boolean) => {
    try {
      // TODO: Implement actual user status toggle API call
      console.log('Toggling user status:', userId, isActive);
    } catch (error) {
      console.error('User status toggle failed:', error);
    }
  }, []);

  const getRoleBadge = (role: string) => {
    const roleConfig = {
      ADMIN: { variant: 'destructive' as const, color: 'text-red-600' },
      APPROVER: { variant: 'default' as const, color: 'text-blue-600' },
      OPERATOR: { variant: 'secondary' as const, color: 'text-green-600' },
      VIEWER: { variant: 'outline' as const, color: 'text-gray-600' },
    };

    const config = roleConfig[role as keyof typeof roleConfig] || roleConfig.VIEWER;

    return (
      <Badge variant={config.variant} className={config.color}>
        {role}
      </Badge>
    );
  };

  const getStatusBadge = (isActive: boolean) => {
    return (
      <Badge variant={isActive ? 'default' : 'secondary'}>
        {isActive ? 'Active' : 'Inactive'}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!canManageUsers) {
    return (
      <div className={`space-y-4 ${className}`}>
        <Alert>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            You don't have permission to manage users.
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
          <h2 className="text-2xl font-bold">User Management</h2>
          <p className="text-muted-foreground">
            Manage users, roles, and permissions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            {filteredUsers.length} users
          </Badge>
          {canCreateUsers && (
            <Dialog>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add User
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create New User</DialogTitle>
                </DialogHeader>
                <UserForm
                  onSubmit={handleCreateUser}
                  isSubmitting={isCreating}
                />
              </DialogContent>
            </Dialog>
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
                  placeholder="Search users..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="ADMIN">Admin</SelectItem>
                <SelectItem value="APPROVER">Approver</SelectItem>
                <SelectItem value="OPERATOR">Operator</SelectItem>
                <SelectItem value="VIEWER">Viewer</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      <div className="space-y-4">
        {filteredUsers.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <User className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-medium mb-2">No users found</h3>
                <p className="text-muted-foreground">
                  {searchTerm || roleFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your search or filter criteria'
                    : 'No users have been created yet'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredUsers.map((user) => (
            <Card key={user.id} className="hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-muted rounded-full flex items-center justify-center">
                        <User className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{user.full_name}</h3>
                        <p className="text-sm text-muted-foreground">{user.email}</p>
                      </div>
                      {getRoleBadge(user.role)}
                      {getStatusBadge(user.is_active)}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        <span>Created: {formatDate(user.created_at)}</span>
                      </div>
                      {user.last_login && (
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4" />
                          <span>Last login: {formatDate(user.last_login)}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        <span>{user.permissions.length} permissions</span>
                      </div>
                    </div>

                    {/* Permissions Preview */}
                    <div className="flex flex-wrap gap-1">
                      {user.permissions.slice(0, 5).map((permission) => (
                        <Badge key={permission} variant="outline" className="text-xs">
                          {permission.replace(/_/g, ' ')}
                        </Badge>
                      ))}
                      {user.permissions.length > 5 && (
                        <Badge variant="outline" className="text-xs">
                          +{user.permissions.length - 5} more
                        </Badge>
                      )}
                    </div>

                    {/* Database Access */}
                    <div className="flex flex-wrap gap-1">
                      {user.database_access.map((db) => (
                        <Badge key={db} variant="secondary" className="text-xs">
                          {db}
                        </Badge>
                      ))}
                    </div>
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
                          <DialogTitle>Edit User: {user.full_name}</DialogTitle>
                        </DialogHeader>
                        <UserForm
                          user={user}
                          onSubmit={(data) => handleUpdateUser(user.id, data)}
                          isSubmitting={isEditing}
                        />
                      </DialogContent>
                    </Dialog>

                    {canDeleteUsers && user.id !== user?.id && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteUser(user.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
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

// User Form Component
interface UserFormProps {
  user?: User;
  onSubmit: (data: Partial<User>) => void;
  isSubmitting: boolean;
}

function UserForm({ user, onSubmit, isSubmitting }: UserFormProps) {
  const [formData, setFormData] = useState({
    email: user?.email || '',
    full_name: user?.full_name || '',
    role: user?.role || 'VIEWER',
    is_active: user?.is_active ?? true,
    database_access: user?.database_access || [],
    permissions: user?.permissions || [],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handlePermissionChange = (permission: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      permissions: checked
        ? [...prev.permissions, permission]
        : prev.permissions.filter(p => p !== permission)
    }));
  };

  const availablePermissions = [
    'execute_select_queries',
    'manage_templates',
    'execute_approved_templates',
    'approve_templates',
    'view_approval_requests',
    'view_audit_logs',
    'manage_users',
    'create_users',
    'update_users',
    'delete_users',
    'configure_security_policies',
    'view_all_audit_logs',
    'export_audit_logs',
    'view_system_statistics',
    'system_administration',
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6 mt-4">
      <Tabs defaultValue="basic" className="space-y-4">
        <TabsList>
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
          <TabsTrigger value="access">Database Access</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="role">Role</Label>
              <Select value={formData.role} onValueChange={(value) => setFormData(prev => ({ ...prev, role: value as any }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="VIEWER">Viewer</SelectItem>
                  <SelectItem value="OPERATOR">Operator</SelectItem>
                  <SelectItem value="APPROVER">Approver</SelectItem>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="permissions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availablePermissions.map((permission) => (
              <div key={permission} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={permission}
                  checked={formData.permissions.includes(permission)}
                  onChange={(e) => handlePermissionChange(permission, e.target.checked)}
                  className="rounded"
                />
                <Label htmlFor={permission} className="text-sm">
                  {permission.replace(/_/g, ' ')}
                </Label>
              </div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="access" className="space-y-4">
          <div>
            <Label>Database Access</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Configure which databases this user can access
            </p>
            {/* TODO: Implement database access configuration */}
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm text-muted-foreground">
                Database access configuration will be implemented here
              </p>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <div className="flex justify-end gap-2">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : user ? 'Update User' : 'Create User'}
        </Button>
      </div>
    </form>
  );
}