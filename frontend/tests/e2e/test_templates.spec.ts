import { test, expect } from '@playwright/test'

test.describe('Template Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication as OPERATOR
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: {
            id: 'operator-123',
            username: 'operator',
            email: 'operator@example.com',
            role: 'OPERATOR',
            is_active: true,
            created_at: '2025-01-27T00:00:00Z',
            last_login: '2025-01-27T00:00:00Z'
          }
        })
      })
    })

    // Login and navigate to templates
    await page.goto('/login')
    await page.fill('input[name="username"]', 'operator')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.goto('/templates')
  })

  test('should display template catalog', async ({ page }) => {
    // Mock template list
    await page.route('**/api/templates', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          templates: [
            {
              id: 'template-1',
              name: 'user_analysis',
              description: 'Analyze user activity',
              sql_content: 'SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
              parameters: {
                start_date: { type: 'date', required: true },
                end_date: { type: 'date', required: true }
              },
              version: 1,
              status: 'APPROVED',
              created_by: 'operator-123',
              approved_by: 'approver-123',
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              approved_at: '2025-01-27T00:00:00Z'
            },
            {
              id: 'template-2',
              name: 'order_summary',
              description: 'Get order summary by date range',
              sql_content: 'SELECT COUNT(*) as order_count, SUM(total) as total_revenue FROM orders WHERE order_date BETWEEN :start_date AND :end_date',
              parameters: {
                start_date: { type: 'date', required: true },
                end_date: { type: 'date', required: true }
              },
              version: 1,
              status: 'PENDING_APPROVAL',
              created_by: 'operator-123',
              approved_by: null,
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              approved_at: null
            }
          ],
          total: 2,
          limit: 50,
          offset: 0
        })
      })
    })

    // Check template catalog elements
    await expect(page.locator('[data-testid="template-catalog"]')).toBeVisible()
    await expect(page.locator('[data-testid="template-card"]')).toHaveCount(2)
    
    // Check first template
    await expect(page.locator('[data-testid="template-card"]').nth(0)).toContainText('user_analysis')
    await expect(page.locator('[data-testid="template-card"]').nth(0)).toContainText('APPROVED')
    
    // Check second template
    await expect(page.locator('[data-testid="template-card"]').nth(1)).toContainText('order_summary')
    await expect(page.locator('[data-testid="template-card"]').nth(1)).toContainText('PENDING_APPROVAL')
  })

  test('should execute approved template', async ({ page }) => {
    // Mock template execution
    await page.route('**/api/templates/template-1/execute', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          query_id: 'query-123',
          results: [
            { id: 1, name: 'John Doe', created_at: '2025-01-15' },
            { id: 2, name: 'Jane Smith', created_at: '2025-01-20' }
          ],
          columns: ['id', 'name', 'created_at'],
          row_count: 2,
          execution_time: 0.2
        })
      })
    })

    // Click on approved template
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Check template details modal
    await expect(page.locator('[data-testid="template-details"]')).toBeVisible()
    await expect(page.locator('[data-testid="template-sql"]')).toContainText('SELECT * FROM users WHERE created_at >= :start_date')

    // Fill parameters
    await page.fill('[data-testid="param-start_date"]', '2025-01-01')
    await page.fill('[data-testid="param-end_date"]', '2025-01-31')

    // Select database
    await page.selectOption('[data-testid="template-database"]', 'production-db')

    // Execute template
    await page.click('[data-testid="execute-template-button"]')

    // Check results
    await expect(page.locator('[data-testid="template-results"]')).toBeVisible()
    await expect(page.locator('[data-testid="template-row-count"]')).toContainText('2 rows')
  })

  test('should block execution of non-approved template', async ({ page }) => {
    // Mock template execution failure
    await page.route('**/api/templates/template-2/execute', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Permission denied',
          message: 'Template not approved for execution'
        })
      })
    })

    // Click on pending template
    await page.click('[data-testid="template-card"]:has-text("order_summary")')

    // Check template details modal
    await expect(page.locator('[data-testid="template-details"]')).toBeVisible()

    // Fill parameters
    await page.fill('[data-testid="param-start_date"]', '2025-01-01')
    await page.fill('[data-testid="param-end_date"]', '2025-01-31')

    // Select database
    await page.selectOption('[data-testid="template-database"]', 'production-db')

    // Execute template
    await page.click('[data-testid="execute-template-button"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Template not approved')
  })

  test('should filter templates by status', async ({ page }) => {
    // Mock filtered template list
    await page.route('**/api/templates?status=APPROVED', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          templates: [
            {
              id: 'template-1',
              name: 'user_analysis',
              description: 'Analyze user activity',
              sql_content: 'SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
              parameters: {
                start_date: { type: 'date', required: true },
                end_date: { type: 'date', required: true }
              },
              version: 1,
              status: 'APPROVED',
              created_by: 'operator-123',
              approved_by: 'approver-123',
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              approved_at: '2025-01-27T00:00:00Z'
            }
          ],
          total: 1,
          limit: 50,
          offset: 0
        })
      })
    })

    // Filter by approved status
    await page.selectOption('[data-testid="status-filter"]', 'APPROVED')

    // Check filtered results
    await expect(page.locator('[data-testid="template-card"]')).toHaveCount(1)
    await expect(page.locator('[data-testid="template-card"]')).toContainText('user_analysis')
    await expect(page.locator('[data-testid="template-card"]')).toContainText('APPROVED')
  })

  test('should search templates by name', async ({ page }) => {
    // Mock search results
    await page.route('**/api/templates?search=user', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          templates: [
            {
              id: 'template-1',
              name: 'user_analysis',
              description: 'Analyze user activity',
              sql_content: 'SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
              parameters: {
                start_date: { type: 'date', required: true },
                end_date: { type: 'date', required: true }
              },
              version: 1,
              status: 'APPROVED',
              created_by: 'operator-123',
              approved_by: 'approver-123',
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              approved_at: '2025-01-27T00:00:00Z'
            }
          ],
          total: 1,
          limit: 50,
          offset: 0
        })
      })
    })

    // Search for templates
    await page.fill('[data-testid="template-search"]', 'user')

    // Check search results
    await expect(page.locator('[data-testid="template-card"]')).toHaveCount(1)
    await expect(page.locator('[data-testid="template-card"]')).toContainText('user_analysis')
  })

  test('should display template version history', async ({ page }) => {
    // Mock template with version history
    await page.route('**/api/templates/template-1/versions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          versions: [
            {
              id: 'template-1',
              version: 2,
              status: 'APPROVED',
              created_at: '2025-01-27T10:00:00Z',
              changes: 'Added email column to results'
            },
            {
              id: 'template-1',
              version: 1,
              status: 'APPROVED',
              created_at: '2025-01-27T00:00:00Z',
              changes: 'Initial version'
            }
          ]
        })
      })
    })

    // Click on template to view details
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Click version history tab
    await page.click('[data-testid="version-history-tab"]')

    // Check version history
    await expect(page.locator('[data-testid="version-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="version-item"]')).toHaveCount(2)
    await expect(page.locator('[data-testid="version-item"]').nth(0)).toContainText('Version 2')
    await expect(page.locator('[data-testid="version-item"]').nth(1)).toContainText('Version 1')
  })

  test('should show template usage statistics', async ({ page }) => {
    // Mock template usage statistics
    await page.route('**/api/templates/template-1/usage', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_executions: 150,
          last_executed: '2025-01-27T09:30:00Z',
          average_execution_time: 0.25,
          success_rate: 98.5,
          most_common_parameters: {
            start_date: '2025-01-01',
            end_date: '2025-01-31'
          }
        })
      })
    })

    // Click on template to view details
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Click usage statistics tab
    await page.click('[data-testid="usage-stats-tab"]')

    // Check usage statistics
    await expect(page.locator('[data-testid="usage-stats"]')).toBeVisible()
    await expect(page.locator('[data-testid="total-executions"]')).toContainText('150')
    await expect(page.locator('[data-testid="success-rate"]')).toContainText('98.5%')
    await expect(page.locator('[data-testid="avg-execution-time"]')).toContainText('0.25s')
  })

  test('should handle template execution errors', async ({ page }) => {
    // Mock template execution error
    await page.route('**/api/templates/template-1/execute', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Database error',
          message: 'Table "users" does not exist'
        })
      })
    })

    // Click on template
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Fill parameters
    await page.fill('[data-testid="param-start_date"]', '2025-01-01')
    await page.fill('[data-testid="param-end_date"]', '2025-01-31')

    // Select database
    await page.selectOption('[data-testid="template-database"]', 'production-db')

    // Execute template
    await page.click('[data-testid="execute-template-button"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Table "users" does not exist')
  })

  test('should validate template parameters', async ({ page }) => {
    // Click on template
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Try to execute without required parameters
    await page.selectOption('[data-testid="template-database"]', 'production-db')
    await page.click('[data-testid="execute-template-button"]')

    // Check validation error
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('Required parameters missing')
  })

  test('should show template execution history', async ({ page }) => {
    // Mock template execution history
    await page.route('**/api/templates/template-1/executions', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          executions: [
            {
              id: 'exec-1',
              executed_at: '2025-01-27T10:00:00Z',
              executed_by: 'operator-123',
              parameters: {
                start_date: '2025-01-01',
                end_date: '2025-01-31'
              },
              execution_time: 0.2,
              row_count: 25,
              status: 'SUCCESS'
            },
            {
              id: 'exec-2',
              executed_at: '2025-01-27T09:00:00Z',
              executed_by: 'operator-123',
              parameters: {
                start_date: '2025-01-01',
                end_date: '2025-01-15'
              },
              execution_time: 0.15,
              row_count: 12,
              status: 'SUCCESS'
            }
          ],
          total: 2
        })
      })
    })

    // Click on template
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Click execution history tab
    await page.click('[data-testid="execution-history-tab"]')

    // Check execution history
    await expect(page.locator('[data-testid="execution-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="execution-item"]')).toHaveCount(2)
    await expect(page.locator('[data-testid="execution-item"]').nth(0)).toContainText('25 rows')
    await expect(page.locator('[data-testid="execution-item"]').nth(1)).toContainText('12 rows')
  })

  test('should export template results', async ({ page }) => {
    // Mock template execution
    await page.route('**/api/templates/template-1/execute', async (route) => {
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
          execution_time: 0.2
        })
      })
    })

    // Click on template
    await page.click('[data-testid="template-card"]:has-text("user_analysis")')

    // Fill parameters and execute
    await page.fill('[data-testid="param-start_date"]', '2025-01-01')
    await page.fill('[data-testid="param-end_date"]', '2025-01-31')
    await page.selectOption('[data-testid="template-database"]', 'production-db')
    await page.click('[data-testid="execute-template-button"]')

    // Wait for results
    await expect(page.locator('[data-testid="template-results"]')).toBeVisible()

    // Mock export
    await page.route('**/api/templates/template-1/export', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        body: 'id,name,email\n1,John Doe,john@example.com\n2,Jane Smith,jane@example.com'
      })
    })

    // Click export button
    await page.click('[data-testid="export-template-results"]')

    // Select CSV format
    await page.click('[data-testid="export-csv"]')

    // Check that download starts
    const downloadPromise = page.waitForEvent('download')
    await page.click('[data-testid="confirm-export"]')
    const download = await downloadPromise
    
    expect(download.suggestedFilename()).toContain('user_analysis')
    expect(download.suggestedFilename()).toContain('.csv')
  })
})