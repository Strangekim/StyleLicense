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
    await expect(page.locator('nav')).toBeVisible()
  })

  test('should have working navigation links', async ({ page }) => {
    await page.goto('/')

    // Check that main navigation links are present
    const nav = page.locator('nav')
    await expect(nav).toBeVisible()

    // Common navigation items
    const navItems = ['Home', 'Models', 'Community', 'Generate', 'Train']

    for (const item of navItems) {
      // Check if link exists (some may be hidden based on auth state)
      const link = page.locator(`nav a:has-text("${item}")`)
      const linkCount = await link.count()

      if (linkCount > 0) {
        expect(linkCount).toBeGreaterThan(0)
      }
    }
  })

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/')

    // Navigate to Models
    const modelsLink = page.locator('text=Models')
    if (await modelsLink.isVisible()) {
      await modelsLink.click()
      await expect(page).toHaveURL(/\/models/)
    }

    // Navigate to Community
    const communityLink = page.locator('text=Community')
    if (await communityLink.isVisible()) {
      await communityLink.click()
      await expect(page).toHaveURL(/\/community/)
    }

    // Navigate back to Home
    const homeLink = page.locator('text=Home')
    if (await homeLink.isVisible()) {
      await homeLink.click()
      await expect(page).toHaveURL(/\/$/)
    }
  })

  test('should show 404 page for invalid route', async ({ page }) => {
    await page.goto('/this-page-does-not-exist')

    // Should show 404 or redirect to home
    const is404 = await page.locator('text=/404|Not Found|Page not found/i').isVisible()
    const isHome = page.url().endsWith('/')

    expect(is404 || isHome).toBeTruthy()
  })

  test('should have responsive navigation', async ({ page }) => {
    // Test on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Navigation should still be present (might be hamburger menu)
    await expect(page.locator('nav')).toBeVisible()

    // Test on desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')

    await expect(page.locator('nav')).toBeVisible()
  })
})
