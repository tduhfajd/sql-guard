/**
 * Approvals page for SQL-Guard frontend
 * Template approval workflow interface
 */
import React from 'react';
import { ApprovalQueue } from '../components/approval-queue/ApprovalQueue';

export function Approvals() {
  return (
    <div className="container mx-auto py-6">
      <ApprovalQueue />
    </div>
  );
}