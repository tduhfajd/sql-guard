/**
 * Policies page for SQL-Guard frontend
 * Security policy configuration interface
 */
import React from 'react';
import { PolicyConfig } from '../components/policy-config/PolicyConfig';

export function Policies() {
  return (
    <div className="container mx-auto py-6">
      <PolicyConfig />
    </div>
  );
}