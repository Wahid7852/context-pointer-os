from typing import Dict, Optional
from .registry import ContextObject, ContextRegistry
from .storage import StorageManager

class ContextStore:
    """The 'RAM' of the OS. Manages currently loaded contexts for the LLM CPU."""
    def __init__(self, registry: ContextRegistry, storage: Optional[StorageManager] = None):
        self.registry = registry
        self.storage = storage
        self.active_contexts: Dict[str, ContextObject] = {}

    def load(self, ctx_id: str, priority: int = 5) -> bool:
        obj = self.registry.get(ctx_id)
        if not obj:
            return False
        
        # Load from storage if storage manager is present
        if not obj.state.loaded and self.storage:
            content = self.storage.read(obj.content_ref)
            if content:
                obj.data = content
                obj.state.loaded = True
        
        self.active_contexts[ctx_id] = obj
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
