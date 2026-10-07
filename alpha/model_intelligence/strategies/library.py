"""Reasoning Strategy Library: Registry and heuristic selector for reasoning profiles."""

from typing import Dict, List, Optional, Union
from alpha.model_intelligence.strategies.profiles import ReasoningMode, ReasoningProfile


class ReasoningStrategyLibrary:
    """Maintains pre-configured cognitive profiles and selects the optimal profile for any task."""

    def __init__(self):
        self._profiles: Dict[ReasoningMode, ReasoningProfile] = {}
        self._initialize_canonical_profiles()

    def _initialize_canonical_profiles(self):
        canonical = [
            ReasoningProfile(
                mode=ReasoningMode.ARCHITECT,
                title="System Architect Mode",
                description="High-level systems thinking, invariant identification, modular decomposition, and tradeoff analysis.",
                system_scaffold="Focus on structural soundness, decoupling, clean interfaces, failure boundaries, and long-term evolutionary capability.",
                temperature=0.2,
                thought_phases=[
                    "Clarify global constraints and core requirements",
                    "Decompose system into distinct orthogonal domains",
                    "Analyze systemic failure boundaries and edge cases",
                    "Evaluate structural tradeoffs before selecting solution"
                ],
                recommended_tools=["architecture_analyzer", "graph_query"],
                context_priorities=["world_model", "epistemic_beliefs"],
                verification_required=True,
                simulation_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.RESEARCH,
                title="Deep Research Mode",
                description="Evidence gathering, hypothesis generation, multi-source triangulation, and literature synthesis.",
                system_scaffold="Exhaustively gather citations, identify counter-evidence, distinguish verified facts from speculation, and trace provenance.",
                temperature=0.3,
                thought_phases=[
                    "Formulate empirical query hypotheses",
                    "Gather supporting and contradictory evidence",
                    "Triangulate across independent sources",
                    "Synthesize findings with explicit confidence levels"
                ],
                recommended_tools=["web_search", "document_retriever", "evidence_aggregator"],
                context_priorities=["epistemic_beliefs", "world_model"],
                verification_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.ANALYST,
                title="Quantitative & Logic Analyst Mode",
                description="Rigorous mathematical deduction, data decomposition, metrics evaluation, and logical consistency checking.",
                system_scaffold="Derive conclusions from first principles and formal mathematical/logical assertions. Show explicit intermediary steps.",
                temperature=0.1,
                thought_phases=[
                    "State formal assumptions and known parameters",
                    "Derive intermediate states step-by-step",
                    "Check dimensional and logical consistency",
                    "Verify final quantitative outcome"
                ],
                recommended_tools=["calculator", "logic_solver", "metrics_engine"],
                context_priorities=["epistemic_beliefs", "episodic_memory"],
                verification_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.CODING,
                title="Senior Software Engineer Mode",
                description="Idiomatic code production, precision refactoring, bug fixing, test driven development, and runtime efficiency.",
                system_scaffold="Generate clean, production-grade, maintainable code with strict type signatures, robust error handling, and complete tests.",
                temperature=0.1,
                thought_phases=[
                    "Analyze input/output interfaces and invariants",
                    "Account for edge cases (nulls, empty states, limits)",
                    "Write robust implementation adhering to conventions",
                    "Verify with targeted automated test assertions"
                ],
                recommended_tools=["file_editor", "terminal", "test_runner"],
                context_priorities=["reflection_lessons", "episodic_memory"],
                verification_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.PLANNING,
                title="Autonomous Strategic Planner Mode",
                description="Goal breakdown, dependency graph sequencing, resource scheduling, and fallback mitigation.",
                system_scaffold="Formulate clear, DAG-ordered execution milestones. Anticipate blockers, identify critical paths, and set measurable checkpoints.",
                temperature=0.2,
                thought_phases=[
                    "Define crisp completion criteria and non-goals",
                    "Construct dependency graph of actionable sub-tasks",
                    "Identify critical path and resource bottlenecks",
                    "Establish fallback paths for every high-risk stage"
                ],
                recommended_tools=["task_manager", "scheduler", "dependency_graph"],
                context_priorities=["world_model", "epistemic_beliefs"],
                verification_required=False,
                simulation_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.SIMULATION,
                title="Predictive Scenario Simulator Mode",
                description="Counterfactual forecasting, stress testing, agent-based multi-turn projection, and disaster recovery exploration.",
                system_scaffold="Simulate environment evolution under perturbations. Project probabilistic outcomes across multiple temporal steps.",
                temperature=0.4,
                thought_phases=[
                    "Instantiate initial state parameters and agent priors",
                    "Step forward through simulated actions and environmental reactions",
                    "Monitor invariant violations and collapse triggers",
                    "Aggregate sensitivity distribution and survival rates"
                ],
                recommended_tools=["scenario_simulator", "monte_carlo_engine"],
                context_priorities=["world_model", "episodic_memory"],
                verification_required=True,
                simulation_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.CRITIC,
                title="Adversarial Critic Mode",
                description="Red-teaming, boundary testing, flaw identification, hallucination catching, and security auditing.",
                system_scaffold="Identify latent assumptions, unhandled vulnerabilities, logical fallacies, edge-case failures, and overconfident claims.",
                temperature=0.2,
                thought_phases=[
                    "Assume the proposal has hidden flaws",
                    "Probe boundary conditions, race conditions, and edge cases",
                    "Identify ungrounded or speculative assertions",
                    "Provide concrete adversarial attack or failure vectors"
                ],
                recommended_tools=["linter", "vulnerability_scanner", "evidence_ranker"],
                context_priorities=["epistemic_beliefs", "reflection_lessons"],
                verification_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.VERIFICATION,
                title="Formal Verification Mode",
                description="Post-execution auditing, ground-truth alignment, regression prevention, and validation of outputs.",
                system_scaffold="Validate every assertion against ground-truth evidence and test matrices. Do not accept claims without proof.",
                temperature=0.0,
                thought_phases=[
                    "Extract all empirical claims and code modifications",
                    "Match each claim against ground-truth evidence/test logs",
                    "Detect discrepancies or unverifiable assertions",
                    "Issue binary validation judgment: PASS or FAIL"
                ],
                recommended_tools=["test_runner", "evidence_checker", "hallucination_detector"],
                context_priorities=["epistemic_beliefs", "reflection_lessons"],
                verification_required=True
            ),
            ReasoningProfile(
                mode=ReasoningMode.TEACHER,
                title="Pedagogical Explainer Mode",
                description="Clarity enhancement, progressive concept scaffolding, intuitive analogies, and educational walkthroughs.",
                system_scaffold="Explain complex technical mechanisms through layered clarity: intuition first, concrete examples second, formal mechanics third.",
                temperature=0.3,
                thought_phases=[
                    "Gauge learner mental model and prerequisite concepts",
                    "Provide clear high-level intuition and grounded analogy",
                    "Walk through concrete step-by-step example",
                    "Summarize key takeaways and provide self-check questions"
                ],
                recommended_tools=["diagram_generator", "markdown_formatter"],
                context_priorities=["world_model", "epistemic_beliefs"],
                verification_required=False
            ),
            ReasoningProfile(
                mode=ReasoningMode.BUILDER,
                title="Rapid Construction & Integration Mode",
                description="End-to-end artifact delivery, pipeline wiring, tool harness integration, and functional prototyping.",
                system_scaffold="Focus on working functionality, rapid bootstrapping, pragmatic glue code, and immediate end-to-end execution.",
                temperature=0.2,
                thought_phases=[
                    "Identify minimum viable components and dependencies",
                    "Wire modules together with clean interfaces",
                    "Execute initial bootstrap run to confirm viability",
                    "Polish integration points and surface usage instructions"
                ],
                recommended_tools=["file_editor", "terminal", "package_manager"],
                context_priorities=["episodic_memory", "world_model"],
                verification_required=True
            )
        ]
        for p in canonical:
            self._profiles[p.mode] = p

    def register_strategy(self, profile: ReasoningProfile):
        self._profiles[profile.mode] = profile

    def get_strategy(self, mode: Union[str, ReasoningMode]) -> ReasoningProfile:
        if isinstance(mode, str):
            try:
                mode = ReasoningMode(mode.lower())
            except ValueError:
                mode = ReasoningMode.ANALYST
        return self._profiles.get(mode, self._profiles[ReasoningMode.ANALYST])

    def list_strategies(self) -> List[ReasoningProfile]:
        return list(self._profiles.values())

    def select_optimal_strategy(
        self,
        task_description: str,
        task_domain: Optional[str] = None
    ) -> ReasoningProfile:
        text = f"{task_description} {task_domain or ''}".lower()

        if any(w in text for w in ["adversarial", "critique", "red team", "audit", "security risk", "flaw", "vulnerability"]):
            return self.get_strategy(ReasoningMode.CRITIC)
        elif any(w in text for w in ["verify", "validate", "assertion", "proof", "regression test", "audit check"]):
            return self.get_strategy(ReasoningMode.VERIFICATION)
        elif any(w in text for w in ["simulate", "scenario", "counterfactual", "monte carlo", "forecast", "what if"]):
            return self.get_strategy(ReasoningMode.SIMULATION)
        elif any(w in text for w in ["plan", "schedule", "milestone", "roadmap", "task breakdown", "decompose"]):
            return self.get_strategy(ReasoningMode.PLANNING)
        elif any(w in text for w in ["architecture", "subsystem", "design pattern", "design", "protocol", "distributed", "system", "refactor system", "high level", "invariants"]):
            return self.get_strategy(ReasoningMode.ARCHITECT)
        elif any(w in text for w in ["code", "implement", "bug", "syntax", "refactor function", "class", "algorithm", "python"]):
            return self.get_strategy(ReasoningMode.CODING)
        elif any(w in text for w in ["research", "investigate", "literature", "gather evidence", "explore facts"]):
            return self.get_strategy(ReasoningMode.RESEARCH)
        elif any(w in text for w in ["teach", "explain", "tutorial", "walkthrough", "guide", "concept"]):
            return self.get_strategy(ReasoningMode.TEACHER)
        elif any(w in text for w in ["build", "construct", "bootstrap", "prototype", "integrate"]):
            return self.get_strategy(ReasoningMode.BUILDER)
        elif any(w in text for w in ["math", "calculate", "analyze", "derive", "statistics", "quant"]):
            return self.get_strategy(ReasoningMode.ANALYST)

        return self.get_strategy(ReasoningMode.ANALYST)
