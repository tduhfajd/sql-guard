/**
 * Templates page for SQL-Guard frontend
 * Template management and execution interface
 */
import React from 'react';
import { TemplateCatalog } from '../components/template-catalog/TemplateCatalog';

export function Templates() {
  return (
    <div className="container mx-auto py-6">
      <TemplateCatalog />
    </div>
  );
}