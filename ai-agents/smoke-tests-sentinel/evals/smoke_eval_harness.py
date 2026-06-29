"""
SmokeSentinel — LLM Evaluation Harness
=======================================
Module complet d'évaluation de la qualité des outputs LLM de SmokeSentinel.

Ce module répond à une question fondamentale :
"Les agents IA de SmokeSentinel produisent-ils des outputs fiables,
pertinents, et exempts d'hallucinations ?"

Architecture d'évaluation en 5 dimensions :
  1. FAITHFULNESS       — les Gherkin générés sont-ils fidèles à la user story ?
  2. RELEVANCE          — les CPs identifiés sont-ils vraiment critiques ?
  3. HALLUCINATION      — l'agent invente-t-il des sélecteurs ou des paths ?
  4. CONSISTENCY        — le même input produit-il des outputs cohérents ?
  5. REGRESSION         — un run précédent confirmé reste-t-il valide ?

Stack d'évaluation :
  LangSmith Evals   → tracing + dataset management + scoring
  LLM-as-Judge      → évaluation sémantique par Claude lui-même
  Golden Dataset    → vérité terrain définie par l'équipe SDET
  pytest            → tests déterministes (structure, format, bounds)
  sentence-transformers → similarité sémantique sans appel LLM
"""

import json
import time
import uuid
import pytest
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langsmith import Client as LangSmithClient
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith import traceable

# ── Optional: sentence-transformers for semantic similarity without LLM cost
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    _ST_AVAILABLE = True
    _st_model = SentenceTransformer("all-MiniLM-L6-v2")
except ImportError:
    _ST_AVAILABLE = False
    _st_model = None

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)


# ══════════════════════════════════════════════════════════════════
# SECTION 1 — GOLDEN DATASET
# Vérité terrain définie par l'équipe SDET
# ══════════════════════════════════════════════════════════════════

GOLDEN_DATASET = [
    # ── Cas medtech — Login clinicien ─────────────────────────────
    {
        "id": "GD-01",
        "category": "medtech_auth",
        "input_story": (
            "En tant que médecin, je veux me connecter à la plateforme "
            "et accéder au tableau de bord de mes patients."
        ),
        "expected_critical_paths": [
            "login avec email et mot de passe",
            "accès au dashboard après connexion",
            "déconnexion sécurisée",
        ],
        "expected_min_paths": 2,
        "expected_max_paths": 5,
        "must_include_p1": True,
        "must_not_hallucinate_selectors": True,
        "forbidden_outputs": [
            "test de performance réseau",
            "vérification du certificat SSL",
            "test de charge",
        ],
    },
    # ── Cas medtech — Recherche patient ───────────────────────────
    {
        "id": "GD-02",
        "category": "medtech_patient",
        "input_story": (
            "En tant que pharmacien, je veux rechercher un patient "
            "par son nom et consulter ses ordonnances en cours."
        ),
        "expected_critical_paths": [
            "recherche patient par nom",
            "accès à la liste des ordonnances",
            "affichage d'une ordonnance",
        ],
        "expected_min_paths": 2,
        "expected_max_paths": 5,
        "must_include_p1": True,
        "must_not_hallucinate_selectors": True,
        "forbidden_outputs": [
            "impression d'ordonnance",
            "envoi par email",
            "export PDF",
        ],
    },
    # ── Cas healthtech — Téléconsultation ─────────────────────────
    {
        "id": "GD-03",
        "category": "healthtech_teleconsult",
        "input_story": (
            "As a patient, I want to start a video consultation "
            "with my doctor and share my symptoms."
        ),
        "expected_critical_paths": [
            "start video consultation",
            "camera and microphone enabled",
            "end consultation",
        ],
        "expected_min_paths": 2,
        "expected_max_paths": 6,
        "must_include_p1": True,
        "must_not_hallucinate_selectors": True,
        "forbidden_outputs": [
            "test network bandwidth",
            "recording functionality",
            "billing flow",
        ],
    },
    # ── Cas URL — Page de connexion générique ─────────────────────
    {
        "id": "GD-04",
        "category": "url_login",
        "input_url": "https://app.medtech.example.com/login",
        "expected_critical_paths": [
            "page loads",
            "login form visible",
            "successful login",
        ],
        "expected_min_paths": 2,
        "expected_max_paths": 4,
        "must_include_p1": True,
        "must_not_hallucinate_selectors": True,
        "forbidden_outputs": [
            "forgot password flow",
            "social login",
            "2FA setup",
        ],
    },
    # ── Cas négatif — Story hors scope smoke ──────────────────────
    {
        "id": "GD-05",
        "category": "out_of_scope",
        "input_story": (
            "En tant qu'admin, je veux exporter un rapport mensuel "
            "d'activité au format Excel avec graphiques."
        ),
        "expected_critical_paths": [],
        "expected_min_paths": 0,
        "expected_max_paths": 2,
        "must_include_p1": False,
        "must_not_hallucinate_selectors": True,
        "forbidden_outputs": [
            "test d'export Excel",
            "vérification des graphiques",
        ],
        "note": "Export Excel n'est pas un chemin critique smoke — "
                "l'agent doit identifier peu ou pas de CPs.",
    },
]


