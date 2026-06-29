# 🧰 my-qa-toolbox

> **A growing collection of AI-powered tools, agents, scripts, and prompts built by and for QA/SDET engineers.**
> From autonomous smoke testing to AI-assisted commit messages — every tool in this repo targets the same goal: eliminate repetitive, low-value QA work and give engineers their time back.

[![Author](https://img.shields.io/badge/Author-Khalid%20Hafid--Medheb-black?style=flat-square)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![Stack](https://img.shields.io/badge/stack-Python%20%7C%20TypeScript%20%7C%20LangChain%20%7C%20Claude-blueviolet?style=flat-square)](#)
[![Playwright](https://img.shields.io/badge/Playwright-MCP-2EAD33?style=flat-square&logo=playwright)](https://playwright.dev)
[![Cypress](https://img.shields.io/badge/Cypress-14-17202C?style=flat-square&logo=cypress)](https://www.cypress.io)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-black?style=flat-square)](https://anthropic.com)
[![Ollama](https://img.shields.io/badge/Ollama-local%20%26%20free-1A1A1A?style=flat-square)](https://ollama.com)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](#)

---

## 🗺️ Table of Contents

- [Why this repo?](#-why-this-repo)
- [What's inside](#-whats-inside)
- [AI Agents](#-ai-agents)
  - [SmokeSentinel — Autonomous smoke test agent](#1-smokesentinel--autonomous-smoke-test-agent)
  - [PR Smoke Gate — Playwright fast CI gate](#2-pr-smoke-gate--playwright-fast-ci-gate)
  - [cy-commands-ai — AI-boosted Cypress commands](#3-cy-commands-ai--ai-boosted-cypress-commands)
  - [Qarvis — AI co-pilot for Playwright SDETs](#4-qarvis--ai-co-pilot-for-playwright-sdets)
  - [User Story → Jira Ticket](#5-user-story--jira-ticket)
- [Git Scripts](#-git-scripts)
  - [git-commit-push-safe](#1-git-commit-push-safe)
  - [git-commit-push-ai](#2-git-commit-push-ai)
  - [create-github-repo](#3-create-github-repo)
  - [qa-toolbox-precommit](#4-qa-toolbox-precommit)
- [Environment Scripts](#-environment-scripts)
  - [dev-setup-kit](#1-dev-setup-kit)
- [Prompts](#-prompts)
  - [CV-ATS-Optimizer](#1-cv-ats-optimizer)
  - [optimus-prompt](#2-optimus-prompt)
- [Repository Structure](#-repository-structure)
- [Author](#-author)

---

## 💡 Why This Repo?

A QA engineer's day is full of tasks that *feel* like work but *add no testing value*: manually triaging CI failures, writing commit messages for the tenth time, reformatting a user story into a Jira ticket, setting up a new repo, or fighting GitHub auth errors before a single line of production code is ever tested.

**This repo systematically attacks those tasks.**

Every tool here was built from a real pain point observed in QA/SDET workflows — in HealthTech, BioTech, or any team running CI-heavy test automation. The design principle is the same across the board:

> *Automate the tedious. Augment the difficult. Leave the judgement to engineers.*

```
Repetitive setup          ──▶ Scripts          → from hours to seconds
Smoke test design         ──▶ AI agents        → from days to minutes
Manual failure triage     ──▶ AI diagnosis     → from hours to one line
Commit message quality    ──▶ AI generation    → from friction to zero friction
```

---

## 📦 What's Inside

| Category | Tool | Status | Primary time saved |
|----------|------|--------|--------------------|
| 🤖 AI Agent | [SmokeSentinel](#1-smokesentinel--autonomous-smoke-test-agent) | WIP | Story → tests → report, zero manual steps |
| 🎭 AI Agent | [PR Smoke Gate](#2-pr-smoke-gate--playwright-fast-ci-gate) | WIP | Full Playwright CI gate under 5 min |
| 🧩 AI Agent | [cy-commands-ai](#3-cy-commands-ai--ai-boosted-cypress-commands) | Active | Assertion writing, failure triage, test design |
| 🤖 AI Agent | [Qarvis](#4-qarvis--ai-co-pilot-for-playwright-sdets) | WIP | Test generation, selector debugging, CI setup |
| 🎫 AI Agent | [User Story → Jira](#5-user-story--jira-ticket) | Active | Jira ticket creation from free-text stories |
| 🔒 Script | [git-commit-push-safe](#1-git-commit-push-safe) | Stable | Guarded Git workflow, zero accidental pushes |
| 🧠 Script | [git-commit-push-ai](#2-git-commit-push-ai) | Stable | AI-written commit messages, Conventional Commits |
| 🚀 Script | [create-github-repo](#3-create-github-repo) | Stable | New GitHub repo published in one command |
| 🛡️ Script | [qa-toolbox-precommit](#4-qa-toolbox-precommit) | Stable | 10 quality gates enforced at every commit |
| 🛠️ Script | [dev-setup-kit](#1-dev-setup-kit) | Stable | Python + PyCharm + 25 plugins installed in one run |
| 🎯 Prompt | [CV-ATS-Optimizer](#1-cv-ats-optimizer) | Stable | ATS-tailored CV + cover letter in minutes |
| 🧠 Prompt | [optimus-prompt](#2-optimus-prompt) | Stable | Battle-tested XML prompt template for Claude |

---

## 🤖 AI Agents

### 1. SmokeSentinel — Autonomous smoke test agent

📁 `ai-agents/smoke-tests-sentinel/`

The most ambitious tool in this repo. SmokeSentinel automates the entire **first line of QA defense** — from reading a Jira user story to running smoke tests and alerting the team — without a single manual step.

```
Jira User Story ──▶ Gherkin Scenarios ──▶ Playwright Tests ──▶ AI Diagnosis ──▶ Report & Alerts
```

**QA value-add:**

| Without SmokeSentinel | With SmokeSentinel |
|-----------------------|--------------------|
| QA writes Gherkin scenarios by hand | LLM generates them from the user story |
| QA manually configures and runs smoke tests | Agent runs Playwright via MCP autonomously |
| Developer reads raw error logs to triage | AI produces a plain-English failure diagnosis |
| Someone writes and sends a Slack alert | Notifier fires automatically on critical regressions |
| Post-deployment smoke testing blocks the team | Runs in CI, unblocking the team in minutes |

**Stack:** Python 3.11+ · LangGraph · LangChain · Claude (Anthropic) · Playwright MCP · Jira API · Slack/Teams · Docker

---

### 2. PR Smoke Gate — Playwright fast CI gate

📁 `ai-agents/smoke-tests-gate/`

A focused Playwright TypeScript smoke suite designed to answer one question before every merge:

> *"Is the application still standing?"*

Three test targets (Amazon.fr, Sauce Demo, Next.js Commerce) covering UI and API, with a hard target of **< 5 minutes** total execution time on GitHub Actions.

**QA value-add:**

| Without a smoke gate | With PR Smoke Gate |
|----------------------|--------------------|
| Full regression suite blocks PRs for hours | Blocking regressions caught in < 5 min |
| Developers wait or bypass checks | Fast feedback loop, no bypass temptation |
| Test setup varies per developer | Shared POM, fixtures, `storageState` for session reuse |

**Stack:** Playwright + TypeScript · Page Object Model · GitHub Actions · `storageState` auth fixture

---

### 3. cy-commands-ai — AI-boosted Cypress commands

📁 `ai-agents/cy-commands-ai/`

Three drop-in Cypress commands that attack the three most expensive recurring costs in any mature Cypress suite.

```
cy.aiAssert(intent)          → semantic assertion — survives UI drift, no selector maintenance
cy.aiTriage(error)           → automatic failure classification — real bug / flaky / environment
cy.aiGenerateTestCase(story) → structured test cases from a user story — nominal + edge cases
```

**QA value-add:**

| Pain point | Manual cost | With cy-commands-ai |
|------------|-------------|---------------------|
| UI copy changes break assertions | Hours re-writing selectors per sprint | `cy.aiAssert` checks intent, not exact text |
| Every red build needs a human to triage | Linear time cost with suite size | `cy.aiTriage` classifies each failure automatically |
| Turning stories into test cases | 30–60 min per story | `cy.aiGenerateTestCase` drafts them in seconds |

Every command runs server-side (`cy.task()`), returns Zod-typed output, and is fully traced in LangSmith — auditable, not a black box. An evaluation layer (`eval/`) measures accuracy before trusting the agent in CI.

**Stack:** Cypress 14 · TypeScript · LangChain.js · Zod · Claude / OpenAI · LangSmith · Docker

---

### 4. Qarvis — AI co-pilot for Playwright SDETs

📁 `ai-agents/qarvis/`

A Jarvis-style AI assistant purpose-built for Playwright engineers. Qarvis does not just answer questions — it generates, reviews, and executes Playwright tests.

| Command | What it produces |
|---------|-----------------|
| `test:generateSpec` | Full `.spec.ts` file from a plain-English feature description |
| `test:generatePOM` | Typed Page Object Model class |
| `test:generateCI` | GitHub Actions workflow for a fast PR smoke gate |
| `test:analyzeSelector` | Robust selector proposal (role/label over CSS/XPath) |
| `test:fixFlaky` | Root-cause diagnosis for flaky tests |

**QA value-add:** A junior SDET can spend an entire day setting up a Playwright suite from scratch. Qarvis generates the scaffold — spec, POM, CI config — in minutes, letting the engineer focus on test logic and edge cases instead of boilerplate. Live selector discovery via Playwright MCP eliminates the trial-and-error loop of writing locators against a running app.

**Stack:** Python 3.11+ · Claude (Anthropic) · Playwright MCP

---

### 5. User Story → Jira Ticket

📁 `ai-agents/user-story-to-jira/`

A React web app that turns any free-text user story into a production-ready, fully structured Jira ticket — in seconds.

**Output includes:** summary · priority · story points · labels · acceptance criteria (Given/When/Then) · test cases (happy path + edge cases) · Definition of Done · technical notes · Jira-compatible JSON.

**QA value-add:** Writing a well-structured Jira ticket from a user story is 15–30 minutes of careful, repetitive work — with a high risk of missing acceptance criteria or test cases if done under time pressure. This tool does it in under 10 seconds and covers every field consistently, regardless of who wrote the story or how it was phrased.

```
Paste story → click Generate → copy JSON → paste into Jira
```

Language-aware: writes the ticket in the same language as the input (FR/EN).

**Stack:** React 18 · Vite · Claude Sonnet (Anthropic API)

---

## 🔧 Git Scripts

These are standalone Python scripts — zero external dependencies beyond the standard library — that wrap the most error-prone Git operations with a structured, interactive safety layer.

### 1. git-commit-push-safe

📁 `git-py-scripts/commit-push/`

A hardened `git add → commit → push` workflow. The plain one-liner has no guardrails: it will commit your `.env` file, push to `main` without warning, and fail with a cryptic error. This script doesn't.

**What it checks before touching anything:**

| Phase | Guard |
|-------|-------|
| Pre-flight | Git installed · valid repo · `origin` configured · branch not detached |
| Branch safety | Explicit confirmation required on `main`, `master`, `production`, `release` |
| File analysis | Colour-coded list of every staged file before anything is added |
| Conflict guard | Blocks if unresolved merge conflicts are detected |
| Secret detection | Flags `.env`, `.pem`, `.key`, SSH private keys — asks before including |
| Commit message | Rejects empty or generic messages (`fix`, `wip`, `update`…) |
| Full summary | Shows remote, branch, message, file list — one final `y/N` before execution |
| Push error diagnosis | Plain-English explanation for: no upstream · rejected push · auth denied · timeout |
| Post-push | Short commit hash + direct GitHub links |

**QA value-add:** eliminates the class of "accidental push" incidents that cost 30–60 min of reverting history, and prevents secret leaks — the single most expensive Git mistake in a team's career.

---

### 2. git-commit-push-ai

📁 `git-py-scripts/commit-push-ai/`

The same safety-checked workflow as above, plus an AI that reads your staged diff and writes the commit message for you.

```
staged diff ──▶ local LLM (Ollama, free) ──▶ Conventional Commits message ──▶ [accept / edit / regenerate]
```

Default provider is **Ollama — 100% local, zero API cost, zero cloud calls.** Claude/Anthropic is available as a one-flag upgrade (`--llm-provider anthropic`).

**QA value-add:** `fix`, `wip`, and `update stuff` commit messages are a permanent record of rushed work. Writing a proper Conventional Commits message takes ~30 seconds per commit — multiplied across a full project, that is hours of friction. The AI removes the excuse: one keystroke to accept, one to regenerate if needed.

---

### 3. create-github-repo

📁 `git-py-scripts/create-repo/`

Publishes a local folder to a new GitHub repository in a single command — repo creation, collaborator invite, and initial push included.

```
Local folder ──▶ Pre-flight checks ──▶ gh repo create ──▶ Collaborator invited ──▶ commit & push
```

**QA value-add:** creating a new repo manually means 7+ sequential steps across browser and terminal. Skip the collaborator invite and the whole team gets a cryptic `Permission denied` on their first push. This script collapses everything into one command and invites the collaborator automatically at creation time.

---

### 4. qa-toolbox-precommit

📁 `git-py-scripts/precommit/`

A plug-and-play pre-commit configuration for Python QA repos. Drop four files into any project, run `make install`, and every `git commit` enforces **10 quality gates automatically** — before code ever reaches CI.

```
git commit
    ├── File hygiene     (trailing whitespace, large files, merge conflict markers)
    ├── Formatting       black (auto-fix)
    ├── Linting          ruff (auto-fix) — replaces flake8 + isort + pyupgrade
    ├── Type checking    mypy --strict
    ├── Dead code        vulture (80% confidence)
    ├── Secret scanning  detect-secrets (blocks new credentials in diffs)
    ├── SAST             bandit (shell injection, hardcoded passwords, weak crypto)
    ├── CVE scan         pip-audit (OSV + PyPI Advisory databases)
    └── Commit message   gitlint (Conventional Commits)
```

**QA value-add:** every one of these checks would otherwise be a manual code review comment or a post-merge CI failure. Running them at commit time means zero style debates in PRs, zero CVE surprises in production, and zero `fix previous fix` commits polluting Git history.

---

## 🛠️ Environment Scripts

### 1. dev-setup-kit

📁 `env-python-py-scripts/setup-python-env/`

An AI-powered installer that sets up a complete Python developer environment — latest stable Python, PyCharm Community, and 25 curated plugins — in a single command. A local Ollama LLM suggests Windows-specific fixes if anything fails.

```
System checks ──▶ Version fetch (python.org + JetBrains APIs) ──▶ Install Python
──▶ Install PyCharm ──▶ Install 25 plugins ──▶ Post-install checks ──▶ AI fix suggestions
```

**QA value-add:** onboarding a new QA engineer or setting up a fresh machine typically takes 2–4 hours of manual downloads, plugin hunts, and environment debugging. This script does it in one run — with AI diagnosis if anything goes wrong, no cloud API key required.

---

## 🎯 Prompts

### 1. CV-ATS-Optimizer

📁 `prompts/cv-ats/`

A master Claude prompt that turns a `.docx` CV + a job offer into a full ATS-optimized application package — without ever inventing a skill, a number, or an experience that isn't already in the CV.

**Deliverables from a single prompt run:**

| Output | Description |
|--------|-------------|
| ATS score estimate | Before and after optimization |
| Keyword gap table | Critical / Important / Secondary — with presence status |
| Optimized one-page CV | ATS-safe format (no tables, no images, no text boxes) |
| Cover letter | Me / You / Us structure, readable in under 60 seconds |
| `.docx` files | Ready to send, correctly named |

**Core principle:** every missing skill is flagged explicitly — never papered over. The prompt is built around the constraint *"maximize my ATS score without lying about who I am."*

**QA value-add (beyond QA):** tailoring a CV and writing a cover letter properly takes 2–4 hours per application. This prompt does it in under 5 minutes, with a structured keyword gap analysis that most candidates skip entirely.

---

### 2. optimus-prompt

📁 `prompts/optimus-prompt/`

A battle-tested **XML prompt template** for Claude, designed to eliminate the four most common prompt failures: hallucinated code, vague output, wasted tokens, and wrong scope.

```xml
<prompt>
  <role>          → Who Claude is for this task
  <context>       → Project facts Claude cannot know on its own
  <objective>     → The ONE deliverable (one sentence, action verb)
  <instructions>  → Ordered steps, REQUIRED / OPTIONAL flagged
  <constraints>   → Hard rules — what Claude must NOT do
  <output_format> → Exact shape, length, and language
  <examples>      → Good AND bad examples (the most powerful anti-hallucination lever)
  <anti_hallucination_rules> → Global safety net
  <task>          → The actual input (swap this to reuse the template)
</prompt>
```

**QA value-add:** a vague prompt produces a vague answer that requires three rounds of back-and-forth correction. This template cuts that iteration loop to one shot — especially valuable when using Claude as a test generation assistant, a code reviewer, or an agent orchestrator where prompt precision directly affects output quality.

---

## 📁 Repository Structure

```
my-qa-toolbox/
│
├── ai-agents/
│   ├── smoke-tests-sentinel/   # SmokeSentinel — autonomous smoke test agent (LangGraph + Playwright MCP)
│   ├── smoke-tests-gate/       # PR Smoke Gate — Playwright TypeScript fast CI suite
│   ├── cy-commands-ai/         # cy-commands-box — AI-boosted Cypress commands (aiAssert, aiTriage, aiGenerateTestCase)
│   ├── qarvis/                 # Qarvis — AI co-pilot for Playwright SDETs
│   ├── user-story-to-jira/     # React app — user story → Jira-ready JSON ticket
│   └── doc/                    # Agent ideas & brainstorming
│
├── git-py-scripts/
│   ├── commit-push/            # git-commit-push-safe — guarded git add → commit → push
│   ├── commit-push-ai/         # git-commit-push-ai — same + AI-generated commit messages (Ollama / Claude)
│   ├── create-repo/            # create-github-repo — new repo + collaborator invite in one command
│   └── precommit/              # qa-toolbox-precommit — 10-gate pre-commit stack for Python QA repos
│
├── env-python-py-scripts/
│   └── setup-python-env/       # dev-setup-kit — AI-powered Python + PyCharm installer
│
└── prompts/
    ├── cv-ats/                  # CV-ATS-Optimizer — ATS-tailored CV + cover letter prompt
    └── optimus-prompt/          # optimus-prompt — universal XML prompt template for Claude
```

---

## 📌 Roadmap

### AI Agents
- [x] SmokeSentinel — Gherkin generator (LLM-based)
- [x] SmokeSentinel — Playwright MCP client
- [x] SmokeSentinel — Slack & Teams notifier
- [ ] SmokeSentinel — Full agent pipeline (executor → healer → reporter)
- [ ] SmokeSentinel — CI/CD pipeline templates (GitHub Actions, GitLab CI)
- [ ] SmokeSentinel — Jira test result sync
- [x] cy-commands-ai — `cy.aiAssert()`, `cy.aiTriage()`, `cy.aiGenerateTestCase()`
- [x] cy-commands-ai — Reliability evaluation layer + LangSmith tracing
- [ ] cy-commands-ai — `cy.aiA11yReview()` accessibility agent
- [ ] Qarvis — Playwright MCP live integration (selector discovery, dry-runs)
- [ ] PR Smoke Gate — Full Playwright suite (Sauce Demo + Amazon + Next.js Commerce)

### Scripts & Tools
- [x] git-commit-push-safe — stable
- [x] git-commit-push-ai — Ollama + Anthropic providers
- [x] create-github-repo — stable
- [x] qa-toolbox-precommit — 10-gate stack
- [x] dev-setup-kit — Python + PyCharm + 25 plugins
- [ ] dev-setup-kit — `setup_git.py`, `setup_wsl.py`, `setup_node.py`, `setup_docker.py`

### Prompts
- [x] CV-ATS-Optimizer — stable
- [x] optimus-prompt — stable

⭐ Star this repo to follow the progress.

---

## 👤 Author

**Khalid Hafid-Medheb**
Senior SDET & AI Engineer — specialized in autonomous QA agents (HealthTech / BioTech)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-khalid--hafid--medheb-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)
[![Org](https://img.shields.io/badge/Org-Kallitests-6e40c9?style=flat-square)](https://github.com/kallitests)

---

*Built with 🧠 Claude (Anthropic) · 🎭 Playwright · 🌲 Cypress · 🦜 LangChain · 🦙 Ollama*
