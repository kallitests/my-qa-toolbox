# 🧰 cy-commands-box

> **AI-boosted custom Cypress commands — not gadgets, agents.**
> Resilient assertions, automatic failure triage, and test case generation, built on LangChain.js and shipped with a measured reliability gate, not a demo script.

[![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)](https://github.com/yourname/cy-commands-box)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org)
[![Cypress](https://img.shields.io/badge/Cypress-14-17202C?style=flat-square&logo=cypress)](https://www.cypress.io)
[![LangChain](https://img.shields.io/badge/LangChain.js-agent-blueviolet?style=flat-square)](https://js.langchain.com)
[![LangSmith](https://img.shields.io/badge/LangSmith-traced-1C3C3C?style=flat-square)](https://smith.langchain.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker)](https://docker.com)

---

## 🗺️ Table of Contents

- [The pain points](#-the-pain-points)
- [The solution](#-the-solution)
- [The 3 commands](#-the-3-commands)
- [Why this repo is not another AI gadget](#-why-this-repo-is-not-another-ai-gadget)
- [Architecture](#-architecture)
- [Stack](#-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Watching LangSmith traces](#-watching-langsmith-traces)
- [Adding a new command](#-adding-a-new-command)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 😤 The Pain Points

Every QA/SDET team running Cypress at scale hits the same three walls, sooner or later:

| Pain point | What it actually costs |
|---|---|
| **Brittle assertions** | Tests assert on exact text/CSS. A copywriting tweak or a minor UI redesign breaks dozens of green tests for zero real regression — engineers burn hours chasing false alarms. |
| **Manual failure triage** | Every red build needs a human to open the video, read the logs, and decide: real bug, flaky test, or environment hiccup? That triage time scales linearly with suite size — and doesn't scale with headcount. |
| **Slow test design** | Turning a user story into a clear, structured set of test cases (nominal + edge cases) is repetitive work that delays the start of actual automation — especially when QA, POs, and devs all phrase requirements differently. |

These aren't hypothetical — they're the three line items that quietly eat the most QA engineering time in any mature Cypress suite.

---

## ✅ The Solution

**cy-commands-box** ships three AI-boosted Cypress commands, each one mapped directly to a pain point above — backed by a measured agent, not a black box.

```
Brittle assertions  ──▶ cy.aiAssert()            → intent-based checks, resilient to minor UI drift
Manual triage        ──▶ cy.aiTriage()            → automatic root-cause classification on every failure
Slow test design      ──▶ cy.aiGenerateTestCase() → structured test cases generated from a user story
```

Every command is a thin Cypress wrapper around a LangChain.js agent running server-side, with typed (Zod) output and full LangSmith tracing — so it's auditable, not magic.

---

## 🧩 The 3 Commands

### 1. `cy.aiAssert(intent)` — Semantic assertion agent

```typescript
cy.aiAssert('the cart shows 0 items');
cy.aiAssert('the page displays a search result mentioning products found');
```

**Problem solved:** classic assertions break on exact text/CSS matches. `cy.aiAssert()` checks whether a *functional intent* is satisfied by reading the live DOM — it survives copywriting changes, minor layout shifts, and non-breaking redesigns that would otherwise turn a green suite red for nothing.

**Team value:** fewer false-positive failures, less time spent re-writing selectors after every UI tweak.

### 2. `cy.aiTriage(error)` — Failure diagnosis agent

```typescript
afterEach(function () {
  if (this.currentTest?.state === 'failed') {
    cy.aiTriage(this.currentTest.err?.message);
  }
});
```

**Problem solved:** not all red builds are equal. `cy.aiTriage()` automatically classifies each failure as `real_bug`, `flaky`, or `environment_issue`, with a confidence score and a one-line reasoning — straight from the test report.

**Team value:** the first triage pass happens before a human even opens the failure — engineers go straight to what actually deserves attention.

### 3. `cy.aiGenerateTestCase(userStory)` — Test design agent

```typescript
cy.aiGenerateTestCase(
  'As a logged-in user, I want to add a product to my cart so I can retrieve it at checkout.'
).then((testCases) => {
  cy.task('table', testCases);
});
```

**Problem solved:** turns a free-text user story into a structured list of test cases (nominal case + at least one edge/negative case), ready to be reviewed and turned into specs — instead of starting from a blank file.

**Team value:** faster handoff between requirements and automation, consistent test case structure across the whole team regardless of who wrote the story.

---

## 🛡️ Why This Repo Is Not Another AI Gadget

Most "Cypress + AI" demos call an LLM once and print the result. This repo goes further:

- **Clean architecture** — AI logic runs server-side (`cy.task()`), never in the browser. Strict separation of concerns.
- **Structured output** (Zod) — every agent returns a typed schema, never free text to parse by hand.
- **Observability** — LangSmith tracing turned on by a single env var, zero manual instrumentation.
- **Measured evaluation** (`eval/`) — before trusting an agent in CI, its accuracy is measured against a labeled dataset. See `npm run eval`.
- **Full CI/CD** — GitHub Actions runs the AI evaluation gate *before* E2E tests, with artifact upload.

---

## 🏗️ Architecture

```
Browser (Cypress)                   Node (setupNodeEvents)
┌──────────────────────┐            ┌───────────────────────────┐
│ cy.aiAssert(intent)   │  cy.task   │ runAiAssert()              │
│ cy.aiTriage(error)    │ ─────────▶ │ runAiTriage()              │──▶ LangChain.js ──▶ LLM (Claude / GPT)
│ cy.aiGenerateTestCase │            │ runAiGenerateTestCase()    │           │
└──────────────────────┘            └───────────────────────────┘           ▼
                                                                        LangSmith (trace)
```

---

## 🧰 Stack

| Layer | Technology |
|---|---|
| **Test runner** | [Cypress 14](https://www.cypress.io) |
| **Language** | TypeScript |
| **AI orchestration** | [LangChain.js](https://js.langchain.com) |
| **Structured output** | [Zod](https://zod.dev) |
| **LLM backend** | [Claude (Anthropic)](https://anthropic.com) · OpenAI |
| **Observability** | [LangSmith](https://smith.langchain.com) |
| **Infra** | Docker · GitHub Actions |

---

## 📁 Project Structure

```
cy-commands-box/
├── cypress/
│   ├── e2e/                       # Demo specs for each AI command
│   ├── fixtures/                  # Local demo app (no external site dependency)
│   └── support/
│       ├── commands.ts            # Browser-side Cypress command wrappers
│       └── ai/                    # Node-side LangChain agents
│           ├── langchainClient.ts # Shared LLM client (Claude/OpenAI)
│           ├── aiAssert.ts
│           ├── aiTriage.ts
│           └── aiGenerateTestCase.ts
├── eval/                          # Reliability evaluation layer
│   ├── dataset.json               # Labeled test cases
│   └── eval-runner.ts             # Accuracy gate — run before trusting the agent in CI
├── .github/workflows/ci.yml       # Eval gate + Cypress run + artifact upload
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── PROMPT_TEMPLATE.md             # Reusable prompt to scaffold new AI commands
└── README.md
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/yourname/cy-commands-box.git
cd cy-commands-box

# Environment
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY (or OPENAI_API_KEY) + LANGCHAIN_API_KEY

npm install
npm run cy:open        # interactive mode
# or
npm run cy:run          # headless
npm run eval             # measure cy.aiAssert reliability on eval/dataset.json
```

### With Docker

```bash
docker compose build
docker compose run --rm cypress
```

---

## 👀 Watching LangSmith Traces

With `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` set, every call from the 3 agents is automatically traced in the `LANGCHAIN_PROJECT` LangSmith project — full prompt, latency, token count, and cost. Useful in an interview to show the agent is auditable, not a black box.

---

## ➕ Adding a New Command

See [`PROMPT_TEMPLATE.md`](./PROMPT_TEMPLATE.md) — a short, reusable prompt (your command pitch in → Cypress command + LangChain agent out) that enforces the same architecture: task-based execution, Zod output, eval dataset hook.

---

## 📌 Roadmap

- [x] Repository bootstrap & architecture design
- [x] `cy.aiAssert()` — semantic assertion agent
- [x] `cy.aiTriage()` — failure diagnosis agent
- [x] `cy.aiGenerateTestCase()` — test design agent
- [x] Reliability evaluation layer (`eval/`)
- [x] LangSmith tracing
- [x] Docker + GitHub Actions CI
- [ ] `cy.aiA11yReview()` — accessibility review agent
- [ ] Multi-model comparison in eval runner (Claude vs GPT accuracy/cost)
- [ ] HTML dashboard for eval results history

⭐ Star this repo to follow the progress.

---

## 👤 Author

**Your Name**
SDET — AI-augmented test automation (Cypress, Playwright, LangChain)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-yourname-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/yourname/)
[![GitHub](https://img.shields.io/badge/GitHub-yourname-181717?style=flat-square&logo=github)](https://github.com/yourname)

---

*Built with 🤖 Claude (Anthropic) · 🌲 Cypress · 🦜 LangChain.js*