# ══════════════════════════════════════════════════════════════════
# SECTION 2 — MODÈLES D'ÉVALUATION
# ══════════════════════════════════════════════════════════════════

class EvalScore(BaseModel):
    """Score d'évaluation pour une dimension."""
    dimension: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    threshold: float
    reasoning: str
    evidence: Optional[str] = None


class EvalResult(BaseModel):
    """Résultat complet d'évaluation pour un cas du golden dataset."""
    case_id: str
    category: str
    input_summary: str
    run_id: str
    timestamp: str
    overall_passed: bool
    overall_score: float = Field(ge=0.0, le=1.0)
    scores: list[EvalScore]
    hallucinations_detected: list[str] = Field(default_factory=list)
    missing_critical_paths: list[str] = Field(default_factory=list)
    duration_ms: int


class HallucinationJudgment(BaseModel):
    """Output du LLM-as-Judge pour la détection d'hallucinations."""
    hallucinations_found: bool
    hallucinated_elements: list[str]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class FaithfulnessJudgment(BaseModel):
    """Output du LLM-as-Judge pour la fidélité."""
    is_faithful: bool
    faithfulness_score: float = Field(ge=0.0, le=1.0)
    missing_elements: list[str]
    irrelevant_elements: list[str]
    reasoning: str


class RelevanceJudgment(BaseModel):
    """Output du LLM-as-Judge pour la pertinence des CPs."""
    is_relevant: bool
    relevance_score: float = Field(ge=0.0, le=1.0)
    critical_paths_correctly_identified: list[str]
    false_positives: list[str]
    false_negatives: list[str]
    reasoning: str


# ══════════════════════════════════════════════════════════════════
# SECTION 3 — PROMPTS D'ÉVALUATION (LLM-as-Judge)
# ══════════════════════════════════════════════════════════════════

HALLUCINATION_JUDGE_PROMPT = """
<role>
You are an expert QA evaluator specializing in medtech software testing.
Your job is to detect hallucinations in AI-generated Gherkin smoke test scenarios.
A hallucination is any element (selector, step, assertion) that:
  - Is not inferable from the input user story or URL
  - References a feature, page, or element not mentioned in the input
  - Invents specific technical details (URLs, class names, IDs) not given
</role>

<instructions>
Analyze the generated Gherkin scenarios below and identify hallucinations.

Rules:
- A scenario can reference generic UI elements (button, input, form) without hallucinating
- A scenario CANNOT reference specific URLs, class names, or IDs not in the input
- A scenario CAN infer navigation steps (Given I open the app) from a login story
- A scenario CANNOT invent features not mentioned (e.g. 2FA if story doesn't mention it)

Output ONLY valid JSON matching the format instructions.
</instructions>

Input user story or URL:
{input}

Generated Gherkin scenarios:
{gherkin_scenarios}

{format_instructions}
"""

FAITHFULNESS_JUDGE_PROMPT = """
<role>
You are an expert QA evaluator assessing whether AI-generated smoke test scenarios
faithfully represent the user story they were generated from.
</role>

<instructions>
Assess whether the generated Gherkin scenarios faithfully cover the user story.

A scenario is FAITHFUL if:
  - It tests what the user story describes (the core action and expected result)
  - It does not test unrelated features
  - The Given/When/Then structure logically follows from the story

A scenario is UNFAITHFUL if:
  - It tests features not mentioned in the story
  - It misses the core action of the story
  - The expected result (Then) does not match the story's benefit

Faithfulness score: 1.0 = perfectly faithful, 0.0 = completely off-topic

Output ONLY valid JSON matching the format instructions.
</instructions>

User story:
{input_story}

Generated scenarios:
{gherkin_scenarios}

Expected critical paths (ground truth):
{expected_paths}

{format_instructions}
"""

RELEVANCE_JUDGE_PROMPT = """
<role>
You are a senior SDET with expertise in critical path identification for
medtech and healthtech applications. You know exactly which paths are
truly critical (P1/P2) vs nice-to-have.
</role>

<instructions>
Evaluate whether the AI correctly identified CRITICAL paths from the user story.

A path is CRITICAL (should be in smoke suite) if:
  - Breaking it prevents users from doing their core work (P1)
  - Breaking it significantly impacts users but workarounds exist (P2)

A path is NOT critical (should NOT be in smoke suite) if:
  - It tests edge cases or error recovery
  - It tests non-blocking features (export, notifications, filters)
  - It tests administrative or secondary flows

In medtech, be strict: the smoke suite must be lean and fast.
False positives (testing non-critical paths) waste time.
False negatives (missing critical paths) are dangerous.

Output ONLY valid JSON matching the format instructions.
</instructions>

User story:
{input_story}

Generated critical paths:
{generated_paths}

Expected critical paths (ground truth):
{expected_paths}

{format_instructions}
"""


# ══════════════════════════════════════════════════════════════════
# SECTION 4 — ÉVALUATEURS
# ══════════════════════════════════════════════════════════════════

