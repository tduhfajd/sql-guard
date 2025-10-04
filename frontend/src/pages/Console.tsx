/**
 * Console page for SQL-Guard frontend
 * Main SQL query execution interface
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function Console() {
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM users LIMIT 10;');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeQuery = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Здесь будет реальный API вызов
      // Пока что симулируем ответ
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Демо данные
      const demoResults = [
        { id: 1, email: 'admin@demo.com', name: 'Admin User', created_at: '2024-01-01' },
        { id: 2, email: 'operator@demo.com', name: 'Operator User', created_at: '2024-01-02' },
        { id: 3, email: 'viewer@demo.com', name: 'Viewer User', created_at: '2024-01-03' }
      ];
      
      setResults(demoResults);
    } catch (err) {
      setError('Ошибка выполнения запроса: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults([]);
    setError(null);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="bg-white shadow rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">SQL Console</h1>
        <p className="text-gray-600 mb-6">Выполните SQL запросы к базе данных</p>
        
        {/* SQL Query Input */}
        <div className="space-y-4">
          <div>
            <label htmlFor="sql-query" className="block text-sm font-medium text-gray-700 mb-2">
              SQL Query
            </label>
            <textarea
              id="sql-query"
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              placeholder="Введите SQL запрос..."
            />
          </div>
          
          <div className="flex space-x-4">
            <Button 
              onClick={executeQuery} 
              disabled={loading || !sqlQuery.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? 'Выполняется...' : 'Выполнить'}
            </Button>
            <Button 
              onClick={clearResults} 
              variant="outline"
              disabled={loading}
            >
              Очистить
            </Button>
          </div>
        </div>
      </div>

      {/* Results */}
      {(results.length > 0 || error) && (
        <Card>
          <CardHeader>
            <CardTitle>Результаты запроса</CardTitle>
          </CardHeader>
          <CardContent>
            {error ? (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800">{error}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {results.length > 0 && Object.keys(results[0]).map((key) => (
                        <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {String(value)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-4 text-sm text-gray-500">
                  Найдено записей: {results.length}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Примеры запросов</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <button
              onClick={() => setSqlQuery('SELECT * FROM users LIMIT 10;')}
              className="block w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
            >
              SELECT * FROM users LIMIT 10;
            </button>
            <button
              onClick={() => setSqlQuery('SELECT * FROM orders WHERE status = \'pending\';')}
              className="block w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
            >
              SELECT * FROM orders WHERE status = 'pending';
            </button>
            <button
              onClick={() => setSqlQuery('SELECT COUNT(*) as total_users FROM users;')}
              className="block w-full text-left px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded"
            >
              SELECT COUNT(*) as total_users FROM users;
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}