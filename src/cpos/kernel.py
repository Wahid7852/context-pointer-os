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

# [AIT Firewall v11.0 Integration]
import sys
import os
# Adding home to path to find ait_firewall module
sys.path.append("/home/mayutama")
from ait_firewall.runtime import AITFirewallRuntime, DefenseProfile

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

        # [AIT Firewall v11.0] Omega Intelligence Shield
        # Initialize firewall with GOD_MODE by default for the kernel
        self.firewall = AITFirewallRuntime(profile=DefenseProfile.GOD_MODE)

    def boot(self, script: list):
        return self.bootloader.boot(script)

    def step(self, instruction: str, agent: str = "root", pid: int = 0):
        """Executes a single instruction and runs homeostasis (GC/Paging)."""
        # 1. AIT Firewall Input Scan (v11.0 Genetic Shield)
        # We treat instruction as untrusted if not from 'root'
        guarded_instruction = self.firewall.process_input(instruction, agent)
        
        # If firewall returned a Mirage or modified instruction, we use that
        self.scheduler.set_agent(agent, pid=pid)
        res = self.scheduler.dispatch(guarded_instruction)
        
        # [CPOS v12.0 Homeostasis] Process Cognitive Decay
        self.policy.process_decay()

        # 2. AIT Firewall Output Scan (DLP 2.0 Abyss Shield)
        # Redact any sensitive info from the result before returning to the caller
        guarded_res = self.firewall.process_output(str(res))
        
        return guarded_res

    def monitor(self):
        """[CPOS v0.7] Triggers the real-time cognitive terminal."""
        from .dashboard import print_terminal_monitor
        print_terminal_monitor(self)

    def save_report(self, output_path: str = "cpos_dashboard.html"):
        """The 'Screen Driver'. Generates the visual system report."""
        render_dashboard(self.registry, self.store, self.scheduler.audit_log, output_path)

    def sync_immunity(self):
        """[CPOS v12.0] Synchronizes evolved genetic rules with the Swarm network."""
        genes = self.firewall.sanitizer.genetic_shield.export_genes()
        if genes:
            print(f"--- [KERNEL] Broadcasting {len(genes)} genetic rules to network ---")
            self.node.broadcast_immunity(genes)

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

    def export_state(self) -> dict:
        """[CPOS v6.0] Serializes the entire cognitive state for reincarnation."""
        return {
            "registry": [obj.dict() for obj in self.registry.registry.values()],
            "history": self.scheduler.cognitive_history,
            "transition_matrix": self.scheduler.transition_matrix,
            "current_persona": self.scheduler.current_persona,
            "acl_roles": {k: int(v) for k, v in self.acl.agent_roles.items()},
            "node_id": self.node.node_id,
            "domain": self.node.domain
        }

    def restore_from_state(self, state: dict):
        """[CPOS v6.0] Restores cognitive state from a reincarnation packet."""
        # 1. Restore Registry
        for item in state.get("registry", []):
            self.registry.register(ContextObject(**item))
        
        # 2. Restore Scheduler state
        self.scheduler.cognitive_history = state.get("history", [])
        self.scheduler.transition_matrix = state.get("transition_matrix", {})
        self.scheduler.current_persona = state.get("current_persona")
        
        # 3. Restore ACL
        for agent, role_val in state.get("acl_roles", {}).items():
            self.acl.set_role(agent, Role(role_val))
            
        print(f"--- [KERNEL] Reincarnation Complete: Node restored from {state.get('node_id')} ---")
