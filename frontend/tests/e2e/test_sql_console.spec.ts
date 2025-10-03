import { test, expect } from '@playwright/test'

test.describe('SQL Console Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com',
            role: 'VIEWER',
            is_active: true,
            created_at: '2025-01-27T00:00:00Z',
            last_login: '2025-01-27T00:00:00Z'
          }
        })
      })
    })

    // Login and navigate to console
    await page.goto('/login')
    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL('/console')
  })

  test('should display SQL console interface', async ({ page }) => {
    // Check that SQL console elements are present
    await expect(page.locator('[data-testid="sql-editor"]')).toBeVisible()
    await expect(page.locator('[data-testid="database-selector"]')).toBeVisible()
    await expect(page.locator('[data-testid="execute-button"]')).toBeVisible()
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
  })

  test('should execute SELECT query successfully', async ({ page }) => {
    // Mock successful query execution
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: [
            { id: 1, name: 'John Doe', email: 'john@example.com' },
            { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
          ],
          columns: ['id', 'name', 'email'],
          row_count: 2,
          execution_time: 0.15,
          warnings: []
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type SQL query
    await page.fill('[data-testid="sql-editor"]', 'SELECT id, name, email FROM users WHERE active = true LIMIT 100')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check results
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
    await expect(page.locator('[data-testid="row-count"]')).toContainText('2 rows')
    await expect(page.locator('[data-testid="execution-time"]')).toContainText('0.15s')
    
    // Check table headers
    await expect(page.locator('th').nth(0)).toContainText('id')
    await expect(page.locator('th').nth(1)).toContainText('name')
    await expect(page.locator('th').nth(2)).toContainText('email')
    
    // Check table data
    await expect(page.locator('tbody tr').nth(0)).toContainText('John Doe')
    await expect(page.locator('tbody tr').nth(1)).toContainText('Jane Smith')
  })

  test('should handle query validation', async ({ page }) => {
    // Mock query validation
    await page.route('**/api/queries/validate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_valid: true,
          errors: [],
          warnings: ['Consider adding an index on the email column'],
          estimated_cost: 0.5,
          security_checks: {
            has_ddl: false,
            has_dml: false,
            has_where_clause: true,
            parameter_count: 0
          }
        })
      })
    })

    // Type SQL query
    await page.fill('[data-testid="sql-editor"]', 'SELECT * FROM users WHERE email = "test@example.com"')

    // Trigger validation (on blur or typing)
    await page.blur('[data-testid="sql-editor"]')

    // Check validation results
    await expect(page.locator('[data-testid="validation-status"]')).toContainText('Valid')
    await expect(page.locator('[data-testid="validation-warnings"]')).toContainText('Consider adding an index')
  })

  test('should handle invalid SQL syntax', async ({ page }) => {
    // Mock validation error
    await page.route('**/api/queries/validate', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          is_valid: false,
          errors: ['Syntax error near "INVALID"'],
          warnings: [],
          estimated_cost: 0,
          security_checks: {
            has_ddl: false,
            has_dml: false,
            has_where_clause: false,
            parameter_count: 0
          }
        })
      })
    })

    // Type invalid SQL
    await page.fill('[data-testid="sql-editor"]', 'INVALID SQL SYNTAX')

    // Trigger validation
    await page.blur('[data-testid="sql-editor"]')

    // Check validation error
    await expect(page.locator('[data-testid="validation-status"]')).toContainText('Invalid')
    await expect(page.locator('[data-testid="validation-errors"]')).toContainText('Syntax error')
    
    // Execute button should be disabled
    await expect(page.locator('[data-testid="execute-button"]')).toBeDisabled()
  })

  test('should block DDL operations for VIEWER', async ({ page }) => {
    // Mock DDL blocking
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Permission denied',
          message: 'DDL operations not allowed for VIEWER role'
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type DDL query
    await page.fill('[data-testid="sql-editor"]', 'CREATE TABLE test_table (id INT, name VARCHAR(100))')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('DDL operations not allowed')
  })

  test('should block DML operations for VIEWER', async ({ page }) => {
    // Mock DML blocking
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Permission denied',
          message: 'DML operations not allowed for VIEWER role'
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type DML query
    await page.fill('[data-testid="sql-editor"]', 'INSERT INTO users (name, email) VALUES ("Test", "test@example.com")')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('DML operations not allowed')
  })

  test('should enforce query timeout', async ({ page }) => {
    // Mock query timeout
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 408,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Query timeout',
          message: 'Query exceeded maximum execution time of 30 seconds'
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type long-running query
    await page.fill('[data-testid="sql-editor"]', 'SELECT * FROM large_table ORDER BY random_column')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check timeout error
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Query exceeded maximum execution time')
  })

  test('should enforce row limit', async ({ page }) => {
    // Mock row limit enforcement
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: Array.from({ length: 1000 }, (_, i) => ({ id: i + 1, name: `User ${i + 1}` })),
          columns: ['id', 'name'],
          row_count: 1000,
          execution_time: 0.5,
          warnings: ['Result set limited to 1000 rows']
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type query without LIMIT
    await page.fill('[data-testid="sql-editor"]', 'SELECT * FROM users')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check results with warning
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
    await expect(page.locator('[data-testid="row-count"]')).toContainText('1000 rows')
    await expect(page.locator('[data-testid="query-warnings"]')).toContainText('Result set limited to 1000 rows')
  })

  test('should mask PII data in results', async ({ page }) => {
    // Mock query with PII data
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: [
            { id: 1, name: 'John Doe', email: '***@***.com', ssn: '***-**-****' },
            { id: 2, name: 'Jane Smith', email: '***@***.com', ssn: '***-**-****' }
          ],
          columns: ['id', 'name', 'email', 'ssn'],
          row_count: 2,
          execution_time: 0.1,
          warnings: []
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type query
    await page.fill('[data-testid="sql-editor"]', 'SELECT id, name, email, ssn FROM users WHERE active = true')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check that PII data is masked
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
    await expect(page.locator('tbody tr').nth(0)).toContainText('***@***.com')
    await expect(page.locator('tbody tr').nth(0)).toContainText('***-**-****')
  })

  test('should display query history', async ({ page }) => {
    // Mock query history
    await page.route('**/api/queries/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          queries: [
            {
              id: 'query-1',
              sql: 'SELECT * FROM users LIMIT 10',
              database: 'production-db',
              executed_at: '2025-01-27T10:00:00Z',
              execution_time: 0.1,
              row_count: 10
            },
            {
              id: 'query-2',
              sql: 'SELECT COUNT(*) FROM orders',
              database: 'production-db',
              executed_at: '2025-01-27T09:30:00Z',
              execution_time: 0.05,
              row_count: 1
            }
          ],
          total: 2
        })
      })
    })

    // Open query history
    await page.click('[data-testid="query-history-button"]')

    // Check history items
    await expect(page.locator('[data-testid="query-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="query-history-item"]').nth(0)).toContainText('SELECT * FROM users')
    await expect(page.locator('[data-testid="query-history-item"]').nth(1)).toContainText('SELECT COUNT(*) FROM orders')
  })

  test('should allow query export', async ({ page }) => {
    // Mock query execution
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: [
            { id: 1, name: 'John Doe', email: 'john@example.com' },
            { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
          ],
          columns: ['id', 'name', 'email'],
          row_count: 2,
          execution_time: 0.15,
          warnings: []
        })
      })
    })

    // Execute query first
    await page.selectOption('[data-testid="database-selector"]', 'production-db')
    await page.fill('[data-testid="sql-editor"]', 'SELECT id, name, email FROM users LIMIT 10')
    await page.click('[data-testid="execute-button"]')

    // Wait for results
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()

    // Mock export
    await page.route('**/api/queries/export', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        body: 'id,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com'
      })
    })

    // Click export button
    await page.click('[data-testid="export-button"]')

    // Select CSV format
    await page.click('[data-testid="export-csv"]')

    // Check that download starts
    const downloadPromise = page.waitForEvent('download')
    await page.click('[data-testid="confirm-export"]')
    const download = await downloadPromise
    
    expect(download.suggestedFilename()).toContain('.csv')
  })

  test('should handle database connection errors', async ({ page }) => {
    // Mock database connection error
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Database connection failed',
          message: 'Unable to connect to database server'
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type query
    await page.fill('[data-testid="sql-editor"]', 'SELECT 1')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Database connection failed')
  })

  test('should show query execution progress', async ({ page }) => {
    // Mock long-running query with progress updates
    await page.route('**/api/queries/execute', async (route) => {
      // Simulate slow response
      await new Promise(resolve => setTimeout(resolve, 1000))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: [{ id: 1, name: 'Test' }],
          columns: ['id', 'name'],
          row_count: 1,
          execution_time: 1.0,
          warnings: []
        })
      })
    })

    // Select database
    await page.selectOption('[data-testid="database-selector"]', 'production-db')

    // Type query
    await page.fill('[data-testid="sql-editor"]', 'SELECT * FROM large_table')

    // Execute query
    await page.click('[data-testid="execute-button"]')

    // Check that progress indicator appears
    await expect(page.locator('[data-testid="query-progress"]')).toBeVisible()
    await expect(page.locator('[data-testid="execute-button"]')).toBeDisabled()

    // Wait for completion
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
    await expect(page.locator('[data-testid="query-progress"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="execute-button"]')).toBeEnabled()
  })
})