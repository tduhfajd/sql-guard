/**
 * Users page for SQL-Guard frontend
 * User management interface
 */
import React from 'react';
import { UserManagement } from '../components/user-management/UserManagement';

export function Users() {
  return (
    <div className="container mx-auto py-6">
      <UserManagement />
    </div>
  );
}