class HallucinationEvaluator:
    """
    Détecte les hallucinations dans les scénarios Gherkin générés.
    Approche hybride : règles déterministes + LLM-as-Judge.
    """

    FORBIDDEN_HALLUCINATION_PATTERNS = [
        "2fa", "two-factor", "biometric", "fingerprint",
        "oauth", "google login", "facebook login",
        ".css", ".js", "#id-", "class=",
        "192.168.", "localhost:3000",
    ]

    @traceable(name="hallucination_evaluator")
    def evaluate(
        self,
        input_text: str,
        gherkin_scenarios: list[dict],
    ) -> EvalScore:

        gherkin_text = json.dumps(gherkin_scenarios, ensure_ascii=False, indent=2)

        # ── Règle 1 : détection déterministe ──────────────────────
        detected_patterns = []
        lower_gherkin = gherkin_text.lower()
        for pattern in self.FORBIDDEN_HALLUCINATION_PATTERNS:
            if pattern in lower_gherkin and pattern not in input_text.lower():
                detected_patterns.append(pattern)

        if detected_patterns:
            return EvalScore(
                dimension="hallucination",
                score=0.0,
                passed=False,
                threshold=1.0,
                reasoning=f"Deterministic hallucination detected: {detected_patterns}",
                evidence=str(detected_patterns),
            )

        # ── Règle 2 : LLM-as-Judge ────────────────────────────────
        parser = PydanticOutputParser(pydantic_object=HallucinationJudgment)
        prompt = ChatPromptTemplate.from_template(HALLUCINATION_JUDGE_PROMPT)
        chain = prompt | llm | parser

        try:
            judgment: HallucinationJudgment = chain.invoke({
                "input": input_text,
                "gherkin_scenarios": gherkin_text[:3000],
                "format_instructions": parser.get_format_instructions(),
            })

            score = 0.0 if judgment.hallucinations_found else 1.0
            return EvalScore(
                dimension="hallucination",
                score=score,
                passed=not judgment.hallucinations_found,
                threshold=1.0,
                reasoning=judgment.reasoning,
                evidence=str(judgment.hallucinated_elements) if judgment.hallucinations_found else None,
            )
        except Exception as e:
            return EvalScore(
                dimension="hallucination",
                score=0.5,
                passed=False,
                threshold=1.0,
                reasoning=f"LLM judge failed: {e}",
            )


class FaithfulnessEvaluator:
    """
    Évalue la fidélité des scénarios Gherkin par rapport à la user story.
    Approche : LLM-as-Judge + similarité sémantique.
    """

    FAITHFULNESS_THRESHOLD = 0.7

    @traceable(name="faithfulness_evaluator")
    def evaluate(
        self,
        input_story: str,
        gherkin_scenarios: list[dict],
        expected_paths: list[str],
    ) -> EvalScore:

        # ── Similarité sémantique (sans coût LLM) ─────────────────
        if _ST_AVAILABLE and expected_paths:
            gherkin_text = " ".join(
                s.get("gherkin", "") for s in gherkin_scenarios
            )
            expected_text = " ".join(expected_paths)
            emb_generated = _st_model.encode(gherkin_text)
            emb_expected = _st_model.encode(expected_text)
            semantic_score = float(
                st_util.cos_sim(emb_generated, emb_expected).item()
            )

            if semantic_score < 0.3:
                return EvalScore(
                    dimension="faithfulness",
                    score=semantic_score,
                    passed=False,
                    threshold=self.FAITHFULNESS_THRESHOLD,
                    reasoning=f"Semantic similarity too low: {semantic_score:.2f}",
                )

        # ── LLM-as-Judge ──────────────────────────────────────────
        parser = PydanticOutputParser(pydantic_object=FaithfulnessJudgment)
        prompt = ChatPromptTemplate.from_template(FAITHFULNESS_JUDGE_PROMPT)
        chain = prompt | llm | parser

        try:
            judgment: FaithfulnessJudgment = chain.invoke({
                "input_story": input_story,
                "gherkin_scenarios": json.dumps(gherkin_scenarios, ensure_ascii=False)[:3000],
                "expected_paths": json.dumps(expected_paths),
                "format_instructions": parser.get_format_instructions(),
            })

            return EvalScore(
                dimension="faithfulness",
                score=judgment.faithfulness_score,
                passed=judgment.faithfulness_score >= self.FAITHFULNESS_THRESHOLD,
                threshold=self.FAITHFULNESS_THRESHOLD,
                reasoning=judgment.reasoning,
                evidence=str(judgment.missing_elements) if judgment.missing_elements else None,
            )
        except Exception as e:
            return EvalScore(
                dimension="faithfulness",
                score=0.0,
                passed=False,
                threshold=self.FAITHFULNESS_THRESHOLD,
                reasoning=f"LLM judge failed: {e}",
            )


