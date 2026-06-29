# cy-commands-ideas.md

Backlog of additional pain points in Cypress test automation at scale, each mapped to a candidate AI-boosted command. Same format as the 3 shipped commands — use `PROMPT_TEMPLATE.md` to scaffold any of these.

---

## 😤 More Pain Points

| Pain point | What it actually costs | Candidate command |
|---|---|---|
| **Selector rot after refactors** | Devs rename classes/IDs during a refactor with zero notice to QA. Dozens of tests fail on the same root cause, and engineers manually re-locate each broken selector one by one. | `cy.aiHeal(intent)` — when a locator fails, re-locates the element from a stored intent description instead of a hardcoded selector, and logs a suggested selector update for review. |
| **Accessibility regressions slip through** | Functional tests pass while contrast, missing labels, or broken focus order silently regress — a11y is usually checked manually, late, or not at all. | `cy.aiA11yReview()` — scans the current DOM, ranks the top accessibility issues by severity, and suggests a concrete fix for each. |
| **Visual regressions without a baseline diff tool** | Teams without a paid visual-testing service either skip visual checks entirely or rely on pixel-diff tools that flag every anti-aliasing change as a failure. | `cy.aiVisualDiff(intent)` — compares a screenshot against the previous baseline and judges whether the change is a meaningful regression or a non-breaking visual drift (font rendering, spacing noise). |
| **Test data drift makes specs unreliable** | Fixtures and seed data go stale as the app's data model evolves — tests fail on data shape mismatches that have nothing to do with the feature being tested. | `cy.aiSeedValidate(schemaIntent)` — checks that current fixture/API response data still matches the expected shape in plain language, flags drift before it causes a misleading failure. |
| **Flaky test backlog never gets prioritized** | Teams know which tests are flaky but rarely have hard data to justify fixing them — flaky tests get re-run and ignored instead of triaged. | `cy.aiFlakyScore()` — aggregates failure history per test (via Cypress Cloud or local run logs) and produces a flakiness score with a likely root-cause category, to rank what to fix first. |
| **PR review misses test coverage gaps** | Reviewers approve PRs without knowing whether new UI logic (conditional rendering, new states) actually has matching test coverage — gaps surface in production instead. | `cy.aiCoverageGapReport(diff)` — given a git diff of changed components, flags UI logic branches that have no corresponding assertion in the current spec file. |
| **Cross-browser/locale bugs found too late** | Behavior or layout issues specific to a locale (RTL, date formats, text expansion) or a secondary browser are rarely covered by smoke suites, and surface only in late manual QA or in production. | `cy.aiLocaleCheck(locale, intent)` — runs an intent-based check against a given locale/viewport combination and flags layout or text-truncation issues an exact-match assertion would miss. |

---

## Notes for prioritization

- **Highest team-value-to-effort ratio:** `cy.aiHeal()` and `cy.aiFlakyScore()` — both attack the single biggest time sink in mature suites (selector maintenance and triage), and both can reuse the existing `aiTriage` plumbing.
- **Best "interview demo" candidate:** `cy.aiA11yReview()` — short feedback loop, visually obvious value, easy to explain to a non-technical interviewer in one sentence.
- **Requires extra infra:** `cy.aiVisualDiff()` needs screenshot storage/baseline management; `cy.aiFlakyScore()` needs either Cypress Cloud access or a local run-history store — scope these after the simpler ones are shipped.
