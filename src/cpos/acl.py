from enum import IntEnum
from typing import Dict, List, Set

class Role(IntEnum):
    GUEST = 1
    USER = 2
    ROOT = 3

class AccessControlList:
    """The 'Protection Layer'. Enforces roles and permissions."""
    def __init__(self):
        # agent_name -> Role
        self.agent_roles: Dict[str, Role] = {}
        # agent_name -> set of ctx_ids they can access
        self.permissions: Dict[str, Set[str]] = {}
        # agent_name -> list of regex patterns or prefix for allowed types
        self.type_permissions: Dict[str, List[str]] = {}
        # New: Immutable flags to prevent role hijacking
        self.immutable_agents: Set[str] = {"root"}

    def set_role(self, agent: str, role: Role, is_immutable: bool = False):
        self.agent_roles[agent] = role
        if is_immutable:
            self.immutable_agents.add(agent)

    def is_immutable(self, agent: str) -> bool:
        return agent in self.immutable_agents

    def get_role(self, agent: str) -> Role:
        return self.agent_roles.get(agent, Role.GUEST)

    def grant(self, agent: str, ctx_id: str):
        if agent not in self.permissions:
            self.permissions[agent] = set()
        self.permissions[agent].add(ctx_id)

    def grant_type(self, agent: str, type_prefix: str):
        if agent not in self.type_permissions:
            self.type_permissions[agent] = []
        self.type_permissions[agent].append(type_prefix)

    def check(self, agent: str, ctx_id: str, ctx_type: str) -> bool:
        role = self.get_role(agent)
        if role == Role.ROOT or agent == "root":
            return True
            
        # Sensitive types require USER or higher
        sensitive_types = ["persona", "neurostate", "message"]
        if ctx_type in sensitive_types and role < Role.USER:
            return False
            
        # Check specific ID
        if agent in self.permissions and ctx_id in self.permissions[agent]:
            return True
            
        # Check type prefix
        if agent in self.type_permissions:
            for prefix in self.type_permissions[agent]:
                if ctx_type.startswith(prefix):
                    return True
                    
        return False
