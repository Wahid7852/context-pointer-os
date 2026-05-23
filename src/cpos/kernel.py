from .registry import ContextRegistry, ContextObject
from .context_store import ContextStore
from .scheduler import Scheduler
from .acl import AccessControlList, Role
from .storage import StorageManager
from .memory_policy import MemoryPolicy
from .boot import CognitiveBootloader
from .dashboard import render_dashboard
from .node_link import NodeLink

class CPOS:
    """The 'Standard Distribution' Master Class. Wires everything together."""
    def __init__(self, workspace: str, token_limit: int = 5000, node_id: str = "node", domain: str = "local"):
        self.registry = ContextRegistry()
        self.acl = AccessControlList()
        self.storage = StorageManager(base_dir=workspace)
        self.store = ContextStore(self.registry, self.storage)
        self.scheduler = Scheduler(self.store, self.acl)
        self.policy = MemoryPolicy(self.store, token_limit=token_limit)
        self.bootloader = CognitiveBootloader(self.scheduler)
        self.kernel_key = self.registry.generate_kernel_key()
        
        # [CPOS v0.4] Node Connectivity
        self.node = NodeLink(node_id, domain)
        self.node.kernel = self
        self.registry.node = self.node # Give registry access to node for invalidation broadcast
        self.store.node = self.node # Give store access to node for remote loading

    def boot(self, script: list):
        return self.bootloader.boot(script)

    def step(self, instruction: str, agent: str = "root", pid: int = 0):
        """Executes a single instruction and runs homeostasis (GC/Paging)."""
        self.scheduler.set_agent(agent, pid=pid)
        res = self.scheduler.dispatch(instruction)
        
        # Homeostasis: Run memory policy and background checks
        self.policy.enforce()
        
        return res

    def save_report(self, path: str = "cpos_dashboard.html"):
        render_dashboard(self.registry, self.store, self.scheduler.audit_log, path)

    def restore(self, snapshot_path: str):
        """Reboots the system from a disk image."""
        import json
        with open(snapshot_path, "r") as f:
            data = json.load(f)
            # Restore Registry
            self.registry.registry = {}
            for item in data["registry"]:
                obj = ContextObject(**item)
                self.registry.register(obj)
            # Restore ACL Roles
            for agent, role_val in data["acl"]["roles"].items():
                self.acl.set_role(agent, Role(role_val))
        print(f"--- [KERNEL] System restored from {snapshot_path} ---")
