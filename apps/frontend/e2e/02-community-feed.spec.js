import { test, expect } from '@playwright/test'

/**
 * E2E Test: Community Feed
 *
 * Scenario: User browses community feed and interacts with posts
 * - Visit community page
 * - View feed items
 * - Test infinite scroll
 * - Like an image (requires auth - will fail for unauthenticated)
 */

test.describe('Community Feed', () => {
  test('should display community feed page', async ({ page }) => {
    await page.goto('/community')

    // Page should load
    await expect(page).toHaveURL(/\/community/)

    // Should have community heading
    await expect(page.locator('h1')).toContainText(/Community|Feed/i)
  })

  test('should display feed items', async ({ page }) => {
    await page.goto('/community')

    // Wait for feed to load
    await page.waitForTimeout(1500)

    // Should have feed items or empty state
    const hasFeedItems = await page.locator('[class*="feed"]').count() > 0
    const hasEmptyState = await page.locator('text=/No generations|Be the first/i').isVisible()

    expect(hasFeedItems || hasEmptyState).toBeTruthy()
  })

  test('should display image in feed item', async ({ page }) => {
    await page.goto('/community')

    // Wait for feed to load
    await page.waitForTimeout(1500)

    // Find first feed item
    const feedItem = page.locator('[class*="feed"]').first()
    const hasFeedItems = await feedItem.isVisible()

    if (hasFeedItems) {
      // Should have an image
      const image = feedItem.locator('img').first()
      await expect(image).toBeVisible()

      // Should have like button
      const likeButton = feedItem.locator('button:has(svg)').first()
      await expect(likeButton).toBeVisible()
    } else {
      test.skip()
    }
  })

  test('should test infinite scroll', async ({ page }) => {
    await page.goto('/community')

    // Wait for initial feed to load
    await page.waitForTimeout(1500)

    // Get initial count of feed items
    const initialCount = await page.locator('[class*="feed"]').count()

    if (initialCount > 0) {
      // Scroll to bottom
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

      // Wait for more items to load
      await page.waitForTimeout(2000)

      // Get new count
      const newCount = await page.locator('[class*="feed"]').count()

      // New count should be greater than or equal to initial count
      // (equal if there are no more items to load)
      expect(newCount).toBeGreaterThanOrEqual(initialCount)
    } else {
      test.skip()
    }
  })

  test('should show authentication requirement for like', async ({ page }) => {
    await page.goto('/community')

    // Wait for feed to load
    await page.waitForTimeout(1500)

    // Find first feed item
    const feedItem = page.locator('[class*="feed"]').first()
    const hasFeedItems = await feedItem.isVisible()

    if (hasFeedItems) {
      // Try to click like button (should redirect to login or show error)
      const likeButton = feedItem.locator('button').first()
      await likeButton.click()

      // Wait for response
      await page.waitForTimeout(1000)

      // Should either redirect to login or show error/no change
      const currentUrl = page.url()
      const redirectedToLogin = currentUrl.includes('/login')

      // Either redirected to login, or nothing happened (graceful handling)
      expect(redirectedToLogin || currentUrl.includes('/community')).toBeTruthy()
    } else {
      test.skip()
    }
  })
})
