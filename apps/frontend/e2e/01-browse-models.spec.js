import { test, expect } from '@playwright/test'

/**
 * E2E Test: Browse Models
 *
 * Scenario: User visits homepage and browses available style models
 * - Visit homepage
 * - Navigate to Models page
 * - Verify models are displayed
 * - Filter models by tag
 * - View model detail
 */

test.describe('Browse Models', () => {
  test('should display homepage', async ({ page }) => {
    await page.goto('/')

    // Homepage should load
    await expect(page).toHaveTitle(/Style License/i)

    // Navigation should be visible
    await expect(page.locator('nav')).toBeVisible()
  })

  test('should navigate to models page', async ({ page }) => {
    await page.goto('/')

    // Click on Models link in navigation
    await page.click('text=Models')

    // Should navigate to /models
    await expect(page).toHaveURL(/\/models/)

    // Models page should have heading
    await expect(page.locator('h1')).toContainText(/Models|Styles/i)
  })

  test('should display model list', async ({ page }) => {
    await page.goto('/models')

    // Wait for models to load (wait for loading to finish or items to appear)
    await page.waitForTimeout(1000)

    // Should have at least one model card or empty state message
    const hasModels = await page.locator('[class*="model"]').count() > 0
    const hasEmptyState = await page.locator('text=/No models|No styles/i').isVisible()

    expect(hasModels || hasEmptyState).toBeTruthy()
  })

  test('should filter models by tag', async ({ page }) => {
    await page.goto('/models')

    // Wait for page to load
    await page.waitForTimeout(1000)

    // Check if there are any tag filters available
    const tagButtons = page.locator('button:has-text("watercolor"), button:has-text("portrait"), button:has-text("anime")')
    const tagCount = await tagButtons.count()

    if (tagCount > 0) {
      // Click on first available tag
      await tagButtons.first().click()

      // Wait for filtered results
      await page.waitForTimeout(500)

      // URL should have tag parameter
      expect(page.url()).toContain('tag=')
    } else {
      // Skip if no tags available
      test.skip()
    }
  })

  test('should view model detail', async ({ page }) => {
    await page.goto('/models')

    // Wait for models to load
    await page.waitForTimeout(1000)

    // Find first model card
    const modelCard = page.locator('[class*="model"]').first()
    const hasModels = await modelCard.isVisible()

    if (hasModels) {
      // Click on model card
      await modelCard.click()

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/models\/\d+/)

      // Detail page should show model info
      await expect(page.locator('h1, h2')).toBeVisible()
    } else {
      // Skip if no models available
      test.skip()
    }
  })
})
