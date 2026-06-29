# 🎭 PR Smoke Gate — Playwright TypeScript

🚧 **Work in progress** — actively building, not production-ready yet.

![Status](https://img.shields.io/badge/status-in%20progress-orange)
![Playwright](https://img.shields.io/badge/Playwright-TypeScript-2EAD33?logo=playwright)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue?logo=githubactions)

---

## Why this project

Most teams don't need a 2-hour end-to-end suite on every pull request — they need a **fast, reliable smoke gate** that catches obvious breakage in under 5 minutes, before merge.

This repo demonstrates exactly that: a focused Playwright TypeScript smoke suite, combining UI and API testing, built the way a senior SDET would design a real PR gate — not a tutorial.

Background: 6 years of Cypress in production environments, now applying that same testing discipline to Playwright.

---

## What's inside

Three targets, three levels of realism:

| Target | What it proves | Type |
|---|---|---|
| **Amazon.fr** (read-only) | Testing a real, complex, uncontrolled site | UI |
| **Sauce Demo** | Clean architecture — Page Object Model, fixtures | UI |
| **Next.js Commerce** (or equivalent open-source demo) | Combining UI + API on a real modern stack | UI + API |

---

## Goal

- Full suite execution: **< 5 minutes**
- Runs automatically on every `pull_request` via GitHub Actions
- HTML report published as a CI artifact

---

## Stack

- Playwright + TypeScript
- GitHub Actions
- Page Object Model + fixtures
- `storageState` for session reuse (no re-login on every test)

---

## Project structure

```
tests/
  amazon/
  saucedemo/
  nextjs-commerce/
pages/          # Page Object Model
fixtures/       # reusable login, auth state
.github/workflows/
  pr-smoke-gate.yml
playwright.config.ts
```

---

## Run locally

```bash
npm install
npx playwright test
```

---

## Status

- [ ] Sauce Demo suite (POM + fixtures)
- [ ] Amazon.fr smoke suite
- [ ] Next.js Commerce suite (UI + API)
- [ ] CI pipeline (< 5 min target)
- [ ] Execution time published in this README

---

## Author

Built by an SDET transitioning from Cypress to Playwright — open to feedback and contributions.