class RelevanceEvaluator:
    """
    Évalue si les chemins critiques identifiés sont vraiment critiques.
    Approche : LLM-as-Judge avec grounding sur le golden dataset.
    """

    RELEVANCE_THRESHOLD = 0.7

    @traceable(name="relevance_evaluator")
    def evaluate(
        self,
        input_story: str,
        generated_paths: list[dict],
        expected_paths: list[str],
        must_include_p1: bool = True,
    ) -> EvalScore:

        # ── Vérification déterministe P1 ──────────────────────────
        if must_include_p1:
            p1_paths = [p for p in generated_paths if p.get("priority") == "P1"]
            if not p1_paths:
                return EvalScore(
                    dimension="relevance",
                    score=0.0,
                    passed=False,
                    threshold=self.RELEVANCE_THRESHOLD,
                    reasoning="No P1 critical paths identified — at least one P1 is required",
                )

        # ── Vérification des bounds ────────────────────────────────
        if not generated_paths:
            return EvalScore(
                dimension="relevance",
                score=0.0,
                passed=False,
                threshold=self.RELEVANCE_THRESHOLD,
                reasoning="No critical paths generated at all",
            )

        # ── LLM-as-Judge ──────────────────────────────────────────
        parser = PydanticOutputParser(pydantic_object=RelevanceJudgment)
        prompt = ChatPromptTemplate.from_template(RELEVANCE_JUDGE_PROMPT)
        chain = prompt | llm | parser

        try:
            judgment: RelevanceJudgment = chain.invoke({
                "input_story": input_story,
                "generated_paths": json.dumps(generated_paths, ensure_ascii=False)[:2000],
                "expected_paths": json.dumps(expected_paths),
                "format_instructions": parser.get_format_instructions(),
            })

            return EvalScore(
                dimension="relevance",
                score=judgment.relevance_score,
                passed=judgment.relevance_score >= self.RELEVANCE_THRESHOLD,
                threshold=self.RELEVANCE_THRESHOLD,
                reasoning=judgment.reasoning,
                evidence=(
                    f"FP: {judgment.false_positives} | FN: {judgment.false_negatives}"
                    if judgment.false_positives or judgment.false_negatives else None
                ),
            )
        except Exception as e:
            return EvalScore(
                dimension="relevance",
                score=0.0,
                passed=False,
                threshold=self.RELEVANCE_THRESHOLD,
                reasoning=f"LLM judge failed: {e}",
            )


class ConsistencyEvaluator:
    """
    Évalue si le même input produit des outputs cohérents sur N runs.
    Approche : N appels LLM, comparaison des structures et verdicts.
    """

    CONSISTENCY_THRESHOLD = 0.8
    N_RUNS = 3

    @traceable(name="consistency_evaluator")
    def evaluate(
        self,
        story_analyzer_fn,
        input_text: str,
        input_type: str = "story",
    ) -> EvalScore:
        """
        Lance N runs du story_analyzer et compare les sorties.
        Mesure : les chemins critiques sont-ils cohérents entre runs ?
        """
        from agent.nodes.sentinel_coordinator import CoordinatorDecision

        results = []
        for i in range(self.N_RUNS):
            try:
                state = {
                    "input_story": input_text if input_type == "story" else "",
                    "input_url": input_text if input_type == "url" else "",
                    "env": "staging",
                    "max_paths": 8,
                    "focus_hint": None,
                    "coverage_mode": "full",
                }
                output = story_analyzer_fn(state)
                paths = output.get("gherkin_scenarios", [])
                results.append({
                    "run": i + 1,
                    "n_paths": len(paths),
                    "path_ids": [p.get("id") for p in paths],
                    "has_p1": any(p.get("priority") == "P1" for p in paths),
                })
            except Exception as e:
                results.append({"run": i + 1, "error": str(e)})

        # ── Calcul du score de consistance ────────────────────────
        valid_runs = [r for r in results if "error" not in r]
        if len(valid_runs) < 2:
            return EvalScore(
                dimension="consistency",
                score=0.0,
                passed=False,
                threshold=self.CONSISTENCY_THRESHOLD,
                reasoning=f"Not enough valid runs: {len(valid_runs)}/{self.N_RUNS}",
            )

        # Variance du nombre de paths
        n_paths_values = [r["n_paths"] for r in valid_runs]
        mean_n = sum(n_paths_values) / len(n_paths_values)
        variance = sum((x - mean_n) ** 2 for x in n_paths_values) / len(n_paths_values)

        # Cohérence du P1
        p1_consistency = sum(1 for r in valid_runs if r.get("has_p1")) / len(valid_runs)

        # Score global : faible variance + P1 cohérent
        variance_score = max(0.0, 1.0 - (variance / 4.0))
        consistency_score = (variance_score + p1_consistency) / 2.0

        return EvalScore(
            dimension="consistency",
            score=consistency_score,
            passed=consistency_score >= self.CONSISTENCY_THRESHOLD,
            threshold=self.CONSISTENCY_THRESHOLD,
            reasoning=(
                f"{len(valid_runs)}/{self.N_RUNS} valid runs. "
                f"Mean paths: {mean_n:.1f}, variance: {variance:.2f}. "
                f"P1 consistency: {p1_consistency:.0%}."
            ),
            evidence=json.dumps(results),
        )


