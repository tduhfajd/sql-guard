/**
 * Audit page for SQL-Guard frontend
 * Audit log viewing and management interface
 */
import React from 'react';
import { AuditLog } from '../components/audit-log/AuditLog';

export function Audit() {
  return (
    <div className="container mx-auto py-6">
      <AuditLog />
    </div>
  );
}