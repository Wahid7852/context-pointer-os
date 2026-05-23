from enum import Enum
from typing import List, Literal, Dict, Optional
from pydantic import BaseModel
from .registry import ContextObject, ContextRegistry
from .context_store import ContextStore

class CognitiveMode(str, Enum):
    NORMAL = "normal"           # On-demand
    PREDICTIVE = "predictive"   # Task-aware prefetch
    AUTONOMOUS = "autonomous"   # Self-healing / re-validation

class RetrievalPolicy(BaseModel):
    """Retrieval Governance Policy as defined in Spec v0.1 Section 9."""
    allowed_context_types: List[str] = ["project_memory", "code", "spec", "neurostate", "persona", "pointer_exchange", "message"]
    blocked_context_types: List[str] = ["private_credentials", "restricted_intel"]
    max_retrieval_depth: int = 2
    minimum_trust_score: float = 0.5
    requires_human_approval: bool = False
    audit_required: bool = True
    # Control sensitivity redaction behavior
    max_sensitivity_allowed: Literal["public", "internal", "private", "restricted"] = "internal"
    # [CPOS v0.5] Global Cognitive Mode
    mode: CognitiveMode = CognitiveMode.NORMAL

class MemoryPolicy:
    """The 'Homeostasis Layer'. Manages importance, freshness, and forgetting."""
    def __init__(self, store: ContextStore, token_limit: int = 5000):
        self.store = store
        self.registry = store.registry
        self.token_limit = token_limit

    def evaluate_forgetting(self):
        """Identifies low-importance/old/cold contexts to unload or compress."""
        active = list(self.store.active_contexts.values())
        total_tokens = sum(obj.tokens_estimate for obj in active)
        
        if total_tokens <= self.token_limit:
            return []

        # Sort by composite score: 
        # (importance * 0.4) + (access_heat * 0.4) + (freshness * 0.2)
        # Lowest score first for removal
        active.sort(key=lambda x: (x.importance * 0.4) + (x.access_heat * 0.4) + (x.freshness * 0.2))
        
        to_unload = []
        reduction = 0
        for obj in active:
            if total_tokens - reduction > self.token_limit:
                to_unload.append(obj.id)
                reduction += obj.tokens_estimate
            else:
                break
                
        return to_unload

    def enforce(self):
        targets = self.evaluate_forgetting()
        for ctx_id in targets:
            obj = self.registry.get(ctx_id)
            if not obj: continue
            
            if obj.importance > 0.6:
                # 1. Cognitive Swap (Full Disk Serialization)
                if self.store.storage and obj.data:
                    swap_ref = f"swap://{obj.id}"
                    self.store.storage.write(swap_ref, str(obj.data))
                    obj.swap_ref = swap_ref
                    obj.state.paged = True
                    obj.data = f"[PAGED TO DISK] {obj.summary}"
                    print(f"Swap-Out: {ctx_id} serialized to .swap")
                else:
                    # Fallback to Summary-only if no storage
                    self.store.load_summary(ctx_id)
            else:
                self.store.unload(ctx_id)
        return targets
