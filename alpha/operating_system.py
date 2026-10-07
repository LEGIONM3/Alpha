"""Alpha Tool-Augmented Cognitive Operating System: Master orchestration for Phase 2."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Core Cognitive Scaffolding (Phase 1)
from alpha.config import AlphaConfig, default_config
from alpha.core.engine import AlphaEngine
from alpha.core.model_adapter import BaseLanguageModel, MockWeakModel

# Multi-Agent Cognitive Operating System (Phase 3)
from alpha.agents import (
    AgentRuntime,
    CouncilDeliberationSystem,
    CouncilVerdict,
    CompetitiveReasoningEngine,
    CompetitiveReasoningResult,
    DynamicTeam,
    TeamManager,
    SharedKnowledgeLayer,
    SkillLibrary,
    AgentEvolutionEngine,
    MetaLearningFramework,
    CivilizationMemorySystem,
    SystemObserver,
    ImprovementReport,
    ExecutionMarketplace,
    Job,
    ChangeGovernanceSystem,
    GovernanceProposal,
    VirtualSandboxWorld,
    SimulationRun,
    AgentRole
)

# Cognitive World Model (Phase 4: Reality-Based Intelligence)
from alpha.world_model import (
    CognitiveWorldModel,
    ToolEntity,
    AgentEntity,
    ProjectEntity,
    TaskEntity,
    GoalEntity,
    DecisionEntity,
    BeliefEntity,
    RelationType,
    Evidence,
    EvidencePolarity,
    EvidenceStrength,
    SelfIntrospection,
    WorldStateSnapshot,
    CognitiveEvolutionResult
)

# Model Intelligence Layer (Phase 5: Foundation Model Amplification System)
from alpha.model_intelligence import (
    ModelIntelligenceSystem,
    AmplificationResult,
    ModelComparisonResult
)

# Research Civilization (Phase 5: Autonomous Discovery & Frontier Expansion)
from alpha.research import (
    ResearchCivilization,
    ResearchCivilizationTelemetry,
    DiscoveryCycleRecord,
    ArchitecturalProposal
)

# Universal Tool Interface & Discovery (Phase 2)
from alpha.tools.protocol import BaseTool, ToolCapability, ToolPermission, ToolResult
from alpha.tools.registry import ToolRegistry
from alpha.tools.sandbox import ToolSandbox
from alpha.tools.discovery import ToolCapabilityGraph, DiscoveredTool

# Execution Engine & Recovery
from alpha.execution.graph import ExecutionGraph, ExecutionNode
from alpha.execution.context import ExecutionContext
from alpha.execution.engine import ToolInvocationEngine, ExecutionGraphResult
from alpha.execution.recovery import RecoverySystem, FailureDetector

# Intelligence Subsystems
from alpha.filesystem.tools import (
    ReadFileTool,
    WriteFileTool,
    ListDirTool,
    FindFilesTool,
    LocateSymbolsTool,
    AnalyzeDependenciesTool,
    ProjectSummaryTool
)
from alpha.sandbox.executor import SecureExecutionSandbox
from alpha.sandbox.tools import (
    ExecuteCodeTool,
    ExecuteShellTool,
    RunUnitTestsTool
)
from alpha.verification.engine import VerificationEngine
from alpha.verification.tools import (
    VerifySchemaTool,
    VerifyArtifactTool,
    VerifyFileExistenceTool,
    VerifyOutputConsistencyTool
)
from alpha.browser.tools import (
    BrowserSearchTool,
    BrowserNavigateTool,
    BrowserExtractTool,
    BrowserSummarizeTool,
    BrowserCompareTool
)
from alpha.git.tools import (
    GitStatusTool,
    GitCloneTool,
    GitInspectCommitsTool,
    GitDiffTool,
    GitBranchAnalysisTool,
    GitReviewPullRequestTool,
    GitSummarizeTool
)
from alpha.api.tools import (
    ApiRestRequestTool,
    ApiGraphQLQueryTool,
    ApiWebhookTriggerTool,
    ApiCircuitBreakerStatusTool
)

# Memory & Reflection Integration
from alpha.memory.tool_memory import ToolMemoryStore
from alpha.reflection.tool_reflection import ToolReflectionEngine, ToolReflectionReport

# Workflow Engine & Analytics
from alpha.workflows.engine import WorkflowEngine, WorkflowExecutionResult
from alpha.workflows.templates import (
    build_research_workflow,
    build_coding_workflow,
    build_debug_workflow,
    build_analysis_workflow,
    build_validation_workflow
)
from alpha.analytics.tracker import PerformanceAnalytics

logger = logging.getLogger(__name__)

class AlphaOperatingSystem:
    """Master Tool-Augmented Cognitive Operating System for Project Alpha (Phase 2).
    
    Transforms Alpha from a reasoning framework into an acting framework using real tools.
    """

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        db_path: str = ":memory:",
        model: Optional[BaseLanguageModel] = None,
        config: Optional[AlphaConfig] = None
    ):
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else Path.cwd()
        self.db_path = db_path
        self.config = config or default_config

        # 1. Cognitive Scaffolding Core (Phase 1)
        self.cognitive_engine = AlphaEngine(
            config=self.config,
            model=model or MockWeakModel(),
            db_path=self.db_path
        )

        # 2. Universal Tool Infrastructure
        self.sandbox = ToolSandbox(default_timeout_seconds=30.0)
        self.registry = ToolRegistry(sandbox=self.sandbox)
        self.recovery = RecoverySystem(registry=self.registry)
        self.invocation_engine = ToolInvocationEngine(
            registry=self.registry,
            recovery_system=self.recovery,
            max_workers=4
        )

        # 3. Verification Engine
        self.verification = VerificationEngine()

        # 4. Analytics & Memory Stores
        self.analytics = PerformanceAnalytics(db_path=self.db_path)
        self.tool_memory = ToolMemoryStore(
            memory_manager=self.cognitive_engine.memory,
            db_path=self.db_path
        )

        # 5. Tool Discovery & Capability Graph
        self.capability_graph = ToolCapabilityGraph(registry=self.registry)

        # 6. Reflection Engine
        self.tool_reflection = ToolReflectionEngine(
            capability_graph=self.capability_graph,
            memory_manager=self.cognitive_engine.memory,
            tool_memory=self.tool_memory
        )

        # 7. Workflow Engine
        self.workflows = WorkflowEngine(
            invocation_engine=self.invocation_engine,
            reflection_engine=self.tool_reflection
        )

        # 8. Cognitive World Model (Phase 4: Reality-Based Source of Truth)
        self.world_model = CognitiveWorldModel()

        # 9. Register Standard Subsystem Tools
        self._register_default_tools()
        self.capability_graph.refresh()

        # 10. Multi-Agent Cognitive Civilization (Phase 3)
        self.agent_runtime = AgentRuntime()
        self.council = CouncilDeliberationSystem(self.agent_runtime)
        self.adversarial = CompetitiveReasoningEngine(self.agent_runtime)
        self.teams = TeamManager(self.agent_runtime)
        self.knowledge_society = SharedKnowledgeLayer()
        self.skills = SkillLibrary()
        self.evolution = AgentEvolutionEngine(self.agent_runtime)
        self.meta_learning = MetaLearningFramework(self.knowledge_society)
        self.civilization_memory = CivilizationMemorySystem()
        self.observer = SystemObserver(self.agent_runtime)
        self.marketplace = ExecutionMarketplace(self.agent_runtime)
        self.governance = ChangeGovernanceSystem()
        self.simulation = VirtualSandboxWorld()

        # 11. Model Intelligence Layer (Phase 5: Foundation Model Amplification System)
        self.model_intelligence = ModelIntelligenceSystem(
            endpoint_url="http://localhost:1234/v1",
            world_model=self.world_model,
            enable_mock_fallback=True
        )

        # 12. Research Civilization (Phase 5: Autonomous Discovery & Frontier Expansion)
        self.research_civilization = ResearchCivilization(
            world_model=self.world_model,
            change_governance=self.governance
        )

    def _register_default_tools(self) -> None:
        """Register all production tools across Filesystem, Sandbox, Verification, Browser, Git, and API."""
        ws = str(self.workspace_root)

        # Filesystem
        fs_tools = [
            ReadFileTool(ws),
            WriteFileTool(ws),
            ListDirTool(ws),
            FindFilesTool(ws),
            LocateSymbolsTool(ws),
            AnalyzeDependenciesTool(ws),
            ProjectSummaryTool(ws)
        ]
        for t in fs_tools:
            self.registry.register_tool(t)

        # Sandbox & Code Execution
        self.code_sandbox = SecureExecutionSandbox(sandbox_dir=ws)
        sand_tools = [
            ExecuteCodeTool(self.code_sandbox),
            ExecuteShellTool(self.code_sandbox),
            RunUnitTestsTool(self.code_sandbox)
        ]
        for t in sand_tools:
            self.registry.register_tool(t)

        # Verification
        val_tools = [
            VerifySchemaTool(self.verification),
            VerifyArtifactTool(self.verification),
            VerifyFileExistenceTool(self.verification),
            VerifyOutputConsistencyTool(self.verification)
        ]
        for t in val_tools:
            self.registry.register_tool(t)

        # Browser
        browser_tools = [
            BrowserSearchTool(),
            BrowserNavigateTool(),
            BrowserExtractTool(),
            BrowserSummarizeTool(),
            BrowserCompareTool()
        ]
        for t in browser_tools:
            self.registry.register_tool(t)

        # Git
        git_tools = [
            GitStatusTool(ws),
            GitCloneTool(),
            GitInspectCommitsTool(ws),
            GitDiffTool(ws),
            GitBranchAnalysisTool(ws),
            GitReviewPullRequestTool(),
            GitSummarizeTool(ws)
        ]
        for t in git_tools:
            self.registry.register_tool(t)

        # API Gateway
        api_tools = [
            ApiRestRequestTool(),
            ApiGraphQLQueryTool(),
            ApiWebhookTriggerTool(),
            ApiCircuitBreakerStatusTool()
        ]
        for t in api_tools:
            self.registry.register_tool(t)

        # Populate Discovery Metadata Store with "Why" and "When" operational rationale
        ms = self.capability_graph.metadata_store
        ms.register_metadata(
            tool_name="fs_read_file",
            why_it_exists="Provides direct disk reading capabilities for repository inspection.",
            when_to_use="When reading the specific contents of a known file path.",
            examples=["fs_read_file(file_path='alpha/config.py')"]
        )
        ms.register_metadata(
            tool_name="fs_write_file",
            why_it_exists="Enables safe filesystem mutation with automatic rollback recording.",
            when_to_use="When creating or updating code artifacts or documentation.",
            examples=["fs_write_file(file_path='src/app.py', content='...')"]
        )
        ms.register_metadata(
            tool_name="fs_locate_symbols",
            why_it_exists="AST-based symbol lookup avoids brute-force file scanning.",
            when_to_use="When locating class or function signatures across the codebase.",
            examples=["fs_locate_symbols(name_query='AlphaEngine')"]
        )
        ms.register_metadata(
            tool_name="sandbox_execute_code",
            why_it_exists="Runs arbitrary Python, NodeJS, or Rust code in an isolated subprocess.",
            when_to_use="When executing or testing generated code logic before persistence.",
            examples=["sandbox_execute_code(language='python', code='...')"]
        )
        ms.register_metadata(
            tool_name="verify_schema",
            why_it_exists="Ensures structured dictionary outputs satisfy contract requirements.",
            when_to_use="After generating API or data specifications.",
            examples=["verify_schema(data=..., required_fields=['status'])"]
        )
        ms.register_metadata(
            tool_name="browser_search",
            why_it_exists="Provides external and simulated web search with source ranking.",
            when_to_use="When researching unfamiliar libraries, APIs, or architectural patterns.",
            examples=["browser_search(query='python concurrency')"]
        )
        ms.register_metadata(
            tool_name="git_diff",
            why_it_exists="Generates unified diffs to review changes before committing.",
            when_to_use="After code modifications to verify changes.",
            examples=["git_diff()"]
        )

        # Register all tools into the Universal World Model ontology & graph
        for tool_name, tool_obj in self.registry._tools.items():
            self.world_model.register_entity(
                ToolEntity(
                    id=f"tool_{tool_name}",
                    name=tool_name,
                    tool_name=tool_name,
                    sandbox_level="subprocess",
                    importance=0.75,
                    confidence=1.0,
                    attributes={"description": getattr(tool_obj, "description", "")}
                )
            )

    def execute_graph(
        self,
        graph: ExecutionGraph,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionGraphResult:
        """Execute a custom tool execution graph, tracking analytics and reflection."""
        ctx = context or ExecutionContext()
        result = self.invocation_engine.execute_graph(graph, ctx)

        # Reflect & record analytics for all nodes
        for nid, node in graph.nodes.items():
            if node.result:
                ref_report = self.tool_reflection.reflect_on_tool_execution(
                    tool_name=node.tool_name,
                    inputs=node.arguments,
                    result=node.result,
                    task_intent=graph.name
                )
                self.analytics.record_event(
                    tool_name=node.tool_name,
                    success=node.result.success,
                    latency_ms=node.result.latency_ms,
                    retries=node.retry_count,
                    reward=1.0 if node.result.success else -0.5,
                    error_type=node.result.error
                )

        return result

    def run_research_workflow(self, topic: str, num_sources: int = 3) -> WorkflowExecutionResult:
        graph = build_research_workflow(topic, num_sources=num_sources)
        return self.workflows.execute_workflow(graph)

    def run_coding_workflow(
        self,
        goal: str,
        target_file: str,
        code_content: str,
        test_file: str,
        test_content: str
    ) -> WorkflowExecutionResult:
        graph = build_coding_workflow(goal, target_file, code_content, test_file, test_content)
        return self.workflows.execute_workflow(graph)

    def run_debug_workflow(
        self,
        buggy_file: str,
        function_name: str,
        patched_file_content: str,
        test_verification_code: str
    ) -> WorkflowExecutionResult:
        graph = build_debug_workflow(buggy_file, function_name, patched_file_content, test_verification_code)
        return self.workflows.execute_workflow(graph)

    def run_analysis_workflow(self, repo_path: str = "") -> WorkflowExecutionResult:
        graph = build_analysis_workflow(repo_path)
        return self.workflows.execute_workflow(graph)

    def run_validation_workflow(
        self,
        data_dict: Dict[str, Any],
        file_to_check: str,
        required_keys: List[str]
    ) -> WorkflowExecutionResult:
        graph = build_validation_workflow(data_dict, file_to_check, required_keys)
        return self.workflows.execute_workflow(graph)

    # -------------------------------------------------------------------------
    # Phase 3 Multi-Agent Cognitive Civilization Interfaces
    # -------------------------------------------------------------------------

    def deliberate(self, question: str, context: Optional[Dict[str, Any]] = None) -> CouncilVerdict:
        """Run multi-agent deliberation council across research, planning, critique, and validation."""
        verdict = self.council.deliberate(question, context=context)
        # Epistemic Grounding: Record council consensus as a verified belief in the Cognitive World Model
        ev = self.world_model.record_evidence(
            statement=f"Council deliberated on: {question}",
            polarity=EvidencePolarity.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            source_id="council_deliberation"
        )
        self.world_model.form_belief(
            statement=f"Consensus on '{question}': {verdict.rationale}",
            initial_confidence=verdict.confidence_score,
            evidence_ids=[ev.evidence_id],
            domain="deliberation"
        )
        return verdict

    def run_adversarial_hardening(
        self,
        target_solution: Dict[str, Any],
        num_rounds: int = 2
    ) -> CompetitiveReasoningResult:
        """Run Red Team vs Blue Team adversarial reasoning rounds to stress-test and harden a solution."""
        return self.adversarial.execute_adversarial_session(target_solution, num_rounds=num_rounds)

    def form_coding_team(self, task_name: str, mission_goal: str) -> DynamicTeam:
        """Form a dynamic collaborative project team across Director, Architect, Planner, Coder, Tester, and Validator."""
        team = self.teams.form_coding_team(task_name=task_name, mission_goal=mission_goal)
        # Register project entity and member relationships in the World Model
        proj = ProjectEntity(
            id=f"proj_{team.team_id[:8]}",
            name=f"Project_{task_name}",
            status="active",
            importance=0.85,
            confidence=0.95,
            attributes={"mission_goal": mission_goal, "team_id": team.team_id}
        )
        self.world_model.register_entity(proj)
        for member in team.members:
            self.world_model.relate(member.agent_id, proj.id, RelationType.BELONGS_TO)
        return team

    def run_marketplace_job(
        self,
        title: str,
        payload: Dict[str, Any],
        required_role: Optional[AgentRole] = None,
        budget_credits: float = 100.0
    ) -> Dict[str, Any]:
        """Post a job, auction it via bidding to available agents, and execute with economic settlement."""
        job = self.marketplace.post_job(
            title=title,
            payload=payload,
            required_role=required_role,
            budget_credits=budget_credits
        )
        # Register task in the World Model
        task_entity = TaskEntity(
            id=job.job_id,
            name=f"Task_{title}",
            status="in_progress",
            priority="normal",
            importance=0.75,
            confidence=0.9
        )
        self.world_model.register_entity(task_entity)
        exec_result = self.marketplace.auction_and_execute(job.job_id)
        task_entity.status = "completed" if exec_result.get("status") == "success" else "failed"
        self.world_model.ontology.update(task_entity)
        return exec_result

    def observe_society(self) -> ImprovementReport:
        """Run the System Observer to collect telemetry percentiles, detect bottlenecks, and output improvement reports."""
        return self.observer.generate_improvement_report()

    # -------------------------------------------------------------------------
    # Phase 4 Cognitive World Model Interfaces
    # -------------------------------------------------------------------------

    def introspect_reality(self) -> SelfIntrospection:
        """Introspect Alpha's self model answering the 10 fundamental existential questions."""
        return self.world_model.introspect_self()

    def get_world_state(self) -> WorldStateSnapshot:
        """Capture the live, verified multi-temporal world state across all 12 cognitive dimensions."""
        return self.world_model.capture_world_state()

    def query_what_is_true(self, min_confidence: float = 0.70) -> List[Dict[str, Any]]:
        """Query epistemologically grounded active beliefs."""
        return self.world_model.what_is_true(min_confidence=min_confidence)

    def process_observation(self, raw_data: Dict[str, Any]) -> CognitiveEvolutionResult:
        """Evolve a raw sensory observation through the 8-stage transformation pipeline."""
        return self.world_model.process_observation_to_understanding(raw_data)

    # -------------------------------------------------------------------------
    # Phase 5 Model Intelligence Interfaces
    # -------------------------------------------------------------------------

    def amplify_model_execution(
        self,
        task_query: str,
        domain: str = "reasoning"
    ) -> AmplificationResult:
        """Execute task through full 7-step Cognitive Amplification Engine."""
        return self.model_intelligence.amplify_task(task_query=task_query, domain=domain)

    def orchestrate_model_task(
        self,
        task_query: str,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Self-adaptive end-to-end task execution choosing model, context, strategy, and prompt."""
        return self.model_intelligence.orchestrate(task_query=task_query, domain=domain)

    def profile_foundation_model(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Benchmark and profile active foundation model across 10 empirical metrics."""
        return self.model_intelligence.profile_active_model(model_name=model_name)

    def compare_foundation_models(self) -> ModelComparisonResult:
        """Benchmark local model against industry architectures (Qwen, DeepSeek, Llama, Gemma, GPT-OSS)."""
        return self.model_intelligence.compare_models()

    # -------------------------------------------------------------------------
    # Phase 5 Research Civilization Interfaces (Autonomous Discovery)
    # -------------------------------------------------------------------------

    def discover_research_frontier(self, domain: str = "software", count: int = 3) -> List[Any]:
        """Proactively detects unknowns and formulates prioritized testable questions."""
        return self.research_civilization.discover_questions(domain=domain, count=count)

    def run_autonomous_discovery_cycle(self, domain: Optional[str] = None) -> DiscoveryCycleRecord:
        """Run single closed-loop scientific discovery cycle: Question -> Hypothesis -> Experiment -> Evidence -> Theory -> Publication -> New Questions."""
        return self.research_civilization.discovery_loop.run_cycle(domain=domain)

    def run_autonomous_research_mission(
        self,
        num_cycles: int = 5,
        domains: Optional[List[str]] = None
    ) -> List[DiscoveryCycleRecord]:
        """Final autonomous test: Remove user tasks; continuously discover and advance knowledge frontier."""
        return self.research_civilization.run_autonomous_discovery_mode(num_cycles=num_cycles, domains=domains)

    def self_research_architecture(self, thrust: str = "NEW_ARCHITECTURE") -> ArchitecturalProposal:
        """Alpha researches future Alpha architectures and capabilities within governed boundaries."""
        return self.research_civilization.self_research(thrust=thrust)

    def get_research_telemetry(self) -> ResearchCivilizationTelemetry:
        """Capture comprehensive telemetry across all research graph entities and frontier metrics."""
        return self.research_civilization.get_civilization_telemetry()



