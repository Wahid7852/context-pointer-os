from .registry import ContextRegistry, ContextObject
from .context_store import ContextStore
from .scheduler import Scheduler
from .acl import AccessControlList, Role
from .storage import StorageManager
from .memory_policy import MemoryPolicy
from .boot import CognitiveBootloader
from .dashboard import render_dashboard
from .node_link import NodeLink
from .gateway import GatewayManager

class CPOS:
    """The 'Standard Distribution' Master Class. Wires everything together."""
    def __init__(self, workspace: str, token_limit: int = 5000, node_id: str = "node", domain: str = "local"):
        self.registry = ContextRegistry()
        self.acl = AccessControlList()
        self.storage = StorageManager(base_dir=workspace)
        self.gateways = GatewayManager() # [CPOS v0.4] Gateway Management
        self.store = ContextStore(self.registry, self.storage)
        self.store.gateways = self.gateways # Give store access to gateways
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
        return res

    def monitor(self):
        """[CPOS v0.7] Triggers the real-time cognitive terminal."""
        from .dashboard import print_terminal_monitor
        print_terminal_monitor(self)

    def save_report(self, output_path: str = "cpos_dashboard.html"):
        """The 'Screen Driver'. Generates the visual system report."""
        render_dashboard(self.registry, self.store, self.scheduler.audit_log, output_path)

    def restore(self, snapshot_path: str):
        """Restores kernel state from a JSON system image."""
        import json
        with open(snapshot_path, "r") as f:
            data = json.load(f)
            # Restore Registry
            for item in data["registry"]:
                obj = ContextObject(**item)
                self.registry.register(obj)
            # Restore ACL Roles
            for agent, role_val in data["acl"]["roles"].items():
                self.acl.set_role(agent, Role(role_val))
        print(f"--- [KERNEL] System restored from {snapshot_path} ---")