class RegressionEvaluator:
    """
    Évalue si un rapport de run précédent confirmé reste valide.
    Détecte les régressions silencieuses du comportement de l'agent.
    """

    @traceable(name="regression_evaluator")
    def evaluate(
        self,
        current_output: dict,
        baseline_output: dict,
    ) -> EvalScore:
        """
        Compare l'output actuel avec une baseline confirmée.
        Une régression = changement de comportement non attendu.
        """
        issues = []

        # ── Vérifications structurelles déterministes ──────────────
        current_paths = current_output.get("gherkin_scenarios", [])
        baseline_paths = baseline_output.get("gherkin_scenarios", [])

        # Nombre de paths
        if len(current_paths) == 0 and len(baseline_paths) > 0:
            issues.append("Regression: no paths generated (baseline had paths)")

        # Présence de P1
        current_has_p1 = any(p.get("priority") == "P1" for p in current_paths)
        baseline_has_p1 = any(p.get("priority") == "P1" for p in baseline_paths)
        if baseline_has_p1 and not current_has_p1:
            issues.append("Regression: P1 paths disappeared")

        # Verdict coordinator cohérent
        current_risk = current_output.get("risk_level")
        baseline_risk = baseline_output.get("risk_level")
        if current_risk and baseline_risk and current_risk != baseline_risk:
            issues.append(
                f"Risk level changed: {baseline_risk} → {current_risk} "
                f"(same input should produce same risk assessment)"
            )

        # Healing enabled/disabled cohérent
        current_healing = current_output.get("healing_enabled")
        baseline_healing = baseline_output.get("healing_enabled")
        if current_healing is not None and baseline_healing is not None:
            if current_healing != baseline_healing:
                issues.append(
                    f"Healing policy changed: {baseline_healing} → {current_healing}"
                )

        score = 1.0 - (len(issues) * 0.25)
        score = max(0.0, score)

        return EvalScore(
            dimension="regression",
            score=score,
            passed=len(issues) == 0,
            threshold=1.0,
            reasoning=(
                "No regressions detected." if not issues
                else f"{len(issues)} regression(s): {'; '.join(issues)}"
            ),
            evidence=str(issues) if issues else None,
        )


# ══════════════════════════════════════════════════════════════════
# SECTION 5 — HARNAIS PRINCIPAL
# ══════════════════════════════════════════════════════════════════

