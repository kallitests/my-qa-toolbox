# 🎯 CV-ATS-Optimizer Prompt

> **A master prompt that turns Claude into a senior ATS/recruiting expert.**
> Feed it your CV (.docx) + a job offer (text, URL, or PDF), and it analyzes your ATS match, flags real gaps, and generates a tailored one-page CV and cover letter — without ever inventing a skill, a number, or an experience you don't have.

[![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)](https://github.com/kallitests/CV-ATS-Optimizer)
[![Type](https://img.shields.io/badge/type-prompt-blueviolet?style=flat-square)](#)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-black?style=flat-square)](https://anthropic.com)
[![Languages](https://img.shields.io/badge/output-FR%20%2F%20EN-blue?style=flat-square)](#-language-detection)
[![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)](#-license)

---

## 🗺️ Table of Contents

- [Why this prompt?](#-why-this-prompt)
- [What it does](#%EF%B8%8F-what-it-does)
- [Pipeline](#-pipeline)
- [Core principle: zero fabrication](#-core-principle-zero-fabrication)
- [Inputs](#-inputs)
- [Language detection](#-language-detection)
- [Deliverables](#-deliverables)
- [Output structure](#-output-structure)
- [File naming](#-file-naming)
- [Getting Started](#-getting-started)
- [Roadmap](#-roadmap)
- [Author](#-author)

---

## 💡 Why This Prompt?

Most "AI CV optimizers" either rewrite your CV into generic buzzword soup, or quietly invent skills and metrics to match the job offer — which falls apart at the first technical interview.

This prompt does the opposite:

> *"Maximize my ATS score and my interview chances — without lying about who I am."*

It forces a clarification step before producing anything, runs a real keyword-by-keyword gap analysis against the job offer, and explicitly **flags every missing skill instead of papering over it**.

```
CV (.docx) + Job Offer (text/URL/PDF) ──▶ ATS Analysis ──▶ Keyword Gap Map ──▶ Optimized CV + Cover Letter
```

---

## ⚙️ What It Does

| Step | Description |
|------|-------------|
| 🔍 **Offer parsing** | Auto-detects text / URL / PDF, extracts role, missions, required & nice-to-have skills, seniority, ATS keywords — ignores marketing fluff |
| 🧭 **Clarification first** | Reformulates the request, asks 1–3 clarifying questions if anything is ambiguous, before producing anything |
| 📊 **ATS scoring** | Estimates an initial ATS match score, seniority fit, strengths, weaknesses, blocking gaps |
| 🔑 **Keyword gap analysis** | Builds a Critical / Important / Secondary keyword table with presence status and required action |
| 🧩 **Skill mapping** | Classifies skills as present, present-under-another-name (e.g. *Behat → Behave*), or genuinely missing |
| 📝 **CV rewrite** | Produces a one-page, single-column, ATS-friendly CV (no tables, icons, images, or text boxes) tailored to the offer |
| ✉️ **Cover letter** | Generates a Me / You / Us structured cover letter, readable in under 60 seconds |
| 🌐 **Bilingual output** | Detects the offer's language and produces matching CV + cover letter (FR or EN) |
| 📄 **File generation** | Outputs ready-to-send `.docx` files, correctly named, with zero manual confirmation step once inputs are confirmed |

---

## 🔄 Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CV-ATS-Optimizer                             │
│                                                                        │
│   ┌──────────────┐     ┌────────────────┐     ┌────────────────────┐ │
│   │  CV (.docx)  │────▶│  ATS Analysis   │────▶│  Keyword Gap Table  │ │
│   │  Job Offer   │     │  (score + gaps) │     │  (critical/missing) │ │
│   └──────────────┘     └────────────────┘     └──────────┬──────────┘ │
│                                                            │           │
│   ┌──────────────┐     ┌────────────────┐     ┌──────────▼──────────┐ │
│   │ .docx files  │◀────│  Cover Letter   │◀────│   Optimized CV       │ │
│   │ (CV + LM)    │     │  (Me/You/Us)    │     │   (1 page, ATS-safe) │ │
│   └──────────────┘     └────────────────┘     └──────────────────────┘ │
│                                                                        │
│   🚫 Zero invented skills, numbers, or experience — gaps always flagged │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🚫 Core Principle: Zero Fabrication

This is the non-negotiable rule the whole prompt is built around. The model **never invents**:

- experiences
- skills
- certifications
- degrees
- responsibilities
- numbers / metrics

Every keyword from the offer that isn't genuinely backed by the CV is surfaced as **missing**, with an explicit question back to the candidate rather than a silent rewrite. If a close-but-different skill exists (e.g. PHP's *Behat* vs Python's *Behave*), the prompt requires an honest transposition statement — never a disguised equivalence.

It also catches the model's own reasoning errors: inconsistent dates, a job title that doesn't match the described scope, etc. — flagged instead of smoothed over.

---

## 📥 Inputs

| Input | Required | Format |
|-------|----------|--------|
| **CV** | ✅ | `.docx` |
| **Job offer** | ✅ | Pasted text · URL · PDF (auto-detected) |
| **Additions** (new experience, skills, certifications, training) | ➖ Optional | Structured fields |

If the offer is missing, unreadable, or a link fails to load, the prompt stops and asks — it never analyzes a generic/default job instead.

---

## 🌐 Language Detection

| Offer language | Output |
|-----------------|--------|
| 🇫🇷 French | CV (FR) + Lettre de motivation (FR) |
| 🇬🇧 English | Resume (EN) + Cover Letter (EN) |

Ambiguous / bilingual offers → the prompt asks for confirmation before producing anything.

---

## 📦 Deliverables

1. Request reformulation + clarifying questions (if needed)
2. Full ATS analysis (score, seniority, strengths, weaknesses, blocking gaps)
3. Keyword gap table (Critical / Important / Secondary)
4. Optimized one-page CV
5. Optimized cover letter
6. Improvement suggestions, including an explicit question on any missing critical skill
7. Initial ATS score estimate
8. Final ATS score estimate
9. Generated `.docx` files — no confirmation step required once inputs are unambiguous

---

## 🏗️ Output Structure

**CV (1 page, ATS-safe: single column, no table/image/icon/emoji/chart/text box)**

```
Header → Professional Summary (4–6 lines) → Key Skills (by category)
       → Professional Experience (Action → Impact → Value, per role)
       → Education → Certifications
```

**Cover Letter (FR: 200–300 words · EN: 250–350 words)**

```
§1 — ME    → background, expertise, fit for the role
§2 — YOU   → understanding of the company, its challenges, the offer
§3 — US    → what I bring, ownership, expected impact
```

---

## 💼 LinkedIn "About" Section Generator

An optional add-on module: once your optimized CV exists, generate a matching LinkedIn "About" section from the same source material — no separate input needed.

| Aspect | Detail |
|--------|--------|
| **Input** | The already-optimized CV (no new info requested) |
| **Length** | 80–120 words, first-person, scannable in under 15 seconds |
| **Structure** | Hook (who I am + core expertise) → proof (concrete experience, no invented metrics) → what I'm looking for / CTA |
| **Tone** | Same constraints as the CV/cover letter: factual, senior, zero corporate jargon ("passionate", "synergy", "rockstar" banned) |
| **Zero fabrication** | Inherits the same rule as the rest of the prompt — nothing appears in the About section that isn't already in the CV |
| **Output** | Plain text block, ready to paste into LinkedIn (LinkedIn has no rich formatting beyond line breaks and emoji bullets, so no Markdown is generated) |

Usage: after the CV is generated and validated, ask Claude *"generate the LinkedIn About section from this CV"* in the same conversation.

---

## 🏷️ File Naming

| Document | Pattern |
|----------|---------|
| CV (French) | `CV_[NAME]_[COMPANY].docx` |
| Resume (English) | `RESUME_[NAME]_[COMPANY].docx` |
| Lettre (French) | `LM_[NAME]_[COMPANY].docx` |
| Cover Letter (English) | `COVER_LETTER_[NAME]_[COMPANY].docx` |

---

## 🚀 Getting Started

1. Copy the prompt from [`prompt-cv-ats.md`](./prompt-cv-ats.md) into a new Claude conversation.
2. Attach your CV as a `.docx` file.
3. Paste the job offer (text, URL, or PDF) in the same message.
4. Answer the clarifying questions if Claude asks any.
5. Get your ATS analysis + optimized CV + cover letter as downloadable `.docx` files.

---

## 📌 Roadmap

- [x] Core prompt: ATS analysis + keyword gap table
- [x] One-page CV generation (FR/EN)
- [x] Cover letter generation (Me/You/Us structure)
- [x] Zero-fabrication / missing-skill flagging rules
- [x] Clarification-first posture (reformulate → ask → plan)
- [x] LinkedIn "About" section generator
- [ ] Multi-offer batch mode (compare CV against several offers at once)
- [ ] PDF export alongside `.docx`

---

## 👤 Author

**Khalid Hafid-Medheb**
QA Automation Engineer | SDET — Playwright · Cypress · CI/CD

[![LinkedIn](https://img.shields.io/badge/LinkedIn-khalid--hafid--medheb-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/khalid-hafid-medheb-40451aa8/)
[![GitHub](https://img.shields.io/badge/GitHub-kallitests-181717?style=flat-square&logo=github)](https://github.com/kallitests)

---

## 📄 License

MIT — use it, fork it, adapt it to your own job search.

---

*Built with 🧠 Claude (Anthropic)*
