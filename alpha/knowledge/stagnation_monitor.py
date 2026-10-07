from typing import Dict, Any
from alpha.knowledge.metrics import novel_knowledge_scorer

# Configuration constants for stagnation detection
STAGNATION_THRESHOLD = 0.0 # Score must be zero
MAX_CYCLE_COUNT = 5 # N cycles before intervention

class CognitiveStagnationDetector:
    """
    Monitors the NovelKnowledgeScore to prevent recursive commentary loops and enforce learning.
    If learning ceases, it forces external investigation (Phase 11).
    """
    def __init__(self):
        self._cycle_counter = 0

    def check_stagnation(self) -> bool:
        """
        Returns True if the system is currently stagnating and requires intervention.
        """
        score = novel_knowledge_scorer.calculate_score()
        
        if score < STAGNATION_THRESHOLD: # Score == 0
            self._cycle_counter += 1
            print(f"[STAGNATION ALERT] Zero learning observed for {self._cycle_counter} cycles.")

            if self._cycle_counter >= MAX_CYCLE_COUNT:
                # Phase 10 Action Triggered
                return True
        else:
            # Reset counter if any positive score is registered, indicating activity
            self._cycle_counter = 0
            return False

    def trigger_intervention(self):
        """
        Called when stagnation is confirmed. This function must enforce the shift 
        to Phase 11 behavior (Force observation/research).
        """
        print("==================================================")
        print("COGNITIVE STAGNATION DETECTED: FORCING REALITY INTERFACE")
        print("System entering Autonomous Research Mode (Phase 11)")
        print("==================================================")

# A simplified standalone instance for immediate use in the cycle logic
stagnation_monitor = CognitiveStagnationDetector()