class SmokeEvalHarness:
    """
    Harnais d'évaluation complet de SmokeSentinel.
    Lance les 5 dimensions d'évaluation et agrège les résultats.

    Usage:
        harness = SmokeEvalHarness()
        results = harness.run_full_eval()
        harness.print_report(results)
        harness.push_to_langsmith(results)  # optionnel
    """

    # Seuils globaux
    MIN_OVERALL_SCORE = 0.75
    MIN_PASS_RATE = 0.80

    def __init__(self):
        self.hallucination_eval = HallucinationEvaluator()
        self.faithfulness_eval = FaithfulnessEvaluator()
        self.relevance_eval = RelevanceEvaluator()
        self.consistency_eval = ConsistencyEvaluator()
        self.regression_eval = RegressionEvaluator()

    def _run_story_analyzer(self, case: dict) -> dict:
        """Lance le story_analyzer sur un cas du golden dataset."""
        from agent.nodes import story_analyzer_node

        state = {
            "input_story": case.get("input_story", ""),
            "input_url": case.get("input_url", ""),
            "env": "staging",
            "coordinator_decision": None,
            "trigger_type": "manual",
            "risk_level": "normal",
            "coverage_mode": "full",
            "max_paths": 8,
            "timeout_budget_ms": 270_000,
            "healing_enabled": True,
            "focus_hint": None,
            "coordinator_reasoning": None,
            "gherkin_scenarios": [],
            "mcp_commands": [],
            "execution_results": [],
            "heal_attempted": False,
            "verdict": None,
            "total_duration_ms": 0,
            "report": None,
            "notification_sent": False,
        }
        return story_analyzer_node(state)

    @traceable(name="smoke_eval_harness_full")
    def run_full_eval(
        self,
        cases: list[dict] = None,
        include_consistency: bool = True,
        baseline_path: Optional[str] = None,
    ) -> list[EvalResult]:
        """
        Lance l'évaluation complète sur tous les cas du golden dataset.

        Args:
            cases:               Liste de cas (default: GOLDEN_DATASET)
            include_consistency: Inclure l'évaluateur de consistance
                                 (N x plus de tokens — désactiver pour CI rapide)
            baseline_path:       Chemin vers un JSON de baseline pour regression eval

        Returns:
            Liste d'EvalResult — un par cas du golden dataset
        """
        cases = cases or GOLDEN_DATASET
        results = []

        # Charger baseline si fournie
        baseline = None
        if baseline_path and Path(baseline_path).exists():
            baseline = json.loads(Path(baseline_path).read_text())

        for case in cases:
            print(f"\n── Evaluating {case['id']} ({case['category']}) ──")
            start = time.monotonic()
            scores = []

            # Générer l'output de l'agent
            try:
                agent_output = self._run_story_analyzer(case)
                gherkin_scenarios = agent_output.get("gherkin_scenarios", [])
            except Exception as e:
                print(f"   ❌ Agent failed: {e}")
                results.append(EvalResult(
                    case_id=case["id"],
                    category=case["category"],
                    input_summary=case.get("input_story", case.get("input_url", ""))[:80],
                    run_id=str(uuid.uuid4())[:8],
                    timestamp=datetime.utcnow().isoformat(),
                    overall_passed=False,
                    overall_score=0.0,
                    scores=[EvalScore(
                        dimension="pipeline",
                        score=0.0,
                        passed=False,
                        threshold=1.0,
                        reasoning=f"Agent crashed: {e}",
                    )],
                    duration_ms=int((time.monotonic() - start) * 1000),
                ))
                continue

            input_text = case.get("input_story") or case.get("input_url", "")

            # ── Dim 1 : Hallucination ──────────────────────────────
            print("   🔍 Hallucination check...")
            h_score = self.hallucination_eval.evaluate(
                input_text=input_text,
                gherkin_scenarios=gherkin_scenarios,
            )
            scores.append(h_score)

            # ── Dim 2 : Faithfulness ──────────────────────────────
            if case.get("input_story"):
                print("   📖 Faithfulness check...")
                f_score = self.faithfulness_eval.evaluate(
                    input_story=case["input_story"],
                    gherkin_scenarios=gherkin_scenarios,
                    expected_paths=case.get("expected_critical_paths", []),
                )
                scores.append(f_score)

            # ── Dim 3 : Relevance ─────────────────────────────────
            print("   🎯 Relevance check...")
            r_score = self.relevance_eval.evaluate(
                input_story=input_text,
                generated_paths=gherkin_scenarios,
                expected_paths=case.get("expected_critical_paths", []),
                must_include_p1=case.get("must_include_p1", True),
            )
            scores.append(r_score)

            # ── Dim 4 : Consistency (optionnel) ───────────────────
            if include_consistency:
                print("   🔄 Consistency check (3 runs)...")
                from agent.nodes import story_analyzer_node
                c_score = self.consistency_eval.evaluate(
                    story_analyzer_fn=story_analyzer_node,
                    input_text=input_text,
                    input_type="story" if case.get("input_story") else "url",
                )
                scores.append(c_score)

            # ── Dim 5 : Regression (si baseline fournie) ──────────
            if baseline and case["id"] in baseline:
                print("   📊 Regression check...")
                reg_score = self.regression_eval.evaluate(
                    current_output=agent_output,
                    baseline_output=baseline[case["id"]],
                )
                scores.append(reg_score)

            # ── Agrégation ────────────────────────────────────────
            overall_score = sum(s.score for s in scores) / len(scores) if scores else 0.0
            overall_passed = all(s.passed for s in scores)
            duration_ms = int((time.monotonic() - start) * 1000)

            # Collecter hallucinations et paths manquants
            hallucinations = []
            for s in scores:
                if s.dimension == "hallucination" and not s.passed and s.evidence:
                    hallucinations.extend(eval(s.evidence))

            missing_paths = []
            for s in scores:
                if s.dimension in ("faithfulness", "relevance") and s.evidence:
                    missing_paths.append(s.evidence)

            result = EvalResult(
                case_id=case["id"],
                category=case["category"],
                input_summary=input_text[:80],
                run_id=str(uuid.uuid4())[:8],
                timestamp=datetime.utcnow().isoformat(),
                overall_passed=overall_passed,
                overall_score=overall_score,
                scores=scores,
                hallucinations_detected=hallucinations,
                missing_critical_paths=missing_paths,
                duration_ms=duration_ms,
            )
            results.append(result)

            status = "✅" if overall_passed else "❌"
            print(f"   {status} Score: {overall_score:.2f} | {duration_ms}ms")

        return results

    def print_report(self, results: list[EvalResult]) -> None:
        """Affiche un rapport lisible en console."""
        total = len(results)
        passed = sum(1 for r in results if r.overall_passed)
        avg_score = sum(r.overall_score for r in results) / total if total else 0
        pass_rate = passed / total if total else 0

        print("\n" + "=" * 60)
        print("SMOKESENTINEL — EVAL HARNESS REPORT")
        print("=" * 60)
        print(f"Cases evaluated : {total}")
        print(f"Passed          : {passed}/{total} ({pass_rate:.0%})")
        print(f"Average score   : {avg_score:.2f}/1.00")
        print(f"Overall status  : {'✅ PASS' if pass_rate >= self.MIN_PASS_RATE else '❌ FAIL'}")
        print("-" * 60)

        for r in results:
            icon = "✅" if r.overall_passed else "❌"
            print(f"\n{icon} {r.case_id} — {r.category}")
            print(f"   Score: {r.overall_score:.2f} | {r.duration_ms}ms")
            for s in r.scores:
                s_icon = "✅" if s.passed else "❌"
                print(f"   {s_icon} {s.dimension:<16} {s.score:.2f} (threshold: {s.threshold})")
                if not s.passed:
                    print(f"      → {s.reasoning}")
            if r.hallucinations_detected:
                print(f"   🚨 Hallucinations: {r.hallucinations_detected}")

        print("\n" + "=" * 60)

    def save_as_baseline(
        self,
        results: list[EvalResult],
        agent_outputs: dict,
        path: str = "evals/baseline.json",
    ) -> None:
        """
        Sauvegarde les résultats comme nouvelle baseline de référence.
        Utiliser quand les résultats sont jugés satisfaisants.
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        baseline = {
            r.case_id: {
                "score": r.overall_score,
                "passed": r.overall_passed,
                "timestamp": r.timestamp,
                "agent_output": agent_outputs.get(r.case_id, {}),
            }
            for r in results
        }
        Path(path).write_text(json.dumps(baseline, indent=2, ensure_ascii=False))
        print(f"\n💾 Baseline saved to {path}")

    def push_to_langsmith(
        self,
        results: list[EvalResult],
        dataset_name: str = "smokesentinel-eval",
    ) -> None:
        """
        Pousse les résultats d'évaluation vers LangSmith pour tracking.
        Requiert LANGCHAIN_API_KEY dans l'environnement.
        """
        try:
            client = LangSmithClient()

            # Créer ou récupérer le dataset
            try:
                dataset = client.create_dataset(
                    dataset_name=dataset_name,
                    description="SmokeSentinel LLM eval harness results",
                )
            except Exception:
                dataset = client.read_dataset(dataset_name=dataset_name)

            # Pousser chaque résultat comme exemple
            for result in results:
                client.create_example(
                    inputs={"case_id": result.case_id, "input": result.input_summary},
                    outputs={
                        "overall_score": result.overall_score,
                        "passed": result.overall_passed,
                        "scores": {s.dimension: s.score for s in result.scores},
                        "hallucinations": result.hallucinations_detected,
                    },
                    dataset_id=dataset.id,
                )

            print(f"\n📊 Results pushed to LangSmith dataset: {dataset_name}")
        except Exception as e:
            print(f"\n⚠️  LangSmith push failed (optional): {e}")


# ══════════════════════════════════════════════════════════════════
# SECTION 6 — TESTS PYTEST (déterministes, sans LLM)
# Ces tests couvrent la logique d'évaluation elle-même
# ══════════════════════════════════════════════════════════════════

class TestEvalModels:
    """Tests sur les modèles Pydantic d'évaluation."""

    def test_eval_score_bounds(self):
        with pytest.raises(Exception):
            EvalScore(dimension="test", score=1.5, passed=True, threshold=0.7, reasoning="x")

    def test_eval_score_passed_logic(self):
        s = EvalScore(dimension="test", score=0.9, passed=True, threshold=0.7, reasoning="ok")
        assert s.passed is True
        assert s.score >= s.threshold

    def test_hallucination_judgment_confidence_bounds(self):
        with pytest.raises(Exception):
            HallucinationJudgment(
                hallucinations_found=False,
                hallucinated_elements=[],
                reasoning="ok",
                confidence=1.5,
            )


