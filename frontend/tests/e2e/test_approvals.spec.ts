import { test, expect } from '@playwright/test'

test.describe('Approval Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication as APPROVER
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: {
            id: 'approver-123',
            username: 'approver',
            email: 'approver@example.com',
            role: 'APPROVER',
            is_active: true,
            created_at: '2025-01-27T00:00:00Z',
            last_login: '2025-01-27T00:00:00Z'
          }
        })
      })
    })

    // Login and navigate to approvals
    await page.goto('/login')
    await page.fill('input[name="username"]', 'approver')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await page.goto('/approvals')
  })

  test('should display approval queue', async ({ page }) => {
    // Mock approval queue
    await page.route('**/api/approvals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          approvals: [
            {
              id: 'approval-1',
              template_id: 'template-1',
              template: {
                id: 'template-1',
                name: 'user_analysis',
                description: 'Analyze user activity',
                sql_content: 'SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
                parameters: {
                  start_date: { type: 'date', required: true },
                  end_date: { type: 'date', required: true }
                },
                version: 1,
                status: 'PENDING_APPROVAL',
                created_by: 'operator-123',
                created_at: '2025-01-27T00:00:00Z'
              },
              requested_by: 'operator-123',
              assigned_to: 'approver-123',
              status: 'PENDING',
              comments: null,
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              resolved_at: null
            },
            {
              id: 'approval-2',
              template_id: 'template-2',
              template: {
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
                created_at: '2025-01-27T00:00:00Z'
              },
              requested_by: 'operator-123',
              assigned_to: 'approver-123',
              status: 'PENDING',
              comments: null,
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              resolved_at: null
            }
          ],
          total: 2,
          limit: 50,
          offset: 0
        })
      })
    })

    // Check approval queue elements
    await expect(page.locator('[data-testid="approval-queue"]')).toBeVisible()
    await expect(page.locator('[data-testid="approval-item"]')).toHaveCount(2)
    
    // Check first approval
    await expect(page.locator('[data-testid="approval-item"]').nth(0)).toContainText('user_analysis')
    await expect(page.locator('[data-testid="approval-item"]').nth(0)).toContainText('PENDING')
    
    // Check second approval
    await expect(page.locator('[data-testid="approval-item"]').nth(1)).toContainText('order_summary')
    await expect(page.locator('[data-testid="approval-item"]').nth(1)).toContainText('PENDING')
  })

  test('should preview template before approval', async ({ page }) => {
    // Mock template preview
    await page.route('**/api/approvals/approval-1/preview', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          rendered_sql: "SELECT * FROM users WHERE created_at >= '2025-01-01' AND created_at <= '2025-01-31'",
          parameter_values: {
            start_date: '2025-01-01',
            end_date: '2025-01-31'
          },
          estimated_cost: 0.5,
          security_analysis: {
            has_ddl: false,
            has_dml: false,
            has_where_clause: true,
            risk_level: 'LOW'
          }
        })
      })
    })

    // Click on first approval
    await page.click('[data-testid="approval-item"]:has-text("user_analysis")')

    // Check approval details modal
    await expect(page.locator('[data-testid="approval-details"]')).toBeVisible()
    await expect(page.locator('[data-testid="template-name"]')).toContainText('user_analysis')
    await expect(page.locator('[data-testid="template-description"]')).toContainText('Analyze user activity')

    // Fill preview parameters
    await page.fill('[data-testid="preview-start_date"]', '2025-01-01')
    await page.fill('[data-testid="preview-end_date"]', '2025-01-31')

    // Click preview button
    await page.click('[data-testid="preview-button"]')

    // Check preview results
    await expect(page.locator('[data-testid="preview-sql"]')).toBeVisible()
    await expect(page.locator('[data-testid="preview-sql"]')).toContainText("SELECT * FROM users WHERE created_at >= '2025-01-01'")
    
    // Check security analysis
    await expect(page.locator('[data-testid="security-analysis"]')).toBeVisible()
    await expect(page.locator('[data-testid="risk-level"]')).toContainText('LOW')
    await expect(page.locator('[data-testid="has-where-clause"]')).toContainText('Yes')
  })

  test('should approve template', async ({ page }) => {
    // Mock approval processing
    await page.route('**/api/approvals/approval-1', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'approval-1',
            status: 'APPROVED',
            comments: 'Approved for production use',
            resolved_at: '2025-01-27T10:00:00Z'
          })
        })
      }
    })

    // Click on first approval
    await page.click('[data-testid="approval-item"]:has-text("user_analysis")')

    // Check approval details modal
    await expect(page.locator('[data-testid="approval-details"]')).toBeVisible()

    // Add approval comments
    await page.fill('[data-testid="approval-comments"]', 'Approved for production use')

    // Click approve button
    await page.click('[data-testid="approve-button"]')

    // Confirm approval
    await page.click('[data-testid="confirm-approval"]')

    // Check success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Template approved successfully')
  })

  test('should reject template', async ({ page }) => {
    // Mock rejection processing
    await page.route('**/api/approvals/approval-2', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'approval-2',
            status: 'REJECTED',
            comments: 'Needs security review - contains sensitive data access',
            resolved_at: '2025-01-27T10:00:00Z'
          })
        })
      }
    })

    // Click on second approval
    await page.click('[data-testid="approval-item"]:has-text("order_summary")')

    // Check approval details modal
    await expect(page.locator('[data-testid="approval-details"]')).toBeVisible()

    // Add rejection comments
    await page.fill('[data-testid="approval-comments"]', 'Needs security review - contains sensitive data access')

    // Click reject button
    await page.click('[data-testid="reject-button"]')

    // Confirm rejection
    await page.click('[data-testid="confirm-rejection"]')

    // Check success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="success-message"]')).toContainText('Template rejected')
  })

  test('should filter approvals by status', async ({ page }) => {
    // Mock filtered approvals
    await page.route('**/api/approvals?status=PENDING', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          approvals: [
            {
              id: 'approval-1',
              template_id: 'template-1',
              template: {
                id: 'template-1',
                name: 'user_analysis',
                description: 'Analyze user activity',
                sql_content: 'SELECT * FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
                parameters: {
                  start_date: { type: 'date', required: true },
                  end_date: { type: 'date', required: true }
                },
                version: 1,
                status: 'PENDING_APPROVAL',
                created_by: 'operator-123',
                created_at: '2025-01-27T00:00:00Z'
              },
              requested_by: 'operator-123',
              assigned_to: 'approver-123',
              status: 'PENDING',
              comments: null,
              created_at: '2025-01-27T00:00:00Z',
              updated_at: '2025-01-27T00:00:00Z',
              resolved_at: null
            }
          ],
          total: 1,
          limit: 50,
          offset: 0
        })
      })
    })

    // Filter by pending status
    await page.selectOption('[data-testid="status-filter"]', 'PENDING')

    // Check filtered results
    await expect(page.locator('[data-testid="approval-item"]')).toHaveCount(1)
    await expect(page.locator('[data-testid="approval-item"]')).toContainText('user_analysis')
    await expect(page.locator('[data-testid="approval-item"]')).toContainText('PENDING')
  })

  test('should show approval history', async ({ page }) => {
    // Mock approval history
    await page.route('**/api/approvals/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          approvals: [
            {
              id: 'approval-3',
              template_id: 'template-3',
              template: {
                name: 'sales_report',
                description: 'Generate sales report'
              },
              requested_by: 'operator-123',
              assigned_to: 'approver-123',
              status: 'APPROVED',
              comments: 'Approved for production',
              created_at: '2025-01-26T00:00:00Z',
              resolved_at: '2025-01-26T10:00:00Z'
            },
            {
              id: 'approval-4',
              template_id: 'template-4',
              template: {
                name: 'user_cleanup',
                description: 'Clean up inactive users'
              },
              requested_by: 'operator-123',
              assigned_to: 'approver-123',
              status: 'REJECTED',
              comments: 'Too risky for production',
              created_at: '2025-01-25T00:00:00Z',
              resolved_at: '2025-01-25T15:00:00Z'
            }
          ],
          total: 2
        })
      })
    })

    // Click history tab
    await page.click('[data-testid="approval-history-tab"]')

    // Check history items
    await expect(page.locator('[data-testid="approval-history"]')).toBeVisible()
    await expect(page.locator('[data-testid="history-item"]')).toHaveCount(2)
    await expect(page.locator('[data-testid="history-item"]').nth(0)).toContainText('sales_report')
    await expect(page.locator('[data-testid="history-item"]').nth(0)).toContainText('APPROVED')
    await expect(page.locator('[data-testid="history-item"]').nth(1)).toContainText('user_cleanup')
    await expect(page.locator('[data-testid="history-item"]').nth(1)).toContainText('REJECTED')
  })

  test('should show approval statistics', async ({ page }) => {
    // Mock approval statistics
    await page.route('**/api/approvals/statistics', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          pending_count: 5,
          approved_count: 25,
          rejected_count: 3,
          average_approval_time: '2.5 hours',
          approval_rate: 89.3
        })
      })
    })

    // Click statistics tab
    await page.click('[data-testid="approval-stats-tab"]')

    // Check statistics
    await expect(page.locator('[data-testid="approval-stats"]')).toBeVisible()
    await expect(page.locator('[data-testid="pending-count"]')).toContainText('5')
    await expect(page.locator('[data-testid="approved-count"]')).toContainText('25')
    await expect(page.locator('[data-testid="rejected-count"]')).toContainText('3')
    await expect(page.locator('[data-testid="approval-rate"]')).toContainText('89.3%')
    await expect(page.locator('[data-testid="avg-approval-time"]')).toContainText('2.5 hours')
  })

  test('should handle approval errors', async ({ page }) => {
    // Mock approval error
    await page.route('**/api/approvals/approval-1', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal server error',
          message: 'Failed to process approval'
        })
      })
    })

    // Click on first approval
    await page.click('[data-testid="approval-item"]:has-text("user_analysis")')

    // Add approval comments
    await page.fill('[data-testid="approval-comments"]', 'Approved')

    // Click approve button
    await page.click('[data-testid="approve-button"]')

    // Confirm approval
    await page.click('[data-testid="confirm-approval"]')

    // Check error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Failed to process approval')
  })

  test('should require comments for rejection', async ({ page }) => {
    // Click on first approval
    await page.click('[data-testid="approval-item"]:has-text("user_analysis")')

    // Try to reject without comments
    await page.click('[data-testid="reject-button"]')

    // Check validation error
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible()
    await expect(page.locator('[data-testid="validation-error"]')).toContainText('Comments required for rejection')
  })

  test('should show template comparison for version changes', async ({ page }) => {
    // Mock template with version changes
    await page.route('**/api/approvals/approval-1/changes', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          previous_version: {
            sql_content: 'SELECT id, name FROM users WHERE created_at >= :start_date',
            parameters: {
              start_date: { type: 'date', required: true }
            }
          },
          current_version: {
            sql_content: 'SELECT id, name, email FROM users WHERE created_at >= :start_date AND created_at <= :end_date',
            parameters: {
              start_date: { type: 'date', required: true },
              end_date: { type: 'date', required: true }
            }
          },
          changes: [
            'Added email column to SELECT clause',
            'Added end_date parameter',
            'Added end_date condition to WHERE clause'
          ]
        })
      })
    })

    // Click on first approval
    await page.click('[data-testid="approval-item"]:has-text("user_analysis")')

    // Click changes tab
    await page.click('[data-testid="template-changes-tab"]')

    // Check changes
    await expect(page.locator('[data-testid="template-changes"]')).toBeVisible()
    await expect(page.locator('[data-testid="change-item"]')).toHaveCount(3)
    await expect(page.locator('[data-testid="change-item"]').nth(0)).toContainText('Added email column')
    await expect(page.locator('[data-testid="change-item"]').nth(1)).toContainText('Added end_date parameter')
    await expect(page.locator('[data-testid="change-item"]').nth(2)).toContainText('Added end_date condition')
  })

  test('should bulk approve templates', async ({ page }) => {
    // Mock bulk approval
    await page.route('**/api/approvals/bulk-approve', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          approved_count: 2,
          failed_count: 0,
          results: [
            { id: 'approval-1', status: 'APPROVED' },
            { id: 'approval-2', status: 'APPROVED' }
          ]
        })
      })
    })

    // Select multiple approvals
    await page.check('[data-testid="approval-checkbox-1"]')
    await page.check('[data-testid="approval-checkbox-2"]')

    // Click bulk approve button
    await page.click('[data-testid="bulk-approve-button"]')

    // Add bulk approval comments
    await page.fill('[data-testid="bulk-approval-comments"]', 'Bulk approved for Q1 reporting')

    // Confirm bulk approval
    await page.click('[data-testid="confirm-bulk-approval"]')

    // Check success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="success-message"]')).toContainText('2 templates approved successfully')
  })
})