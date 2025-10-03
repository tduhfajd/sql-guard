/**
 * Console page for SQL-Guard frontend
 * Main SQL query execution interface
 */
import React from 'react';
import { SQLConsole } from '../components/sql-console/SQLConsole';

export function Console() {
  return (
    <div className="container mx-auto py-6">
      <SQLConsole />
    </div>
  );
}