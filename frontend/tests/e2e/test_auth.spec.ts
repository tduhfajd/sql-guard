import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')
  })

  test('should display login form', async ({ page }) => {
    // Check that login form elements are present
    await expect(page.locator('h1')).toContainText('SQL-Guard Login')
    await expect(page.locator('input[name="username"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('should handle successful login', async ({ page }) => {
    // Mock successful authentication
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

    // Fill login form
    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')

    // Submit form
    await page.click('button[type="submit"]')

    // Should redirect to console page
    await expect(page).toHaveURL('/console')
    
    // Should display user info in header
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
    await expect(page.locator('[data-testid="user-menu"]')).toContainText('testuser')
  })

  test('should handle login failure', async ({ page }) => {
    // Mock failed authentication
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Authentication failed',
          message: 'Invalid credentials'
        })
      })
    })

    // Fill login form with invalid credentials
    await page.fill('input[name="username"]', 'invaliduser')
    await page.fill('input[name="password"]', 'wrongpassword')

    // Submit form
    await page.click('button[type="submit"]')

    // Should display error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials')
    
    // Should stay on login page
    await expect(page).toHaveURL('/login')
  })

  test('should handle OIDC login', async ({ page }) => {
    // Mock OIDC authentication flow
    await page.route('**/auth/oidc/login', async (route) => {
      await route.fulfill({
        status: 302,
        headers: {
          'Location': 'http://localhost:8080/realms/sql-guard/protocol/openid-connect/auth?client_id=sql-guard&redirect_uri=http://localhost:3000/auth/callback&response_type=code&scope=openid'
        }
      })
    })

    // Click OIDC login button
    await page.click('[data-testid="oidc-login-button"]')

    // Should redirect to Keycloak
    await expect(page).toHaveURL(/keycloak/)
  })

  test('should handle logout', async ({ page }) => {
    // First login
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

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for redirect to console
    await expect(page).toHaveURL('/console')

    // Mock logout
    await page.route('**/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({})
      })
    })

    // Click logout button
    await page.click('[data-testid="user-menu"]')
    await page.click('[data-testid="logout-button"]')

    // Should redirect to login page
    await expect(page).toHaveURL('/login')
  })

  test('should handle token refresh', async ({ page }) => {
    // Mock initial login
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

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for redirect to console
    await expect(page).toHaveURL('/console')

    // Mock token refresh
    await page.route('**/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'new_access_token'
        })
      })
    })

    // Simulate token expiration by making an API call
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Token expired'
        })
      })
    })

    // Trigger API call that should refresh token
    await page.click('[data-testid="execute-query-button"]')

    // Should automatically refresh token and retry request
    await expect(page.locator('[data-testid="query-results"]')).toBeVisible()
  })

  test('should handle session timeout', async ({ page }) => {
    // Mock initial login
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

    await page.fill('input[name="username"]', 'testuser')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for redirect to console
    await expect(page).toHaveURL('/console')

    // Mock session timeout
    await page.route('**/auth/refresh', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Session expired'
        })
      })
    })

    // Simulate session timeout by making an API call
    await page.route('**/api/queries/execute', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Session expired'
        })
      })
    })

    // Trigger API call that should detect session timeout
    await page.click('[data-testid="execute-query-button"]')

    // Should redirect to login page with session timeout message
    await expect(page).toHaveURL('/login')
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Session expired')
  })

  test('should display role-based navigation', async ({ page }) => {
    // Mock login as VIEWER
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: {
            id: 'user-123',
            username: 'viewer',
            email: 'viewer@example.com',
            role: 'VIEWER',
            is_active: true,
            created_at: '2025-01-27T00:00:00Z',
            last_login: '2025-01-27T00:00:00Z'
          }
        })
      })
    })

    await page.fill('input[name="username"]', 'viewer')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for redirect to console
    await expect(page).toHaveURL('/console')

    // VIEWER should only see Console and Audit navigation items
    await expect(page.locator('[data-testid="nav-console"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-audit"]')).toBeVisible()
    
    // VIEWER should not see Templates, Approvals, Users, or Policies
    await expect(page.locator('[data-testid="nav-templates"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="nav-approvals"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="nav-users"]')).not.toBeVisible()
    await expect(page.locator('[data-testid="nav-policies"]')).not.toBeVisible()
  })

  test('should display admin navigation', async ({ page }) => {
    // Mock login as ADMIN
    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: {
            id: 'admin-123',
            username: 'admin',
            email: 'admin@example.com',
            role: 'ADMIN',
            is_active: true,
            created_at: '2025-01-27T00:00:00Z',
            last_login: '2025-01-27T00:00:00Z'
          }
        })
      })
    })

    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Wait for redirect to console
    await expect(page).toHaveURL('/console')

    // ADMIN should see all navigation items
    await expect(page.locator('[data-testid="nav-console"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-templates"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-approvals"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-audit"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-users"]')).toBeVisible()
    await expect(page.locator('[data-testid="nav-policies"]')).toBeVisible()
  })
})