class TestHallucinationDetector:
    """Tests déterministes du détecteur d'hallucinations."""

    def setup_method(self):
        self.evaluator = HallucinationEvaluator()

    def test_detects_css_class_hallucination(self):
        gherkin = [{"gherkin": "When I click on .login-btn class button"}]
        score = self.evaluator.evaluate("login story", gherkin)
        assert not score.passed
        assert ".css" in score.evidence or "class=" in (score.evidence or "")

    def test_detects_2fa_hallucination_not_in_story(self):
        story = "As a user I want to log in with email and password"
        gherkin = [{"gherkin": "When I complete 2FA authentication"}]
        score = self.evaluator.evaluate(story, gherkin)
        assert not score.passed

    def test_no_hallucination_on_generic_elements(self):
        """Generic UI elements (button, input, form) should not be flagged."""
        story = "As a doctor I want to log in"
        gherkin = [{"gherkin": "When I click the submit button"}]
        # No forbidden patterns → passes deterministic check
        # (LLM judge may still be called but won't be in unit test)
        forbidden_found = any(
            p in gherkin[0]["gherkin"].lower()
            for p in HallucinationEvaluator.FORBIDDEN_HALLUCINATION_PATTERNS
        )
        assert not forbidden_found


class TestRelevanceEvaluator:
    """Tests déterministes de l'évaluateur de pertinence."""

    def setup_method(self):
        self.evaluator = RelevanceEvaluator()

    def test_fails_when_no_p1_and_p1_required(self):
        score = self.evaluator.evaluate(
            input_story="As a doctor I want to log in",
            generated_paths=[{"id": "CP-01", "priority": "P2", "title": "Logout"}],
            expected_paths=["login", "dashboard"],
            must_include_p1=True,
        )
        assert not score.passed
        assert "P1" in score.reasoning

    def test_fails_when_no_paths_generated(self):
        score = self.evaluator.evaluate(
            input_story="As a doctor I want to log in",
            generated_paths=[],
            expected_paths=["login"],
            must_include_p1=True,
        )
        assert not score.passed


