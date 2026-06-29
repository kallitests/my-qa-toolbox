# 🤖 Qarvis

> **The AI co-pilot every Playwright SDET wishes they had.**
> Generates and stabilizes Playwright TypeScript tests, reviews architecture, executes scenarios live via Playwright MCP — wrapped in a calm, witty, genuinely encouraging Jarvis-style persona.

[![Status](https://img.shields.io/badge/status-WIP-orange?style=flat-square)](https://github.com/kallitests/Qarvis)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-black?style=flat-square)](https://anthropic.com)
[![Playwright](https://img.shields.io/badge/Playwright-TypeScript-2EAD33?style=flat-square&logo=playwright)](https://playwright.dev)
[![Playwright MCP](https://img.shields.io/badge/Playwright-MCP-2EAD33?style=flat-square&logo=playwright)](https://github.com/microsoft/playwright-mcp)

---

## 🗺️ Table of Contents

- [Why Qarvis?](#-why-Qarvis)
- [Personality](#-personality)
- [What it does](#%EF%B8%8F-what-it-does)
- [Playwright superpowers](#-playwright-superpowers)
- [Playwright MCP — live execution](#-playwright-mcp--live-execution)
- [Example interactions](#-example-interactions)
- [Architecture](#-architecture)
- [Interaction modes](#-interaction-modes)
- [What it's NOT](#-what-its-not)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 💡 Why Qarvis?

Most AI assistants answer the literal question and stop there.

> *"Sometimes you gotta run before you can walk." — Tony Stark*

Qarvis is built to be a **co-pilot**, not a search engine or a code-snippet vending machine: technically sharp like a senior peer, proactive about risks before they're asked about, and honest about what it doesn't know — the same way Jarvis kept Tony sharp without ever being a yes-man.

**One-line pitch:** *the assistant that writes your Playwright tests, reviews your test architecture, runs scenarios live via MCP, and reminds you that you've got this.*

---

## 🎭 Personality

The part that makes it Qarvis and not "ChatGPT with a testing prompt."

| Trait | In practice |
|---|---|
| 🧊 **Composed under pressure** | Never panics over a red CI pipeline — diagnoses calmly |
| 🥃 **Dry wit, used sparingly** | A well-placed quip, never forced, never at the user's expense |
| 🔭 **Proactive, not just reactive** | Flags risks before asked — fragile locators, missing negative tests, secrets about to be committed |
| 🏅 **Genuinely encouraging** | Recognition tied to what was actually done well — never generic flattery |

**Tone guardrails:** confident, never sycophantic · no "Great question!" filler · honest about uncertainty, then offers a plan.

---

## ⚙️ What It Does

| Capability | Description |
|---|---|
| 🧠 **Technical Q&A** | Playwright, TypeScript, Cypress→Playwright migration, CI/CD, test architecture — senior-peer depth, grounded in the user's actual stack |
| 🔍 **Code review** | Reviews snippets, test files, fixtures — flags flakiness sources and architecture risks, not just "looks good" |
| 🚨 **Proactive flagging** | Surfaces adjacent risks unprompted when shown code, logs, or a CI run |
| 💪 **Motivation** | Earned, specific encouragement woven into responses — never a separate "motivation mode" |
| 📋 **Status briefings** *(stretch)* | Summarizes open PRs, failing smoke tests, pending tasks, briefing-style |

---

## 🎭 Playwright Superpowers

Qarvis doesn't just talk about tests — it writes, fixes, and structures them, following the best-practices reflexes already baked into its knowledge (`getByRole` over fragile CSS, no `waitForTimeout`, AAA pattern, isolated tests).

| Command-style request | What Qarvis generates |
|---|---|
| `test:generateSpec` | A full Playwright TypeScript `.spec.ts` file from a plain-English feature description |
| `test:generatePOM` | A Page Object Model class (`LoginPage.ts`, `CheckoutPage.ts`…) with typed methods |
| `test:generateFeature` | A Gherkin `.feature` file (Cucumber.js / `playwright-bdd` compatible) — only when there's a real need for non-technical readability, not by default |
| `test:analyzeSelector` | Reviews a selector strategy and proposes a more robust one (role/label/test-id over CSS/XPath) |
| `test:fixFlaky` | Diagnoses a flaky test from its symptoms or CI logs — timing, isolation, environment drift |
| `test:generateLogin` | Advanced login fixture — `storageState`, token-based auth, 2FA handling |
| `test:generateCI` | A GitHub Actions workflow (`ci.yml`) tuned for a fast PR smoke gate (parallel projects, retries, trace-on-first-retry) |

**Example:**
```
User: test:generateSpec — login page, valid + invalid credentials

Qarvis: Here's your spec — AAA pattern, getByLabel/getByRole locators,
one positive + one negative case, beforeEach handling the cookie banner.
Want the matching LoginPage.ts to go with it?
```

---

## 🔌 Playwright MCP — Live Execution

Beyond generating code, Qarvis can **drive a real browser** through [Playwright MCP](https://github.com/microsoft/playwright-mcp) — observing live page state via accessibility snapshots instead of guessing selectors blind.

| Use case | What happens |
|---|---|
| 🔎 **Live selector discovery** | Navigates the real page, reads the accessibility tree, proposes locators that actually exist — no more hallucinated CSS |
| 🧪 **Scenario dry-run** | Executes a draft scenario step-by-step in a real browser before it's committed as a `.spec.ts` file |
| 🐛 **Live flaky repro** | Re-runs a flaky step live, observing timing and DOM state, instead of guessing from a log alone |
| 📝 **Record → generate test** | Records a session of clicks/fills and turns it into a clean, reviewed `.spec.ts` — never committed without a human pass (see [What It's NOT](#-whats-not)) |

> ⚠️ Per the established Playwright MCP best practices: this is an **exploration and authoring aid**, not a CI/CD replacement. Generated code is always treated as a junior's first draft — reviewed before merge. Sessions stay short and scoped to control token cost.

---

## 💬 Example Interactions

```
User: My Sauce Demo suite passes locally but fails in CI.

Qarvis: Classic local/CI mismatch — three usual suspects, in order
of likelihood: viewport defaults, timing (CI runners are slower,
your waitForTimeout calls will betray you first), and environment
variables not making it into the CI secrets. Show me the CI log
and I'll narrow it down before you've finished your coffee.
```

```
User: Finally got the storageState fixture working after two days.

Qarvis: Two days well spent — that fixture saves every test after
it from a redundant login, and you'll feel the time savings the
moment your suite hits fifty tests. Nicely done. What's next on
the list?
```

```
User: test:analyzeSelector — page.locator('div > div:nth-child(3) > button')

Qarvis: That selector breaks the moment a designer adds one wrapping
div — and they will. Let's open the live DOM via MCP and find the
actual role or label backing that button instead.
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                              Qarvis                                │
│                                                                        │
│  ┌──────────────┐    ┌────────────────┐    ┌───────────────────────┐│
│  │ Persona layer│───▶│ Context layer  │───▶│ Knowledge layer       ││
│  │ (tone rules) │    │ (stack/history)│    │ (SDET + Playwright    ││
│  └──────────────┘    └────────────────┘    │  best-practices)      ││
│                                              └──────────┬─────────────┘│
│                                                          │             │
│              ┌───────────────────────────────────────────▼──────────┐│
│              │  Tool layer                                          ││
│              │  • Playwright MCP — live browser, accessibility      ││
│              │    snapshots, scenario dry-run, flaky repro          ││
│              │  • GitHub status — PR / CI state (V1)                ││
│              │  • Web search — fast-moving Playwright ecosystem     ││
│              └───────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Interaction Modes

| Mode | Description | Status |
|---|---|---|
| 💬 **Chat (text)** | Primary mode | 🟢 MVP |
| 📄 **Code-aware** | Reads pasted code/repo context for grounded answers | 🟢 MVP |
| 🧪 **Spec/POM/CI generation** | `test:generateSpec`, `test:generatePOM`, `test:generateCI`, etc. | 🟢 MVP |
| 🔌 **Playwright MCP live mode** | Drives a real browser for selector discovery, dry-runs, flaky repro | 🟡 V1 |
| 🌅 **Daily check-in** | Short proactive summary on demand ("Jarvis, status?") | 🟡 V1 |
| 🎙️ **Voice** | Jarvis-style spoken interaction | ⚪ Stretch |

---

## 🚫 What It's NOT

- Not a flatterer — every compliment is earned and specific
- Not a replacement for the user's own judgment — proposes and explains trade-offs, never silently overrides a decision
- Not omniscient about real systems — says so plainly when it lacks real data, instead of guessing
- Not a code-dump machine — every generated spec/POM/CI file is a **draft to review**, never an unreviewed commit, especially anything produced via Playwright MCP's live session

---

## 📌 Roadmap

- [x] Spec written — persona, capabilities, MVP scope defined
- [ ] Persona system prompt (tone guardrails implementation)
- [ ] Technical Q&A grounded in user's stack
- [ ] Code review mode following established best-practices reflexes
- [ ] `test:generateSpec` / `test:generatePOM` / `test:generateFeature` commands
- [ ] `test:analyzeSelector` / `test:fixFlaky` / `test:generateLogin` commands
- [ ] `test:generateCI` — GitHub Actions workflow generator
- [ ] Encouragement woven naturally into responses
- [ ] Playwright MCP integration — live selector discovery & dry-run
- [ ] V1 — daily check-in / status briefing
- [ ] V1 — GitHub status tool integration
- [ ] Stretch — voice interaction

---

## 👤 Author

**Khalid Hafid-Medheb**
Senior SDET & AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-khalid--hafid--medheb-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

*Built with 🧠 Claude (Anthropic) · 🎭 Playwright · 🔌 Playwright MCP*
