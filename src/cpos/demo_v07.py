import os
import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role
from cpos.storage import StorageManager

def v07_demo():
    print("--- Context Pointer OS Kernel v0.7: Expansion Bus & Secure I/O ---")
    
    # 1. Setup
    workspace = "/tmp/cpos_v07"
    os.makedirs(workspace, exist_ok=True)
    with open(os.path.join(workspace, "hello.txt"), "w") as f:
        f.write("Hello from external device!")

    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx7", type="neurostate", title="NeuroState", content_ref="", summary="State", tokens_estimate=100, data='{"calm": 0.5}'))
    
    acl = AccessControlList()
    acl.set_role("root-agent", Role.ROOT)
    acl.set_role("guest-agent", Role.GUEST)
    
    storage = StorageManager(base_dir=workspace)
    store = ContextStore(registry, storage)
    scheduler = Scheduler(store, acl)

    # 2. Test Device Driver (Mounting)
    print("\n[V0.7: Device Driver - Mounting /tmp as 'tmp://']")
    scheduler.set_agent("root-agent")
    scheduler.dispatch(f">MEM:DEV #ctx0 !9 | mount=tmp path={workspace}")
    
    # Register and Load from mount
    registry.register(ContextObject(id="ctx100", type="file", title="External File", content_ref="tmp://hello.txt", summary="External content", tokens_estimate=100))
    scheduler.dispatch(">MEM:LOAD #ctx100 !5")
    print(f"Loaded from Device: {registry.get('ctx100').data}")

    # 3. Test Syscall
    print("\n[V0.7: System Call - listdir]")
    res_sys = scheduler.dispatch(">MEM:SYS #ctx0 !9 | func=listdir")
    print(f"Syscall Result: {res_sys['result']}")

    # 4. Test Memory Redaction (Secure I/O)
    print("\n[V0.7: Secure I/O - Memory Redaction for GUEST]")
    scheduler.dispatch(">MEM:LOAD #ctx7 !5")
    
    # As Root
    scheduler.set_agent("root-agent")
    print(f"Root View:\n{scheduler.get_active_content()}")
    
    # As Guest
    scheduler.set_agent("guest-agent")
    # Grant guest access to ctx7 first (ACL check)
    acl.grant("guest-agent", "ctx7")
    print(f"\nGuest View (Redacted):\n{scheduler.get_active_content()}")

if __name__ == "__main__":
    v07_demo()
