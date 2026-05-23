import os
import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.storage import StorageManager

def v02_demo():
    print("--- Context Pointer OS Kernel v0.2 ---")
    workspace = "/tmp/cpos_v02"
    os.makedirs(workspace, exist_ok=True)
    
    # 1. Setup Disk (Storage)
    storage = StorageManager(base_dir=workspace)
    
    # Create a dummy security log on 'disk'
    log_content = "2026-05-23: XSS detected on /api/login"
    storage.write("storage://logs/security.txt", log_content)
    
    # Create initial NeuroState on 'disk'
    initial_ns = {"calm": 0.5, "openness": 0.8}
    storage.write("storage://internal/neurostate.json", json.dumps(initial_ns))

    # 2. Setup Memory Map (Registry)
    registry = ContextRegistry()
    registry.register(ContextObject(
        id="ctx4", type="security_log", title="Security Logs",
        content_ref="storage://logs/security.txt", summary="Recent XSS events",
        tokens_estimate=500
    ))
    registry.register(ContextObject(
        id="ctx7", type="neurostate", title="NeuroState",
        content_ref="storage://internal/neurostate.json", summary="Core state",
        tokens_estimate=100
    ))

    # 3. Setup RAM and Scheduler
    store = ContextStore(registry, storage)
    scheduler = Scheduler(store)

    print("\n[V0.2: Loading from Storage]")
    scheduler.dispatch(">MEM:LOAD #ctx4 !8")
    print(f"ctx4 data: {registry.get('ctx4').data}")

    print("\n[V0.2: Updating NeuroState via EAP]")
    scheduler.dispatch(">NEU:UPDATE #ctx7 !9 | calm=0.1 corruption=high")
    
    # Check updated data in RAM
    ns_obj = registry.get("ctx7")
    print(f"Updated NeuroState in RAM: {ns_obj.data}")
    print(f"Dirty flag before SYNC: {ns_obj.state.dirty}")

    print("\n[V0.2: Syncing to Disk]")
    scheduler.dispatch(">NEU:SYNC #ctx7 !9")
    print(f"Dirty flag after SYNC: {ns_obj.state.dirty}")

    print("\n[V0.2: Persisting Registry]")
    registry_path = os.path.join(workspace, "registry.json")
    registry.save(registry_path)
    print(f"Registry saved to {registry_path}")

    # 4. Verification: Reloading in a new session
    print("\n[V0.2: Recovery Test (New Session)]")
    with open(registry_path, "r") as f:
        new_registry = ContextRegistry.from_json(f.read())
    
    new_store = ContextStore(new_registry, storage)
    new_store.load("ctx7")
    print(f"Recovered NeuroState from 'Disk': {new_registry.get('ctx7').data}")

if __name__ == "__main__":
    v02_demo()
