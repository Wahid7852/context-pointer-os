from typing import List
from .registry import ContextObject, ContextRegistry
from .context_store import ContextStore

class MemoryPolicy:
    """The 'Homeostasis Layer'. Manages importance, freshness, and forgetting."""
    def __init__(self, store: ContextStore, token_limit: int = 5000):
        self.store = store
        self.registry = store.registry
        self.token_limit = token_limit

    def evaluate_forgetting(self):
        """Identifies low-importance/old contexts to unload or compress."""
        active = list(self.store.active_contexts.values())
        total_tokens = sum(obj.tokens_estimate for obj in active)
        
        if total_tokens <= self.token_limit:
            return []

        # Sort by importance (ascending) and freshness (ascending)
        # Lowest priority first
        active.sort(key=lambda x: (x.importance, x.freshness))
        
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
            if obj and obj.importance > 0.6:
                # Instead of unloading, Swap to Summary (Paging)
                print(f"Paging: Swapping {ctx_id} for Summary to save tokens")
                self.store.load_summary(ctx_id)
            else:
                self.store.unload(ctx_id)
        return targets
