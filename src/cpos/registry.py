from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field

class ContextState(BaseModel):
    loaded: bool = False
    cached: bool = True
    dirty: bool = False
    paged: bool = False # On-disk swap state

class ContextObject(BaseModel):
    # Core CPOS v0.1 Pointer Fields
    id: str  # alias for pointer_id
    type: str # alias for context_type
    title: str
    summary: str
    source: str = "unknown"
    location: str = "unknown"
    content_ref: Optional[str] = None # Internal implementation detail for storage
    
    # Priority & Trust
    priority: float = 0.5 # alias for importance
    trust_score: float = 0.5
    sensitivity_level: Literal["public", "internal", "private", "restricted"] = "internal"
    retrieval_rule: Optional[str] = None
    
    # Metrics & Lifecycle
    access_count: int = 0
    decay_rate: float = 0.05
    tokens_estimate: int = 0
    importance: float = 0.5 # Legacy support
    freshness: float = 1.0
    access_heat: float = 0.0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: float = Field(default_factory=lambda: datetime.now().timestamp())
    expiration: Optional[datetime] = None
    
    # Status & State
    status: Literal["active", "stale", "archived", "invalidated", "deleted"] = "active"
    invalidated_reason: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    replacement_pointer: Optional[str] = None
    
    # Ownership & Control
    owner_pid: Optional[int] = None
    locked_by: Optional[int] = None
    swap_ref: Optional[str] = None
    permissions: List[str] = []
    
    # Relationships
    parent: Optional[str] = None
    dependencies: List[str] = []
    branches: List[str] = []
    
    # Data Container
    state: ContextState = Field(default_factory=ContextState)
    data: Optional[Any] = None
    metadata: Dict[str, Any] = {}

class ContextRegistry:
    """The 'Memory Map' of the OS. Manages available context pointers and Kernel Key."""
    def __init__(self):
        self.registry: Dict[str, ContextObject] = {}
        self.kernel_key: Optional[str] = None
        self.audit_log: List[Dict[str, Any]] = []

    def generate_kernel_key(self) -> str:
        import uuid
        self.kernel_key = str(uuid.uuid4())
        return self.kernel_key

    def verify_key(self, key: str) -> bool:
        return self.kernel_key is None or self.kernel_key == key

    def register(self, obj: ContextObject):
        self.registry[obj.id] = obj

    def get(self, ctx_id: str) -> Optional[ContextObject]:
        obj = self.registry.get(ctx_id)
        if obj:
            # Auto-update access metrics
            obj.access_count += 1
            obj.last_accessed = datetime.now().timestamp()
            obj.updated_at = datetime.now()
        return obj

    def invalidate(self, ctx_id: str, reason: str, replacement: Optional[str] = None) -> bool:
        obj = self.registry.get(ctx_id)
        if not obj:
            return False
        
        obj.status = "invalidated"
        obj.invalidated_reason = reason
        obj.invalidated_at = datetime.now()
        obj.replacement_pointer = replacement
        obj.updated_at = datetime.now()
        
        self._log_event("context_invalidation", ctx_id, {"reason": reason})
        return True

    def update_trust(self, ctx_id: str, score: float, reason: str) -> bool:
        obj = self.registry.get(ctx_id)
        if not obj:
            return False
        
        obj.trust_score = max(0.0, min(1.0, score))
        obj.updated_at = datetime.now()
        
        self._log_event("trust_update", ctx_id, {"score": score, "reason": reason})
        return True

    def _log_event(self, event: str, ctx_id: str, metadata: Dict[str, Any]):
        self.audit_log.append({
            "event": event,
            "pointer_id": ctx_id,
            "timestamp": datetime.now().isoformat(),
            **metadata
        })

    def save(self, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.json())

    def json(self) -> str:
        # Use pydantic's json serialization if possible, but keep compatibility
        import json
        return json.dumps([obj.dict() for obj in self.registry.values()], default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'ContextRegistry':
        import json
        data = json.loads(json_str)
        registry = cls()
        for item in data:
            # Handle datetime strings
            if 'created_at' in item and isinstance(item['created_at'], str):
                item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in item and isinstance(item['updated_at'], str):
                item['updated_at'] = datetime.fromisoformat(item['updated_at'].replace('Z', '+00:00'))
            
            obj = ContextObject(**item)
            registry.register(obj)
        return registry

    def branch(self, parent_id: str, branch_suffix: str) -> Optional[ContextObject]:
        parent = self.get(parent_id)
        if not parent:
            return None
        
        branch_id = f"{parent_id}.{branch_suffix}"
        import copy
        branch_obj = copy.deepcopy(parent)
        branch_obj.id = branch_id
        branch_obj.parent = parent_id
        branch_obj.branches = []
        branch_obj.state.dirty = False
        branch_obj.created_at = datetime.now()
        
        self.register(branch_obj)
        parent.branches.append(branch_id)
        return branch_obj

    def list_by_type(self, type_prefix: str) -> List[ContextObject]:
        return [obj for obj in self.registry.values() if obj.type.startswith(type_prefix)]
