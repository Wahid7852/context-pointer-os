from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class ContextState(BaseModel):
    loaded: bool = False
    cached: bool = True
    dirty: bool = False
    paged: bool = False # New: On-disk swap state

class ContextObject(BaseModel):
    id: str
    type: str
    title: str
    content_ref: str
    summary: str
    tokens_estimate: int
    importance: float = 0.5
    freshness: float = 1.0
    access_heat: float = 0.0
    owner_pid: Optional[int] = None # New: Process ownership
    locked_by: Optional[int] = None # New: Mutex lock
    swap_ref: Optional[str] = None # New: Reference to .swap file
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: float = Field(default_factory=lambda: datetime.now().timestamp()) # For real-time decay
    parent: Optional[str] = None

    branches: List[str] = []
    permissions: List[str] = []
    state: ContextState = Field(default_factory=ContextState)
    data: Optional[Any] = None  # The actual content when loaded

class ContextRegistry:
    """The 'Memory Map' of the OS. Manages available context pointers and Kernel Key."""
    def __init__(self):
        self.registry: Dict[str, ContextObject] = {}
        self.kernel_key: Optional[str] = None

    def generate_kernel_key(self) -> str:
        import uuid
        self.kernel_key = str(uuid.uuid4())
        return self.kernel_key

    def verify_key(self, key: str) -> bool:
        return self.kernel_key is None or self.kernel_key == key

    def register(self, obj: ContextObject):
        self.registry[obj.id] = obj

    def save(self, file_path: str):
        with open(file_path, "w") as f:
            f.write(self.json())

    def json(self) -> str:
        return "[" + ",".join(obj.json() for obj in self.registry.values()) + "]"

    @classmethod
    def from_json(cls, json_str: str) -> 'ContextRegistry':
        import json
        data = json.loads(json_str)
        registry = cls()
        for item in data:
            obj = ContextObject(**item)
            registry.register(obj)
        return registry

    def get(self, ctx_id: str) -> Optional[ContextObject]:
        return self.registry.get(ctx_id)

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
        
        self.register(branch_obj)
        parent.branches.append(branch_id)
        return branch_obj

    def list_by_type(self, type_prefix: str) -> List[ContextObject]:
        return [obj for obj in self.registry.values() if obj.type.startswith(type_prefix)]
