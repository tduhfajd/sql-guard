import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

const Layout = () => {
  const location = useLocation();
  
  const navigation = [
    { name: 'Console', href: '/console', current: location.pathname === '/' || location.pathname === '/console' },
    { name: 'Templates', href: '/templates', current: location.pathname === '/templates' },
    { name: 'Approvals', href: '/approvals', current: location.pathname === '/approvals' },
    { name: 'Audit', href: '/audit', current: location.pathname === '/audit' },
    { name: 'Users', href: '/users', current: location.pathname === '/users' },
    { name: 'Policies', href: '/policies', current: location.pathname === '/policies' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-semibold text-gray-900 hover:text-blue-600">
                SQL-Guard
              </Link>
            </div>
            <div className="flex items-center space-x-8">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    item.current
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {item.name}
                </Link>
              ))}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">Welcome to SQL-Guard</span>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
