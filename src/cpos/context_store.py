from typing import Dict, Optional
from .registry import ContextObject, ContextRegistry
from .storage import StorageManager

class ContextStore:
    """The 'RAM' of the OS. Manages currently loaded contexts for the LLM CPU."""
    def __init__(self, registry: ContextRegistry, storage: Optional[StorageManager] = None):
        self.registry = registry
        self.storage = storage
        self.active_contexts: Dict[str, ContextObject] = {}

    def load(self, ctx_id: str, priority: int = 5, _seen: Optional[set] = None) -> bool:
        obj = self.registry.get(ctx_id)
        if not obj:
            return False
        
        # Circular dependency protection
        if _seen is None: _seen = set()
        if ctx_id in _seen: return True
        _seen.add(ctx_id)

        # CPOS v0.1: Check pointer status
        if obj.status in ["invalidated", "deleted"]:
            print(f"Load Error: Cannot load pointer '{ctx_id}' with status '{obj.status}'.")
            if obj.replacement_pointer:
                print(f"Hint: Use replacement pointer '{obj.replacement_pointer}' instead.")
            return False

        if obj.status == "archived":
            print(f"Load Warning: Loading archived pointer '{ctx_id}'.")

        # 1. Handle Swap-In
        if obj.state.paged and self.storage and obj.swap_ref:
            content = self.storage.read(obj.swap_ref)
            if content:
                obj.data = content
                obj.state.paged = False
                print(f"Swap-In: {ctx_id} restored from .swap")

        # 2. Standard Load from storage
        # v2.0: For device types, we always reload to get fresh I/O results
        is_device = obj.type == "device" or (obj.content_ref and "://" in obj.content_ref)
        if (not obj.state.loaded or is_device) and self.storage and obj.content_ref:
            content = self.storage.read(obj.content_ref)
            if content:
                obj.data = content
                obj.state.loaded = True
        
        self.active_contexts[ctx_id] = obj

        # CPOS v0.2: Recursive Dependency Loading
        if hasattr(obj, 'dependencies') and obj.dependencies:
            for dep_id in obj.dependencies:
                # Load dependency with the same priority
                self.load(dep_id, priority=priority, _seen=_seen)

        return True

    def load_summary(self, ctx_id: str):
        obj = self.registry.get(ctx_id)
        if obj:
            obj.state.loaded = True
            obj.data = f"[SUMMARY ONLY] {obj.summary}"
            self.active_contexts[ctx_id] = obj

    def unload(self, ctx_id: str):
        if ctx_id in self.active_contexts:
            del self.active_contexts[ctx_id]

    def get_active_content(self) -> str:
        """Serializes all active contexts for the LLM prompt."""
        output = []
        for ctx_id, obj in self.active_contexts.items():
            content = f"[{ctx_id}: {obj.title}]\n{obj.summary}"
            if obj.data:
                content += f"\nRAW: {obj.data}"
            output.append(content)
        return "\n\n".join(output)