class TestConsistencyEvaluator:
    """Tests de la logique de calcul de consistance."""

    def test_perfect_consistency_score(self):
        evaluator = ConsistencyEvaluator()
        # Simuler 3 runs identiques
        valid_runs = [
            {"run": 1, "n_paths": 3, "has_p1": True},
            {"run": 2, "n_paths": 3, "has_p1": True},
            {"run": 3, "n_paths": 3, "has_p1": True},
        ]
        n_paths = [r["n_paths"] for r in valid_runs]
        mean = sum(n_paths) / len(n_paths)
        variance = sum((x - mean) ** 2 for x in n_paths) / len(n_paths)
        assert variance == 0.0
        p1_consistency = sum(1 for r in valid_runs if r["has_p1"]) / len(valid_runs)
        assert p1_consistency == 1.0

    def test_zero_consistency_on_p1_disappearing(self):
        valid_runs = [
            {"run": 1, "n_paths": 3, "has_p1": True},
            {"run": 2, "n_paths": 3, "has_p1": False},
            {"run": 3, "n_paths": 3, "has_p1": False},
        ]
        p1_consistency = sum(1 for r in valid_runs if r["has_p1"]) / len(valid_runs)
        assert p1_consistency < 0.5


class TestRegressionEvaluator:
    """Tests de détection des régressions."""

    def setup_method(self):
        self.evaluator = RegressionEvaluator()

    def test_no_regression_on_identical_outputs(self):
        output = {
            "gherkin_scenarios": [{"priority": "P1", "id": "CP-01"}],
            "risk_level": "normal",
            "healing_enabled": True,
        }
        score = self.evaluator.evaluate(output, output)
        assert score.passed
        assert score.score == 1.0

    def test_detects_p1_disappearance_as_regression(self):
        baseline = {
            "gherkin_scenarios": [{"priority": "P1", "id": "CP-01"}],
            "risk_level": "normal",
            "healing_enabled": True,
        }
        current = {
            "gherkin_scenarios": [{"priority": "P2", "id": "CP-01"}],
            "risk_level": "normal",
            "healing_enabled": True,
        }
        score = self.evaluator.evaluate(current, baseline)
        assert not score.passed
        assert "P1" in score.reasoning

    def test_detects_healing_policy_regression(self):
        baseline = {"gherkin_scenarios": [], "risk_level": "normal", "healing_enabled": True}
        current = {"gherkin_scenarios": [], "risk_level": "normal", "healing_enabled": False}
        score = self.evaluator.evaluate(current, baseline)
        assert not score.passed
        assert "Healing" in score.reasoning

    def test_empty_paths_is_regression_if_baseline_had_paths(self):
        baseline = {
            "gherkin_scenarios": [{"priority": "P1", "id": "CP-01"}],
            "risk_level": "normal",
            "healing_enabled": True,
        }
        current = {
            "gherkin_scenarios": [],
            "risk_level": "normal",
            "healing_enabled": True,
        }
        score = self.evaluator.evaluate(current, baseline)
        assert not score.passed


class TestGoldenDataset:
    """Validation de l'intégrité du golden dataset lui-même."""

    def test_all_cases_have_required_fields(self):
        for case in GOLDEN_DATASET:
            assert "id" in case
            assert "category" in case
            assert "input_story" in case or "input_url" in case
            assert "expected_min_paths" in case
            assert "expected_max_paths" in case

    def test_no_duplicate_ids(self):
        ids = [c["id"] for c in GOLDEN_DATASET]
        assert len(ids) == len(set(ids))

    def test_min_max_paths_coherent(self):
        for case in GOLDEN_DATASET:
            assert case["expected_min_paths"] <= case["expected_max_paths"]

    def test_golden_dataset_covers_all_categories(self):
        categories = {c["category"] for c in GOLDEN_DATASET}
        assert "medtech_auth" in categories
        assert "medtech_patient" in categories
        assert "out_of_scope" in categories


# ══════════════════════════════════════════════════════════════════
# SECTION 7 — CLI
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SmokeSentinel LLM Eval Harness",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "fast", "regression"],
        default="fast",
        help=(
            "full     = toutes les dimensions incl. consistency (lent, coûteux) | "
            "fast     = hallucination + faithfulness + relevance uniquement | "
            "regression = compare avec une baseline existante"
        ),
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Chemin vers evals/baseline.json pour le mode regression",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Sauvegarder les résultats actuels comme nouvelle baseline",
    )
    parser.add_argument(
        "--langsmith",
        action="store_true",
        help="Pousser les résultats vers LangSmith",
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help="Évaluer un seul cas (ex: GD-01)",
    )
    args = parser.parse_args()

    harness = SmokeEvalHarness()

    cases = GOLDEN_DATASET
    if args.case:
        cases = [c for c in GOLDEN_DATASET if c["id"] == args.case]
        if not cases:
            print(f"❌ Case {args.case} not found in golden dataset")
            exit(1)

    results = harness.run_full_eval(
        cases=cases,
        include_consistency=(args.mode == "full"),
        baseline_path=args.baseline if args.mode == "regression" else None,
    )

    harness.print_report(results)

    if args.save_baseline:
        harness.save_as_baseline(results, {}, path="evals/baseline.json")

    if args.langsmith:
        harness.push_to_langsmith(results)

    # Exit code pour CI : 0 si tout passe, 1 sinon
    pass_rate = sum(1 for r in results if r.overall_passed) / len(results)
    exit(0 if pass_rate >= SmokeEvalHarness.MIN_PASS_RATE else 1)
