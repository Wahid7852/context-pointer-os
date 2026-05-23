from .registry import ContextRegistry, ContextObject
from .context_store import ContextStore
from .scheduler import Scheduler
from .acl import AccessControlList, Role
from .storage import StorageManager
from .memory_policy import MemoryPolicy
from .boot import CognitiveBootloader
from .dashboard import render_dashboard

class CPOS:
    """The 'Standard Distribution' Master Class. Wires everything together."""
    def __init__(self, workspace: str, token_limit: int = 5000):
        self.registry = ContextRegistry()
        self.acl = AccessControlList()
        self.storage = StorageManager(base_dir=workspace)
        self.store = ContextStore(self.registry, self.storage)
        self.scheduler = Scheduler(self.store, self.acl)
        self.policy = MemoryPolicy(self.store, token_limit=token_limit)
        self.bootloader = CognitiveBootloader(self.scheduler)
        self.kernel_key = self.registry.generate_kernel_key()

    def boot(self, script: list):
        return self.bootloader.boot(script)

    def step(self, instruction: str, agent: str = "root"):
        """Executes a single instruction and runs homeostasis (GC/Paging)."""
        self.scheduler.set_agent(agent)
        res = self.scheduler.dispatch(instruction)
        
        # Homeostasis: Run memory policy and background checks
        self.policy.enforce()
        
        return res

    def save_report(self, path: str = "cpos_dashboard.html"):
        render_dashboard(self.registry, self.store, self.scheduler.audit_log, path)
