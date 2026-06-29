# agentic-qa
💡 An idea box of AI agents for QA Automation & SDET (Software Engineer in Test). Flaky tests. Vague MRs. Broken pipelines at 2am. I automate tests — then I automate the automation. 20 production-grade AI agents covering the full QA & DevOps lifecycle: user story generation, Gherkin scenarios, PowerBI reporting, flaky detection, CI/CD monitoring, Jira triage, MR reviews. LangGraph · Claude · MCP · GitLab · Jira. ISTQB® SDET · 10+ yrs.

# 💡 AI Agents Idea Box for QA Automation & SDET — agentic-qa - Portfolio

> **Khalid HAFID-MEDHEB** · SDET Freelance · ISTQB® · 10+ years QA & Dev  
> Building autonomous AI agents at the intersection of **test automation**, **DevOps**, and **agentic AI**.

[![ISTQB](https://img.shields.io/badge/Certified-ISTQB®%20Foundation-green)](https://www.istqb.org/)
[![Status](https://img.shields.io/badge/status-WIP-orange?style=flat-square)](https://github.com/khafid1506/SmokeSentinel)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-agent-blueviolet?style=flat-square)](https://langchain.com)
[![Playwright](https://img.shields.io/badge/Playwright-MCP-green?style=flat-square&logo=playwright)](https://playwright.dev)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-black?style=flat-square)](https://anthropic.com)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker)](https://docker.com)

---

## 📚 Table of Contents

- [Philosophy](#-philosophy)
- [Tech Stack](#-tech-stack)
- [Projects](#-projects)
    - [SDET & Test Automation Agents](#-sdet--test-automation-agents)
    - [DevOps & CI/CD Agents](#-devops--cicd-agents)
    - [Jira & Ticketing Agents](#-jira--ticketing-agents)
    - [Merge Request & Code Review Agents](#-merge-request--code-review-agents)
    - [Original & Crossover Agents](#-original--crossover-agents)
    - [Requirements & Reporting Agents](#-requirements--reporting-agents)
- [Why SDET × AI Agents?](#-why-sdet--ai-agents)
- [Connect](#-connect)

---

## 💡 Philosophy

> *Most AI engineers know how to build agents. Few know how to make them reliable.  
> I do — because I've spent 10 years breaking software on purpose.*

These projects solve **real SDET and DevOps pain points** using autonomous AI agents built with LangGraph, CrewAI, Anthropic Claude SDK, and MCP. Each agent targets a specific friction point in the QA/DevOps lifecycle — the kind of pain you only feel after years of pipelines, flaky tests, and 2am incidents.

---

## 🛠 Tech Stack

| Layer | Tools |
|---|---|
| **Agent Frameworks** | LangGraph · CrewAI · AutoGen · Anthropic Agents SDK |
| **LLMs** | Claude (Anthropic) · GPT-4o · Mistral |
| **Protocol** | MCP (Model Context Protocol) |
| **Test Ecosystem** | Cypress · Cucumber/Gherkin · JUnit · Playwright · RabbitMQ |
| **DevOps** | GitLab CI · Docker · GitHub Actions · Shell scripting |
| **Ticketing** | Jira REST API · Confluence API |
| **Reporting** | Power BI · Playwright HTML Reporter |
| **Observability** | LangSmith · Grafana · Prometheus |
| **Language** | Python · Java · JavaScript |

---

## 📁 Projects

---

### 🧪 SDET & Test Automation Agents

---

#### 01 · `gherkin-scenario-agent`

**🎯 QA Agent — Gherkin Scenario Generator**

You paste a user story or a functional spec. The agent generates complete Gherkin scenarios — happy path, edge cases, KO paths — validates the syntax, maps each scenario to the right feature file folder, and commits the result directly to your repo. No more hours spent writing `.feature` files by hand.

> **Pain point solved:** Writing BDD scenarios from scratch is slow, inconsistent, and often incomplete on edge cases.  
> **Stack:** LangGraph · Anthropic Claude · Python · Git API

---

#### 02 · `flaky-test-detective`

**🔍 Flaky Test Detective**

An agent that ingests your GitLab CI/CD pipeline logs over the last N runs, identifies unstable tests, and classifies each flaky failure into one of four categories: ENV infrastructure issue, timing race condition, test data collision, or real product bug. Outputs a structured investigation report with actionable fix recommendations per scenario.

> **Pain point solved:** Flaky tests are the #1 killer of CI/CD confidence. Triage is manual and time-consuming.  
> **Stack:** LangGraph · GitLab API · Python · Anthropic Claude

---

#### 03 · `rabbitmq-event-flow-tester`

**🐇 RabbitMQ Event Flow Tester Agent**

You describe an asynchronous event flow — exchanges, queues, routing keys, expected consumer behaviour. The agent generates the test scenarios, publishes events to RabbitMQ, polls the consumer side, and asserts the expected state transitions. End-to-end message flow testing without writing a single line of test code.

> **Pain point solved:** Testing async event-driven architectures manually is error-prone and hard to reproduce.  
> **Stack:** LangGraph · RabbitMQ AMQP · Python · Pika · Anthropic Claude

---

#### 04 · `test-coverage-gap-hunter`

**📊 Test Coverage Gap Hunter**

An agent that cross-references your source code, existing feature files, and OpenAPI spec to identify untested paths. It scores each gap by business risk and criticality, then generates the missing test scenarios prioritised by impact. Shift-left testing, piloted by AI.

> **Pain point solved:** Coverage gaps are only discovered in production. No tooling connects code, specs, and tests intelligently.  
> **Stack:** LangGraph · AST parsing · Anthropic Claude · Python

---

#### 05 · `postman-collection-builder-agent`

**📬 Postman Collection Builder Agent**

You drop in an OpenAPI/Swagger spec or a set of BDD feature files. The agent generates a complete Postman collection: requests, assertions, pre-request scripts, environment variables, and edge case coverage — ready to import and run. What used to take half a day takes 30 seconds.

> **Pain point solved:** Building Postman collections manually from specs is repetitive, incomplete, and rarely kept in sync.  
> **Stack:** LangGraph · OpenAPI parser · Anthropic Claude · Python

---

#### 06 · `bug-report-triage-agent`

**🐛 Bug Report Analyzer & Triage Agent**

An agent that ingests Surefire XML reports, JUnit output, and raw pipeline logs after a red build. It classifies each failure (regression, ENV, new bug, flaky), assigns a severity score, correlates failures across test suites, and produces a ready-to-paste Jira ticket for each real defect. Zero manual triage time after a broken pipeline.

> **Pain point solved:** Post-failure triage is the most time-consuming part of a QA engineer's day — and the least valuable.  
> **Stack:** LangGraph · JUnit XML parser · Jira REST API · Anthropic Claude

---

### ⚙️ DevOps & CI/CD Agents

---

#### 07 · `pipeline-health-monitor-agent`

**🛡️ CI/CD Pipeline Health Monitor Agent**

A continuous agent that queries the GitLab API, tracks stability KPIs (pass rate, duration trends, recurring failure patterns), classifies failures as ENV or LEGIT, and sends structured Teams/Slack alerts with root cause analysis and corrective action proposals. Think `runPipelineStats.sh` — but intelligent, conversational, and self-improving.

> **Pain point solved:** Pipeline instability is detected too late, reported poorly, and investigated manually.  
> **Stack:** LangGraph · GitLab API · Microsoft Teams Webhook · Python

---

#### 08 · `docker-compose-debugger-agent`

**🐳 Docker Compose Debugger Agent**

An agent that monitors your `docker-compose` test stack during CI runs, detects container crashes, port conflicts, health check failures, and OOM kills, then diagnoses the root cause and suggests a corrective `docker-compose.yml` patch — before the pipeline even fails.

> **Pain point solved:** Docker issues in CI are opaque, hard to reproduce locally, and eat hours of debugging time.  
> **Stack:** LangGraph · Docker SDK · Python · Anthropic Claude

---

#### 09 · `release-readiness-agent`

**🚀 Release Readiness Agent**

Before any deployment, this agent autonomously checks: test pass rate threshold met, no open P0/P1 Jira tickets, Docker image tagged and pushed, smoke tests green, feature flags configured, and rollback plan documented. It produces a signed release readiness report and blocks the pipeline if any gate fails.

> **Pain point solved:** Release go/no-go decisions are manual, inconsistent, and often miss critical checks under pressure.  
> **Stack:** CrewAI · GitLab API · Jira API · Docker Hub API · Anthropic Claude

---

#### 10 · `incident-postmortem-agent`

**🔥 Incident Post-Mortem Writer Agent**

After a production incident or a major pipeline failure, this agent collects timeline data from GitLab logs, Jira tickets, and Teams alerts, reconstructs the chronology of events, identifies the root cause, and writes a structured post-mortem document (5 Whys + action items) ready to publish in Confluence.

> **Pain point solved:** Post-mortems are written late, incompletely, or not at all — institutional memory is lost.  
> **Stack:** LangGraph · GitLab API · Confluence API · Anthropic Claude · Python

---

### 🎫 Jira & Ticketing Agents

---

#### 11 · `jira-ticket-writer-agent`

**📝 Jira Ticket Writer Agent**

You describe a bug verbally or paste a log snippet. The agent generates a properly structured Jira ticket: summary, description, steps to reproduce, expected vs actual result, severity, labels, component, and a suggested assignee based on the affected module. One sentence in, one perfect ticket out.

> **Pain point solved:** Poorly written tickets waste developer time and get rejected or mis-prioritised. Writing good tickets is an underrated skill that takes time.  
> **Stack:** LangGraph · Jira REST API · Anthropic Claude · Python

---

#### 12 · `jira-sprint-triage-agent`

**📋 Sprint Triage & Backlog Grooming Agent**

A multi-agent system that reads your Jira backlog, scores each ticket by business value, technical risk, and test coverage required, detects duplicates and stale tickets, and proposes an optimised sprint plan with effort estimates. Grooming meetings in 5 minutes instead of 2 hours.

> **Pain point solved:** Backlog grooming is one of the most hated Agile ceremonies — slow, subjective, and often skipped.  
> **Stack:** CrewAI · Jira REST API · Anthropic Claude · Python

---

#### 13 · `test-evidence-collector-agent`

**📎 Test Evidence Collector Agent**

An agent that automatically links test execution results (Cucumber reports, JUnit XML, screenshots) to their corresponding Jira tickets after each pipeline run. It updates ticket status, attaches artefacts, adds a structured comment with pass/fail summary, and closes validated tickets — with zero human intervention.

> **Pain point solved:** Updating Jira tickets with test evidence is a manual, repetitive task that QA engineers skip under deadline pressure.  
> **Stack:** LangGraph · Jira REST API · GitLab Artifacts API · Anthropic Claude

---

### 🔀 Merge Request & Code Review Agents

---

#### 14 · `mr-quality-gate-agent`

**🔎 Merge Request Quality Gate Agent**

An agent triggered on every MR that reviews the diff, checks for missing test coverage on new code paths, flags untested edge cases, verifies Gherkin scenarios exist for new features, and posts a structured QA review comment directly on the MR — before a human reviewer even opens it.

> **Pain point solved:** Code reviews rarely catch missing tests. QA is brought in too late in the MR lifecycle.  
> **Stack:** LangGraph · GitLab MR API · Anthropic Claude · Python · AST diff analysis

---

#### 15 · `mr-description-agent`

**✍️ Merge Request Description Generator**

The laziest thing developers do is write MR descriptions. This agent reads the git diff, commit messages, and linked Jira ticket, then writes a complete MR description: what changed, why, how to test it, deployment notes, and rollback procedure. Reviewers get context. Developers save time.

> **Pain point solved:** Vague MR descriptions slow down reviews, block QA, and make git history useless for future debugging.  
> **Stack:** LangGraph · GitLab API · Jira API · Anthropic Claude · Python

---

### 🌟 Original & Crossover Agents

---

#### 16 · `test-oracle-agent`

**🔮 Test Oracle Agent — AI-Powered Expected Result Generator**

The hardest part of writing a test is knowing what the expected result should be. This agent analyses your business rules, API contract, and historical test data to generate precise expected values for each test scenario — including boundary values, null cases, and format constraints. No more `// TODO: add assertion`.

> **Pain point solved:** Defining expected results requires deep domain knowledge that is undocumented, implicit, and siloed in people's heads.  
> **Stack:** LangGraph · Anthropic Claude · OpenAPI parser · Python

---

#### 17 · `qa-knowledge-base-agent`

**🧠 QA Knowledge Base Agent (MCP Server)**

A fully agentic knowledge base built as an MCP server that indexes your Confluence documentation, Gherkin feature files, Jira tickets, and past incident reports. Answers questions like *"Has this bug been reported before?"*, *"Which scenarios cover the payment flow?"*, or *"What was the root cause of last month's P0?"* — instantly, in natural language.

> **Pain point solved:** QA knowledge is scattered across Confluence, Jira, Slack, and people's memories. Onboarding and debugging take weeks instead of hours.  
> **Stack:** MCP (Model Context Protocol) · Anthropic Claude · Confluence API · Jira API · Python · Vector Store

---

### 📋 Requirements & Reporting Agents

---

#### 18 · `user-story-generator-agent`

**📖 User Story Generator Agent**

You drop in a functional or technical specification document — PDF, Confluence page, or plain text. The agent reads the spec, extracts business intent and acceptance criteria, and generates a complete set of well-structured user stories following the *As a / I want / So that* format, enriched with definition of done, edge cases, and suggested story points. From specs to backlog in seconds.

> **Pain point solved:** Translating dense specification documents into actionable user stories is slow, inconsistent, and often loses critical edge cases along the way.  
> **Stack:** LangGraph · Anthropic Claude · Python · PDF/Confluence parser

---

#### 19 · `gherkin-from-user-story-agent`

**🥒 Gherkin Scenario Generator from User Story**

You feed the agent a user story. It generates complete, production-ready Gherkin scenarios in `.feature` format — covering the happy path, alternative flows, edge cases, and KO paths. Each scenario is properly tagged, mapped to the right feature file folder, and validated for BDD syntax. From story to executable spec in one shot.

> **Pain point solved:** Writing BDD scenarios from user stories requires both QA expertise and time — two things that are always scarce before a sprint starts.  
> **Stack:** LangGraph · Anthropic Claude · Python · Git API · Cucumber/Gherkin

---

#### 20 · `playwright-powerbi-reporter-agent`

**📊 Playwright → Power BI Reporting Agent**

After your Playwright test suite runs, this agent ingests the JSON/HTML execution results, transforms them into a structured dataset, and generates a ready-to-import Power BI report: pass/fail trends by suite and feature, flakiness heatmap, test duration distribution, and coverage delta vs previous run. Your QA dashboard, built automatically after every pipeline.

> **Pain point solved:** Test results live in raw JSON files no stakeholder ever reads. Translating execution data into meaningful management reporting is a manual, time-consuming task that rarely happens.  
> **Stack:** LangGraph · Anthropic Claude · Playwright JSON Reporter · Python · Power BI REST API

---

## 🎯 Why SDET × AI Agents?

Most AI engineers can build an agent. Very few can make it **production-grade, observable, and reliable**.

I can — because 10 years of breaking software on purpose taught me:

- How systems fail under real conditions (not happy-path demos)
- How to design assertions that catch the right things
- How to monitor what matters and ignore noise
- How to write documentation that survives its author

These projects are not demos. They are tools built to solve pain I have felt personally — writing Gherkin at 11pm, triaging flaky tests on a Friday, debugging a Docker container no one understands.

**The intersection of SDET expertise and agentic AI is still wide open. That is where I operate.**

---

---

## 📬 Connect

| | |
|---|---|
| 📧 Email | khafid1506@gmail.com |
| 💼 LinkedIn | [khalid-hafidmedheb](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/) |
| 🐙 GitHub | [kallitests](https://github.com/kallitests) |
| 🐦 X / Twitter | [@kallitests](https://x.com/kallitests) |
| 📍 Location | Montgeron — Full Remote FR/EU |

---

> *"Software quality as an engineering discipline — not a safety net."*  
> — Khalid HAFID-MEDHEB