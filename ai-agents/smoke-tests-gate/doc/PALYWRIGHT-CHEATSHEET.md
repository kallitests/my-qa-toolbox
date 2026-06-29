# 🎭 Playwright Cheat Sheet — SDET Reference

> Personal reference for the Playwright TypeScript portfolio project. Background: 6 years of Cypress, learning Playwright.

## Table of contents

1. [TypeScript fundamentals](#1-typescript-fundamentals)
2. [Playwright core](#2-playwright-core)
3. [Locators](#3-locators)
4. [Actions & assertions](#4-actions--assertions)
5. [Fixtures & custom commands](#5-fixtures--custom-commands)
6. [API testing](#6-api-testing)
7. [Playwright Python (equivalent)](#7-playwright-python-equivalent)
8. [Gherkin / BDD](#8-gherkin--bdd)
9. [Best practices — Playwright](#9-best-practices--playwright)
10. [Best practices — TypeScript](#10-best-practices--typescript)
11. [Worked example — Amazon.fr smoke tests](#11-worked-example--amazonfr-smoke-tests)
12. [Playwright MCP](#12-playwright-mcp)
13. [Portfolio project ideas](#13-portfolio-project-ideas)

---

## 1. TypeScript fundamentals

### `async` / `await`

```typescript
async function sayHello() {          // "async" = this function contains operations that take time
  await page.goto('/login');         // "await" = "wait for this line to finish before moving on"
  console.log('Page loaded');        // only runs AFTER goto() has finished
}
```
Almost everything in Playwright (`click()`, `fill()`, `goto()`, `expect()`...) returns a **Promise** — always put `await` in front of it.

### `Promise`

```typescript
const promise = page.goto('/login'); // at this point the page isn't loaded yet — a "promise" of a future result
await promise;                       // "unwraps" the promise: wait and get the real result
```
3 states: `pending`, `resolved`, `rejected`. `await` waits for `resolved` (or throws on `rejected`).

### `import` / `export`

```typescript
// loginPage.ts
export class LoginPage { ... }        // make this available to other files

// test.spec.ts
import { LoginPage } from './loginPage'; // use what was exported elsewhere
```

### Closures

```typescript
function createCounter() {
  let count = 0;                     // variable "enclosed" inside the function
  return function () {               // returned function still has access to "count"
    count++;
    return count;
  };
}
```
Playwright fixtures rely on this: a fixture function "remembers" the `page` it was given, even when used later in the test.

### Types

```typescript
let name: string = 'Alice';
let age: number = 30;
let isActive: boolean = true;

interface User {
  email: string;
  password: string;
}
```
Catches type errors **before running the test**, in the editor — not during execution.

### Quick glossary

| Concept | Plain explanation |
|---|---|
| `const` vs `let` | `const` = never reassigned. `let` = can change. Avoid `var`. |
| Arrow function | `(a, b) => a + b` — short syntax for a function |
| Destructuring `{ page }` | extract a property directly from an object/parameter |
| Callback | a function passed to another function, called later |
| Try/catch | run code and "catch" the error if it fails, without crashing everything |

---

## 2. Playwright core

### Setup

```bash
npm init playwright@latest
```
Creates `playwright.config.ts`, `tests/`, `tests-examples/`.

### Common CLI commands

```bash
npx playwright test                   # run all tests
npx playwright test login.spec.ts     # run one file
npx playwright test -g "should login" # run by name (grep)
npx playwright test --headed          # see the browser
npx playwright test --debug           # step-by-step debug
npx playwright show-report            # open HTML report
npx playwright codegen mysite.com     # generate code by clicking
```

### Anatomy of a test

```typescript
import { test, expect } from '@playwright/test';

test.describe('Login page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('https://mysite.com/login');
  });

  test('successful login with valid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('user@test.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page.getByText('Welcome')).toBeVisible();
  });
});
```

### "School" template — optimal test anatomy (AAA pattern)

```typescript
test.describe('Feature: User login', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('https://mysite.com/login'); // common starting point
  });

  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status !== testInfo.expectedStatus) {
      console.log(`Test failed: ${testInfo.title}`);
    }
  });

  test('successful login with valid credentials', async ({ page }) => {
    // --- ARRANGE: prepare data ---
    const email = 'user@test.com';
    const password = 'password123';

    // --- ACT: perform the action ---
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill(password);
    await page.getByRole('button', { name: 'Log in' }).click();

    // --- ASSERT: verify the expected result ---
    await expect(page.getByText('Welcome')).toBeVisible();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  // negative test — just as important as the positive one
  test('login fails with wrong password', async ({ page }) => {
    await page.getByLabel('Email').fill('user@test.com');
    await page.getByLabel('Password').fill('wrong_password');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page.getByText('Invalid credentials')).toBeVisible();
    await expect(page).toHaveURL(/.*login/);
  });
});
```

**AAA pattern (Arrange / Act / Assert)** — the structure to apply to EVERY test, in any language:
1. **Arrange**: set up data/context
2. **Act**: perform the action under test
3. **Assert**: verify the result matches expectations

---

## 3. Locators

Priority order (most to least recommended):

```typescript
// 1. By ARIA role — most recommended, robust and accessible
page.getByRole('button', { name: 'Submit' });
page.getByRole('textbox', { name: 'Email' });

// 2. By label (forms)
page.getByLabel('Password');

// 3. By visible text
page.getByText('Welcome');

// 4. By placeholder
page.getByPlaceholder('Search...');

// 5. By test-id (if you control the source code — most stable)
page.getByTestId('submit-button');

// 6. CSS / XPath — last resort, more fragile
page.locator('.btn-primary');
page.locator('#login-form');
```

**Tip:** ask devs to add `data-testid="..."` on key elements — the most stable method, insensitive to style/text changes.

---

## 4. Actions & assertions

### Common actions

```typescript
await page.getByRole('button').click();
await page.getByLabel('Email').fill('test@test.com');
await page.getByLabel('Country').selectOption('France');
await page.getByLabel('Terms').check();
await page.keyboard.press('Enter');
await page.locator('input[type=file]').setInputFiles('path/file.pdf');
```

### Assertions — auto-retry built in

```typescript
await expect(page.getByText('Error')).toBeVisible();
await expect(page.getByRole('button')).toBeEnabled();
await expect(page).toHaveURL(/.*dashboard/);
await expect(page).toHaveTitle('My Dashboard');
await expect(page.getByLabel('Email')).toHaveValue('test@test.com');
await expect(page.locator('.item')).toHaveCount(5);
```
No need for manual `waitFor` in most cases: `expect` automatically retries for a few seconds.

### Explicit waits (when needed)

```typescript
await page.waitForURL('**/dashboard');
await page.waitForLoadState('networkidle');
await page.waitForResponse(resp => resp.url().includes('/api/users') && resp.status() === 200);
```

---

## 5. Fixtures & custom commands

Playwright has no `Cypress.Commands.add()`, but offers something **more powerful: fixtures**.

```typescript
// fixtures.ts
import { test as base, expect } from '@playwright/test';

type MyFixtures = {
  loginAsUser: () => Promise<void>;
};

export const test = base.extend<MyFixtures>({
  loginAsUser: async ({ page }, use) => {
    const login = async () => {
      await page.goto('/login');
      await page.getByLabel('Email').fill('user@test.com');
      await page.getByLabel('Password').fill('password123');
      await page.getByRole('button', { name: 'Log in' }).click();
    };
    await use(login); // "provides" the function to the test
  },
});

export { expect };
```

```typescript
// login.spec.ts
import { test, expect } from './fixtures';

test('dashboard access after login', async ({ page, loginAsUser }) => {
  await loginAsUser();
  await expect(page.getByText('Dashboard')).toBeVisible();
});
```

### Page Object Model — the other common factoring pattern

```typescript
// pages/LoginPage.ts
import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async login(email: string, password: string) {
    await this.page.getByLabel('Email').fill(email);
    await this.page.getByLabel('Password').fill(password);
    await this.page.getByRole('button', { name: 'Log in' }).click();
  }
}
```

---

## 6. API testing

Playwright can test REST APIs directly, without a browser — much faster than going through the UI.

| Criterion | UI test | API test |
|---|---|---|
| Speed | Slow (rendering, JS, network) | Very fast |
| Reliability | More fragile (selectors, timing) | More stable |
| Coverage | Real user experience | Business/backend logic |
| Typical use | Smoke tests, critical journeys | Data tests, setup/teardown, edge cases |

**Test pyramid strategy:** many API/unit tests, few UI tests (slow and costly to maintain) — reserve UI tests for truly critical journeys.

### GET

```typescript
test('GET /users returns the user list', async ({ request }) => {
  const response = await request.get('https://api.mysite.com/users');
  expect(response.status()).toBe(200);
  expect(response.ok()).toBeTruthy();

  const body = await response.json();
  expect(Array.isArray(body)).toBeTruthy();
  expect(body.length).toBeGreaterThan(0);
});
```

### POST

```typescript
test('POST /users creates a new user', async ({ request }) => {
  const response = await request.post('https://api.mysite.com/users', {
    data: { name: 'Smith', email: 'smith@test.com' },
    headers: { 'Content-Type': 'application/json' },
  });

  expect(response.status()).toBe(201); // 201 = Created
  const body = await response.json();
  expect(body).toHaveProperty('id');
});
```

### PATCH / DELETE

```typescript
test('PATCH /users/:id updates a user', async ({ request }) => {
  const response = await request.patch('https://api.mysite.com/users/42', {
    data: { name: 'Jones' },
  });
  expect(response.status()).toBe(200);
});

test('DELETE /users/:id removes a user', async ({ request }) => {
  const response = await request.delete('https://api.mysite.com/users/42');
  expect(response.status()).toBe(204); // 204 = No Content
});
```

### Bearer token authentication

```typescript
test('access a protected route with a token', async ({ request }) => {
  const loginResponse = await request.post('https://api.mysite.com/login', {
    data: { email: 'user@test.com', password: 'password123' },
  });
  const { token } = await loginResponse.json();

  const response = await request.get('https://api.mysite.com/profile', {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(response.status()).toBe(200);
});
```

### Reusable authenticated API fixture

```typescript
// fixtures.ts
import { test as base, expect, APIRequestContext } from '@playwright/test';

type ApiFixtures = { authenticatedRequest: APIRequestContext };

export const test = base.extend<ApiFixtures>({
  authenticatedRequest: async ({ playwright }, use) => {
    const context = await playwright.request.newContext({ baseURL: 'https://api.mysite.com' });
    const loginResponse = await context.post('/login', {
      data: { email: 'user@test.com', password: 'password123' },
    });
    const { token } = await loginResponse.json();

    const authContext = await playwright.request.newContext({
      baseURL: 'https://api.mysite.com',
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });

    await use(authContext);
    await authContext.dispose();
  },
});

export { expect };
```

### Combining API + UI (very common pattern)

```typescript
test('a product created via API appears correctly in the UI', async ({ page, request }) => {
  // ARRANGE — create data quickly via API
  const response = await request.post('https://api.mysite.com/products', {
    data: { name: 'Mechanical keyboard', price: 49.99 },
  });
  const product = await response.json();

  // ACT — check the UI
  await page.goto(`https://mysite.com/products/${product.id}`);

  // ASSERT
  await expect(page.getByText('Mechanical keyboard')).toBeVisible();
});
```
Key technique: create/clean test data via API (fast, reliable), and only test the UI for what's actually UI-related.

### Mocking a route (testing error states)

```typescript
await page.route('**/api/users', route => route.fulfill({ status: 500 }));
await page.goto('/users');
await expect(page.getByText('Something went wrong')).toBeVisible();
```

---

## 7. Playwright Python (equivalent)

### Setup

```bash
pip install pytest-playwright
playwright install
```

```bash
pytest                        # all tests
pytest -k "test_login"        # by name
pytest --headed                # see the browser
```

### Test anatomy

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture(autouse=True)              # equivalent of beforeEach
def go_to_login_page(page: Page):
    page.goto("https://mysite.com/login")   # no "await" with the sync API

def test_successful_login(page: Page):
    page.get_by_label("Email").fill("user@test.com")
    page.get_by_label("Password").fill("password123")
    page.get_by_role("button", name="Log in").click()

    expect(page.get_by_text("Welcome")).to_be_visible()
```

> Python has two APIs: **sync** (`sync_api`, simpler for beginners) and **async** (`async_api`, with `async`/`await` like TS).

### Fixtures (conftest.py)

```python
import pytest
from playwright.sync_api import Page

@pytest.fixture
def login_as_user(page: Page):
    def _login():
        page.goto("/login")
        page.get_by_label("Email").fill("user@test.com")
        page.get_by_label("Password").fill("password123")
        page.get_by_role("button", name="Log in").click()
    return _login
```

### TypeScript ↔ Python quick mapping

| Concept | TypeScript | Python |
|---|---|---|
| Async | `await page.goto(url)` | `page.goto(url)` (sync_api) |
| Variable | `const x = 5;` | `x = 5` |
| Function | `function f(a: number) {}` | `def f(a: int):` |
| Class self | `this.page` | `self.page` |
| Import | `import { x } from './f'` | `from f import x` |
| Assertion | `expect(x).toBeVisible()` | `expect(x).to_be_visible()` |
| Test runner | built into Playwright | pytest |

---

## 8. Gherkin / BDD

Not native, but integrates well via **playwright-bdd** (most popular) or Cucumber.js.

```bash
npm install -D playwright-bdd
```

```gherkin
# features/login.feature
Feature: Login
  Scenario: Successful login
    Given I am on the login page
    When I enter "user@test.com" and "password123"
    Then I see the dashboard
```

```typescript
// steps/login.steps.ts
import { Given, When, Then } from 'playwright-bdd';

Given('I am on the login page', async ({ page }) => {
  await page.goto('/login');
});

When('I enter {string} and {string}', async ({ page }, email: string, password: string) => {
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Log in' }).click();
});

Then('I see the dashboard', async ({ page }) => {
  await expect(page.getByText('Dashboard')).toBeVisible();
});
```

⚠️ **Pragmatic take:** Gherkin adds complexity (feature ↔ steps sync, double maintenance). Use it only if non-technical stakeholders genuinely need to read scenarios. Otherwise, plain TypeScript with clear test names is usually simpler to maintain.

---

## 9. Best practices — Playwright

### Locators
✅ `getByRole`, `getByLabel`, `getByTestId` — reflect what the user sees.
❌ `div > div:nth-child(3) > button`, generated CSS classes — fragile.

### Waits
✅ `expect(...).toBeVisible()`, `waitForResponse()` — built-in auto-retry.
❌ `page.waitForTimeout(3000)` — fixed wait, slow AND unreliable.

### Test isolation
✅ Each test runs alone, in any order. Create/clean data via API in `beforeEach`/`afterEach`.
❌ Test B depending on data created by test A — Playwright runs tests in parallel by default, so this is a major flakiness source.

### Project structure
✅ Page Object Model or fixtures to factor repeated code. Clear folders: `tests/`, `pages/`, `utils/`. Descriptive test names.
❌ Copy-pasting the same login code in 30 files. Vague names like `test('test1', ...)`.

### Assertions
✅ `expect(locator).toHaveText(...)` — precise, auto-retried.
❌ Manually extracting text and comparing it with `if` — reinvents the wheel, no auto-retry.

### CI configuration

```typescript
export default defineConfig({
  retries: process.env.CI ? 2 : 0,   // retries only in CI, not locally
  trace: 'on-first-retry',            // trace only when something fails once
  screenshot: 'only-on-failure',
  video: 'retain-on-failure',
});
```
❌ `retries: 5` everywhere to hide flaky tests instead of fixing them.

### "Parasite" elements (cookies, popups)

```typescript
test.beforeEach(async ({ page }) => {
  await page.goto('/');
  const cookieBanner = page.getByRole('button', { name: /accept/i });
  if (await cookieBanner.isVisible({ timeout: 3000 }).catch(() => false)) {
    await cookieBanner.click();
  }
});
```

### Negative tests & edge cases
Also test: empty/invalid fields, denied permissions, network/API errors (mock a 500 with `page.route()`), limits (0, max value, special characters).

### Performance
- Create test data via **API**, not by clicking through the UI.
- Reuse authentication via `storageState` instead of logging in on every test:

```typescript
// global-setup.ts
import { chromium } from '@playwright/test';

async function globalSetup() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://mysite.com/login');
  await page.getByLabel('Email').fill('user@test.com');
  await page.getByLabel('Password').fill('password123');
  await page.getByRole('button', { name: 'Log in' }).click();
  await page.context().storageState({ path: 'auth.json' });
  await browser.close();
}
export default globalSetup;
```

```typescript
// playwright.config.ts
export default defineConfig({
  globalSetup: require.resolve('./global-setup'),
  use: { storageState: 'auth.json' }, // every test starts already logged in
});
```

---

## 10. Best practices — TypeScript

| Rule | ✅ Do | ❌ Avoid |
|---|---|---|
| Type exported functions | `function f(a: number): number` | `function f(a, b)` — no type checking possible |
| Variable declaration | `const` by default, `let` if reassigned | `var` — scoping bugs |
| Structure test data | `interface User { email: string; role: 'admin' \| 'user' }` | loose untyped objects everywhere |
| Avoid `any` | Use precise types or `unknown` | `any` disables all type checks |
| Async consistency | `async`/`await` everywhere | mixing with `.then()` chains |
| Promises | always `await` or return | floating promises = guaranteed flakiness |
| Test data | centralize in `test-data.ts` | hardcoded values copy-pasted everywhere |
| Naming | `test('login button stays disabled until fields are filled', ...)` | `test('test button', ...)` |

**ESLint tip:** enable `no-floating-promises` to catch missing `await` automatically.

### Quick reflex table

| Situation | Reflex |
|---|---|
| Click/verify an element | `getByRole`/`getByLabel` first, CSS last resort |
| Wait for a state | `expect(...).toBeVisible()`, never `waitForTimeout` |
| A test depends on another | Fix immediately — isolation is mandatory |
| Need test data | Create via API (`request.post`), not the UI |
| Copy-pasting login code | Build a fixture or Page Object |
| Tempted to write `any` | Find the real type, or use `unknown` |
| Forgot an `await` | Check with ESLint `no-floating-promises` |
| Only testing the happy path | Add at least one error/edge case |
| Re-logging in every test | Use `storageState` |

---

## 11. Worked example — Amazon.fr smoke tests

Read-only, no login. Goal: practice SDET methodology on a real, uncontrolled site.

### Test cases

| # | Title | Expected result |
|---|---|---|
| TC01 | Home page loads | Status 200, title contains "Amazon.fr" |
| TC02 | Logo is visible | Logo visible and clickable |
| TC03 | Search bar is visible | Empty field with expected placeholder |
| TC04 | A search returns results | Redirected to results page with products |
| TC05 | Empty search doesn't break the site | No 500 error, no blank page |
| TC06 | Cart icon is visible | Visible and clickable |
| TC07 | Clicking the cart opens the cart page | URL contains "/cart" |
| TC08 | "Sign in" link is visible | Visible in header |
| TC09 | Footer is present | Visible with usual links |
| TC10 | Basic responsiveness | Search bar/menu accessible on mobile viewport |

### Implementation

```typescript
// tests/amazon-smoke.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Smoke tests — Amazon.fr (home page, no login)', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('https://www.amazon.fr/');

    // handle the cookie consent banner — a frequent "parasite" element in practice
    const cookieButton = page.getByRole('button', { name: /accept/i });
    if (await cookieButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await cookieButton.click();
    }
  });

  test('TC01 - home page loads correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/Amazon\.fr/i);
  });

  test('TC02 - Amazon logo is visible', async ({ page }) => {
    await expect(page.locator('#nav-logo-sprites')).toBeVisible();
  });

  test('TC03 - search bar is visible', async ({ page }) => {
    const searchBox = page.locator('#twotabsearchtextbox');
    await expect(searchBox).toBeVisible();
    await expect(searchBox).toBeEmpty();
  });

  test('TC04 - a search returns results', async ({ page }) => {
    await page.locator('#twotabsearchtextbox').fill('book');
    await page.locator('#nav-search-submit-button').click();

    await expect(page).toHaveURL(/k=book/i);
    const results = page.locator('[data-component-type="s-search-result"]');
    await expect(results.first()).toBeVisible();
  });

  test('TC06 - cart icon is visible', async ({ page }) => {
    await expect(page.locator('#nav-cart')).toBeVisible();
  });

  test('TC07 - clicking the cart opens the cart page', async ({ page }) => {
    await page.locator('#nav-cart').click();
    await expect(page).toHaveURL(/cart/i);
  });

  test('TC10 - site stays usable on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 size
    await page.goto('https://www.amazon.fr/');
    await expect(page.locator('#twotabsearchtextbox')).toBeVisible();
  });
});
```

### Lessons learned

1. `#twotabsearchtextbox`, `#nav-cart` are Amazon's real (historically stable) CSS IDs. On an internal company project, you'd use clean `data-testid`s instead — Amazon doesn't have any since it isn't your codebase.
2. `[data-component-type="s-search-result"]` — useful technique when no `data-testid` exists: target an existing `data-*` attribute already in the DOM.
3. On a real third-party site like Amazon: selectors can change without notice, cookie/CAPTCHA banners may appear depending on session, and running this in CI at high frequency against a real external production site raises usage/ToS concerns — fine as a learning exercise, not as a CI staple.

---

## 12. Playwright MCP

### Core concepts

**MCP (Model Context Protocol)** is a standard protocol letting an AI agent (Claude, Copilot, etc.) call external **tools** in a structured way, instead of generating free text. Without MCP, an LLM can only "talk". With MCP, it can "act" — click, navigate, read real page content — through tools made available to it.

| Term | Plain explanation |
|---|---|
| Host | The app hosting the AI agent (Claude Desktop, VS Code, Cursor) |
| MCP Client | The component inside the Host that speaks MCP |
| MCP Server | The external program exposing tools (here, Playwright MCP) |
| Tool | A concrete action, e.g. `browser_navigate`, `browser_click` |
| Snapshot | A structured "photo" of the current state (the page's accessibility tree) |

**Loop:** human writes natural language → Host interprets intent → MCP Client calls a Tool → Playwright MCP Server executes it in the real browser → result (snapshot/status) returns to the LLM → LLM decides the next step based on real state, not a guess.

### Why it's different from a classic Playwright test

| | Classic Playwright test | Playwright MCP |
|---|---|---|
| Who writes the code | You, in advance | The LLM, step by step, live |
| Goal | Verify a repeatable behavior | Explore, act, or generate test code |
| Execution | Scripted, deterministic | Driven by an AI agent, decision after decision |
| Typical use | CI/CD, regression suite | Assisted exploration, test generation, interactive debugging |

**Key point:** Playwright MCP doesn't replace your automated tests — it's a tool to **assist writing, exploring, and debugging**.

### Snapshot-based, not vision-based

Playwright MCP uses the page's **accessibility tree** (same one used by screen readers), not screenshots analyzed by a vision model. Each element gets a reference (`ref=e5`...) the LLM uses to interact — faster, cheaper in tokens, and reflects real semantic structure (ARIA roles).

### Setup

```bash
npx @playwright/mcp@latest
```

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```
Official Microsoft server, Apache-2.0, runs locally, no API key, no rate limit.

### Tool categories
Navigation, interaction (click/fill/select/drag), inspection (snapshot, network, console), network mocking (`page.route`-style URL pattern matching), state persistence (cookies/localStorage save & restore), code generation (record a session → generate a reusable Playwright test file), and an advanced "run arbitrary code" escape hatch (RCE-equivalent — trusted clients only).

### Tokens vs flexibility — the key trade-off

A typical browser automation task costs ~114,000 tokens via MCP (each tool call returns a full page snapshot, which feeds the context every step). Microsoft's `@playwright/cli` (early 2026) does the same task in ~27,000 tokens — about 4x less.

| Need | Recommended tool |
|---|---|
| Interactive exploration, step-by-step debugging | Playwright MCP |
| Bulk code generation, repeated/cost-sensitive use | Playwright CLI |
| CI/CD regression suite | Classic Playwright (TS/Python), not MCP |

### Best practices

- **Don't confuse exploration with a test suite.** Use MCP to explore/debug/generate a first draft; always review generated code before merging it (fragile locators, unnecessary waits).
- **Keep control over dangerous tools.** Only enable the arbitrary-code-execution tool in a trusted local/personal environment.
- **Treat generated code like a junior's PR.** Never commit it without human review; rename auto-generated test names.
- **Keep sessions short** to control token cost — each snapshot adds to context, so cost grows with conversation length.
- **Headed mode for observing, HTTP transport for headless/CI** environments without a display.
- **Never commit saved auth state files** (cookies/session) containing real credentials to a public repo.
- Start with `microsoft/playwright-mcp` (official, best documented) before exploring alternative servers.

---

## 13. Portfolio project ideas

Goal: prove Playwright mastery (coming from 6 years of Cypress) with concrete, recruiter-readable projects.

### Pitch 1 — "PR Smoke Gate" (current project)
A UI + API smoke suite running in **under 5 minutes** on every pull request — what a senior SDET actually builds, not a 2h full E2E suite.
- Targets: Amazon.fr (read-only, real uncontrolled site), Sauce Demo (clean POM/fixtures reference app), Next.js Commerce or equivalent (UI + real API combined)
- Demonstrates: reasoned test selection, parallel execution, CI integration with published HTML report, flakiness handling

### Pitch 2 — "API-first regression suite"
Mostly API tests (fast, stable) + a few critical UI tests, on a real public API (e.g. reqres.io, Restful-booker).
- Demonstrates: full CRUD, Bearer auth, fixtures, negative/edge cases, API-then-UI data setup pattern, tagged reporting (`@smoke`, `@regression`)

### Pitch 3 — "Cypress vs Playwright" migration
Migrate a small existing Cypress suite to Playwright TypeScript, with a documented comparison.
- Demonstrates: this isn't "discovering" Playwright — it's **translating 6 years of Cypress expertise**. Strongest argument against the "0 years Playwright" objection from sales/clients.

**Suggested order:** Pitch 1 (fastest, most aligned with the "fast smoke gate" positioning) → Pitch 3 (directly defuses the Cypress→Playwright objection) → Pitch 2 (technical depth once trust is established).
