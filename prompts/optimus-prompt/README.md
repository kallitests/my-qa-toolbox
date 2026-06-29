<div align="center">

# 🧠 optimus-prompt

### The Universal XML Prompt Template for Claude

*Precision · Anti-hallucination · Token efficiency · Clarity*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Prompt: XML](https://img.shields.io/badge/Format-XML-blue)]()
[![LLM: Claude](https://img.shields.io/badge/Optimised%20for-Claude%20(Anthropic)-purple)](https://www.anthropic.com)
[![Author](https://img.shields.io/badge/Author-Khalid%20HAFID--MEDHEB-black)](https://www.linkedin.com/in/khalid-hafidmedheb-40451aa8)

</div>

---

## 📌 What is this?

**optimus-prompt** is a battle-tested XML prompt template designed for Claude (Anthropic).

XML is the optimal format for Claude prompts because:
- Claude was trained to understand XML structure as a hierarchy of instructions
- Tags act as named containers — Claude knows exactly what each section means
- Nested tags encode priority and relationships between instructions
- It is unambiguous, machine-readable, and human-readable at the same time

This template eliminates the four most common prompt failures:

| Failure | Cause | How this template fixes it |
|---|---|---|
| Hallucinated code / APIs | No grounding | `<context>` + `<anti_hallucination_rules>` |
| Vague output | No format spec | `<output_format>` + `<examples>` |
| Wasted tokens | Over-specified prompts | One-purpose-per-tag discipline |
| Wrong scope | No constraints | `<constraints>` with hard rules |

---

## 🗂 Repository structure

```
optimus-prompt/
├── optimus-prompt.xml     # ← The main template (copy this)
└── README.md              # ← This file
```

---

## ⚡ Quick start

1. Open `optimus-prompt.xml`
2. Fill in every `[FILL IN: ...]` placeholder
3. Delete sections that do not apply to your task
4. Delete all `<!-- comment -->` lines
5. Paste the result into Claude

---

## 🏗 Template architecture

The template has **10 sections**, ordered from broadest to most specific.
Claude reads top-to-bottom — each section narrows the task before the next adds detail.

```
<prompt>
  ├── <role>                    # Who Claude is for this task
  ├── <context>                 # Project facts Claude cannot know on its own
  ├── <objective>               # The ONE deliverable Claude must produce
  ├── <instructions>            # Ordered steps to reach the objective
  ├── <constraints>             # Hard rules — what Claude must NOT do
  ├── <output_format>           # Exact shape, length, and language of the output
  ├── <examples>                # Good and bad examples to anchor the response
  ├── <clarification_policy>    # When Claude should ask vs proceed
  ├── <anti_hallucination_rules># Global safety net against invented facts
  └── <task>                    # The actual user input (swap this to reuse the template)
</prompt>
```

---

## 📖 Section-by-section reference

### `<role>`
Sets Claude's expert identity for the conversation.
**Rule:** one identity, one sentence. Do not stack multiple roles.

```xml
<role>
  You are a senior SDET with 10+ years of experience in BDD,
  test automation, and AI-assisted QA pipelines.
</role>
```

---

### `<context>`
Grounds Claude in your project reality. Without this, Claude fills gaps with plausible-sounding hallucinations.
**Rule:** include only facts that change the answer. Delete generic filler.

```xml
<context>
  <project>agentic-qa — a portfolio of 20 AI agents for QA automation</project>
  <tech_stack>Python · LangGraph · Anthropic Claude · Playwright · Gherkin</tech_stack>
  <current_situation>
    New agent needed. Existing agents use LangGraph state-machine pattern
    with typed state dicts.
  </current_situation>
</context>
```

---

### `<objective>`
The single most important section. One concrete sentence starting with an action verb.

```xml
<objective>
  Generate a complete, production-ready Python LangGraph agent that ingests
  a Playwright JSON test report and produces a structured CSV dataset
  ready to import into Power BI.
</objective>
```

---

### `<instructions>`
Step-by-step ordered actions. Each step = one action in imperative mood.
Flag mandatory vs optional with `[REQUIRED]` / `[OPTIONAL]`.

```xml
<instructions>
  <step order="1">[REQUIRED] Define the LangGraph state dict with typed fields.</step>
  <step order="2">[REQUIRED] Implement the ingestion node.</step>
  <step order="3">[OPTIONAL] Add error handling for malformed reports.</step>
</instructions>
```

---

### `<constraints>`
Hard rules that override any default behaviour.
**Rule:** write constraints as prohibitions, not preferences.

```xml
<constraints>
  <hard_rule>Use only Python standard library + LangGraph + pandas.</hard_rule>
  <hard_rule>All node functions must use Python type hints.</hard_rule>
  <hard_rule>Do NOT invent API methods that do not exist. If unsure, say so.</hard_rule>
  <hard_rule>If you do not know something with certainty, say "I am not sure"
  rather than inventing an answer.</hard_rule>
</constraints>
```

---

### `<output_format>`
Tells Claude the exact shape of its response. Eliminates format surprises.

```xml
<output_format>
  <format>A single Python code block followed by a 5-line usage example.</format>
  <structure>
    1. Module-level docstring
    2. Imports
    3. State dict
    4. Node functions
    5. Graph wiring
    6. __main__ block
  </structure>
  <length>As short as correct allows. No padding comments.</length>
  <language>English only.</language>
</output_format>
```

---

### `<examples>`
The most powerful anti-hallucination lever. Shows Claude the exact vocabulary and style expected.
A `<bad_example>` is even more effective than a good one — it explicitly rules out common failure modes.

```xml
<examples>
  <good_example label="Expected node function signature">
    <![CDATA[
      def ingest_report(state: AgentState) -> AgentState:
          """Parse Playwright JSON and store results in state."""
          with open(state["report_path"]) as f:
              state["raw_results"] = json.load(f)
          return state
    ]]>
  </good_example>
  <bad_example label="Pattern to avoid">
    <![CDATA[
      # Do NOT use a class-based pattern:
      class PlaywrightAgent:
          def __init__(self): ...
    ]]>
  </bad_example>
</examples>
```

---

### `<clarification_policy>`
Controls when Claude asks questions vs proceeds.
Choose one of three modes:

| Mode | When to use |
|---|---|
| **A — Ask first** | Complex open-ended tasks where a wrong assumption wastes significant work |
| **B — Proceed with assumptions** | Simple tasks where assumptions are easy to correct |
| **C — Hybrid (recommended)** | Most tasks — ask only if ambiguity breaks correctness |

```xml
<clarification_policy>
  Proceed with reasonable assumptions for minor ambiguities.
  Ask ONE question only if a missing detail would make the output incorrect
  or require a full rewrite. State the question before producing any output.
</clarification_policy>
```

---

### `<anti_hallucination_rules>`
A global safety net. Keep this section as-is in every prompt.
~60 tokens — consistently prevents fabricated library methods, fake URLs, and invented API signatures.

```xml
<anti_hallucination_rules>
  <rule>Do NOT invent library methods or API endpoints you are not certain exist.</rule>
  <rule>Do NOT cite documentation URLs unless certain they are real and current.</rule>
  <rule>If a detail might have changed, say: "Please verify in the official docs."</rule>
  <rule>Prefer a shorter, accurate answer over a longer answer with uncertain content.</rule>
  <rule>If two options are equally valid, say so rather than picking one without reason.</rule>
</anti_hallucination_rules>
```

---

### `<task>`
The actual user input. Separated from configuration so the template is fully reusable — swap only this section for each new task.

```xml
<task>
  Generate the agent described in <objective>.
  Follow all <instructions> in order.
  Respect all <constraints>.
  Format output as specified in <output_format>.
  Apply <clarification_policy> if anything is unclear.
</task>
```

---

## 🎯 Design principles

**One purpose per tag.**
Every section has a single job. Do not mix context and instructions. Do not put constraints in the task.

**Order encodes priority.**
Role → Context → Objective → Instructions → Constraints. Claude processes top-to-bottom; earlier sections frame later ones.

**Explicit beats implicit.**
Never rely on Claude to infer your constraints, format, or assumptions. State them. The cost is a few tokens; the benefit is a correct first answer.

**Short and accurate beats long and uncertain.**
Padding a prompt with vague requirements produces vague output. Be sparse and specific.

**Examples are not optional for complex tasks.**
A 10-line code example eliminates more ambiguity than 200 words of description.

---

## 🔧 Adapting the template

| Use case | Sections to keep | Sections to drop |
|---|---|---|
| Code generation | All | — |
| Document writing | role, context, objective, output_format, task | examples (optional) |
| Data analysis | role, context, objective, instructions, constraints, task | — |
| Simple Q&A | objective, anti_hallucination_rules, task | role, context, examples |
| Agent system prompt | role, context, constraints, anti_hallucination_rules | clarification_policy, task |

---

## 📬 Connect

| | |
|---|---|
| 💼 LinkedIn | [khalid-hafidmedheb](https://www.linkedin.com/in/khalid-hafidmedheb-40451aa8) |
| 🐙 GitHub | [kallitests](https://github.com/kallitests) |
| 🌍 Location | Montgeron — Full Remote FR/EU |

---

> *"A model is only as precise as the instruction it receives."*
> — Khalid HAFID-MEDHEB
