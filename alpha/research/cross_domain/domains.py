"""Cross-Domain Framework: 9 Canonical Domains and 100+ Specialized Research Subdomains."""

from __future__ import annotations

from typing import Dict, List, Any


CANONICAL_DOMAINS = [
    "engineering",
    "software",
    "economics",
    "psychology",
    "biology",
    "physics",
    "mathematics",
    "design",
    "product_systems"
]

# Generate comprehensive registry covering 100+ research domains for massive stress testing & discovery
SUBDOMAINS_BY_PARENT: Dict[str, List[str]] = {
    "engineering": [
        "control_systems", "signal_processing", "robotics", "fault_tolerant_hardware",
        "mechatronics", "thermo_fluid_systems", "structural_resilience", "cyber_physical_systems",
        "reliability_engineering", "avionics", "nanotechnology", "embedded_systems"
    ],
    "software": [
        "distributed_systems", "compiler_optimization", "formal_methods", "database_internals",
        "asynchronous_runtimes", "virtualization", "networking_protocols", "cryptography",
        "operating_systems", "garbage_collection", "microservices_architecture", "type_systems"
    ],
    "economics": [
        "game_theory", "mechanism_design", "auction_theory", "behavioral_economics",
        "market_microstructure", "tokenomics", "information_asymmetry", "macroeconomic_feedback",
        "resource_allocation", "contract_theory", "econometrics", "incentive_alignment"
    ],
    "psychology": [
        "cognitive_load_theory", "dual_process_reasoning", "attention_economics", "heuristic_biases",
        "decision_fatigue", "mental_models", "gestalt_perception", "metacognition",
        "social_proof_dynamics", "reinforcement_learning_behavior", "habit_formation", "working_memory"
    ],
    "biology": [
        "cellular_homeostasis", "evolutionary_adaptation", "epigenetics", "allostasis",
        "metabolic_efficiency", "neural_plasticity", "immune_system_defense", "symbiosis",
        "morphogenesis", "population_genetics", "quorum_sensing", "ecological_resilience"
    ],
    "physics": [
        "thermodynamics_entropy", "statistical_mechanics", "phase_transitions", "quantum_entanglement",
        "nonlinear_dynamics", "chaos_theory", "conservation_laws", "electromagnetism",
        "renormalization_group", "fluid_dynamics", "percolation_theory", "wave_interference"
    ],
    "mathematics": [
        "category_theory", "topology", "graph_theory", "probability_theory",
        "differential_geometry", "information_theory", "combinatorics", "abstract_algebra",
        "dynamical_systems", "linear_algebra", "functional_analysis", "game_theoretic_logic"
    ],
    "design": [
        "interaction_affordances", "visual_hierarchy", "ergonomics", "cognitive_friction",
        "aesthetic_usability", "design_systems", "responsive_adaptation", "spatial_composition",
        "color_theory", "typography_readability", "inclusive_accessibility", "sensory_feedback"
    ],
    "product_systems": [
        "flywheel_effects", "retention_loops", "network_effects", "value_proposition_fit",
        "feature_cannibalization", "growth_funnels", "product_led_growth", "churn_mitigation",
        "platform_orchestration", "unit_economics", "user_journey_mapping", "market_penetration"
    ]
}


class DomainRegistry:
    """Registry maintaining all 100+ supported discovery domains."""

    def __init__(self):
        self.domains: Dict[str, Dict[str, Any]] = {}
        self._populate_all()

    def _populate_all(self):
        for parent, subdomains in SUBDOMAINS_BY_PARENT.items():
            self.domains[parent] = {
                "parent": None,
                "type": "CANONICAL",
                "subdomains": subdomains
            }
            for sub in subdomains:
                self.domains[sub] = {
                    "parent": parent,
                    "type": "SPECIALIZED",
                    "subdomains": []
                }

    def list_all_domains(self) -> List[str]:
        return list(self.domains.keys())

    def get_parent_domain(self, domain: str) -> str:
        entry = self.domains.get(domain)
        if entry and entry["parent"]:
            return entry["parent"]
        return domain

    def count_domains(self) -> int:
        return len(self.domains)
