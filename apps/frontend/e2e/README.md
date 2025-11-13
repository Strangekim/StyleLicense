# E2E Tests

This directory contains End-to-End (E2E) tests using Playwright.

## Test Structure

Tests are organized by feature:

- `01-browse-models.spec.js` - Browse and view style models
- `02-community-feed.spec.js` - Community feed interactions
- `03-navigation.spec.js` - Basic navigation and routing

## Running Tests

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run with browser visible (headed mode)
npm run test:e2e:headed

# Run specific test file
npx playwright test 01-browse-models.spec.js
```

## Prerequisites

Before running E2E tests:

1. **Backend server must be running** on `http://localhost:8000`
2. **Frontend dev server** will start automatically (configured in playwright.config.js)
3. **Database** should have some test data (optional, tests handle empty states)

## Test Data Setup

For complete E2E test coverage, you may want to create test data:

1. At least one completed Style model
2. At least one public Generation image
3. Test user accounts (authenticated tests)

## Writing New Tests

Follow these conventions:

1. Use descriptive test names
2. Handle empty states gracefully (skip tests if data not available)
3. Use `page.waitForTimeout()` sparingly (prefer `waitForSelector`)
4. Clean up test data in `afterEach` hooks if creating data
5. Document test scenarios at the top of each file

## Authentication Tests

Tests requiring authentication are currently skipped or check for login redirect.

To add authenticated tests:

1. Use Playwright's `storageState` to save auth cookies
2. Create `auth.setup.js` for login flow
3. Reuse auth state in tests with `use: { storageState: 'auth.json' }`

Example:

```javascript
// auth.setup.js
test('authenticate', async ({ page }) => {
  await page.goto('/login')
  // Perform login with Google OAuth mock or test credentials
  await page.context().storageState({ path: 'auth.json' })
})

// Use in tests
test.use({ storageState: 'auth.json' })
```

## CI/CD Integration

Tests are configured to run in CI with:

- 2 retries for flaky tests
- 1 worker (non-parallel) for consistency
- HTML reporter for test results

See `.github/workflows/` for CI configuration.

## Troubleshooting

**Tests timing out:**
- Increase `timeout` in playwright.config.js
- Check if backend/frontend servers are running

**Tests failing on "no elements found":**
- Tests gracefully skip if data not available
- Add test data to database for full coverage

**Port conflicts:**
- Frontend dev server uses port 5173 (default Vite)
- Backend should run on port 8000
- Change `baseURL` in playwright.config.js if needed
