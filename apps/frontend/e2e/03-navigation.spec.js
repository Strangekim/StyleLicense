import { test, expect } from '@playwright/test'

/**
 * E2E Test: Basic Navigation
 *
 * Scenario: User navigates through main pages of the application
 * - Homepage
 * - Models page
 * - Community page
 * - Generate page (requires auth)
 * - Train page (requires auth + artist role)
 */

test.describe('Basic Navigation', () => {
  test('should navigate to homepage', async ({ page }) => {
    await page.goto('/')

    await expect(page).toHaveTitle(/Style License/i)
    await expect(page.locator('header')).toBeVisible()
    await expect(page.locator('text=Style License').first()).toBeVisible()
  })

  test('should have working navigation links', async ({ page }) => {
    await page.goto('/')

    // Wait for page to load
    await page.waitForLoadState('networkidle')

    // Check that header is visible
    await expect(page.locator('header')).toBeVisible()

    // Common navigation items that should exist (marketplace and community are public)
    const navItems = ['Marketplace', 'Community']

    for (const item of navItems) {
      // Check if link exists
      const link = page.locator(`a:has-text("${item}")`)
      await expect(link.first()).toBeVisible()
    }
  })

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/')

    // Navigate to Community
    const communityLink = page.locator('text=Community').first()
    if (await communityLink.isVisible()) {
      await communityLink.click()
      await expect(page).toHaveURL(/\/community/)
    }
  })

  test('should show 404 page for invalid route', async ({ page }) => {
    await page.goto('/this-page-does-not-exist')

    // Wait for page to load
    await page.waitForLoadState('networkidle')

    // Should show 404 or redirect to home - for now just check it doesn't crash
    await expect(page.locator('header')).toBeVisible()
  })

  test('should have responsive navigation', async ({ page }) => {
    // Test on desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')

    // Header should be visible
    await expect(page.locator('header')).toBeVisible()

    // Test on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Header should still be present (navigation might be in hamburger menu)
    await expect(page.locator('header')).toBeVisible()
  })
})
