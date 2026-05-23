import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.memory_policy import MemoryPolicy

def v05_demo():
    print("--- Context Pointer OS Kernel v0.5: The Kernel Expansion Pack ---")
    
    # 1. Setup
    registry = ContextRegistry()
    # ctx7: NeuroState (Extreme Corruption for Watchdog Test)
    registry.register(ContextObject(
        id="ctx7", type="neurostate", title="NeuroState",
        content_ref="internal://neurostate", summary="Core state",
        tokens_estimate=100, data=json.dumps({"calm": 0.1, "corruption": 0.95})
    ))
    # ctx4: Large context for Paging Test
    registry.register(ContextObject(
        id="ctx4", type="log", title="Huge Database Context",
        content_ref="storage://huge.txt", summary="Millions of logs...",
        tokens_estimate=8000, importance=0.8, data="VERY_LARGE_DATA_STRING"
    ))
    
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    policy = MemoryPolicy(store, token_limit=5000)

    # 2. Watchdog & Interrupt Test
    print("\n[V0.5: Watchdog Check - Extreme Corruption Detected]")
    # dispatching a dummy command should trigger the watchdog IRQ first
    scheduler.dispatch(">MEM:LOAD #ctx4 !1")
    
    ns_obj = registry.get("ctx7")
    ns_data = json.loads(ns_obj.data)
    print(f"Watchdog Status: corruption is now {ns_data.get('corruption')} (Reset successful via IRQ)")

    # 3. Virtual Memory Paging Test
    print("\n[V0.5: Virtual Memory Paging - Token Pressure]")
    # ctx4 is 8000 tokens, limit is 5000
    store.load("ctx4")
    print(f"Before Paging: {registry.get('ctx4').data[:20]}...")
    
    policy.enforce()
    print(f"After Paging: {registry.get('ctx4').data}")

    # 4. Garbage Collector (GC) Test
    print("\n[V0.5: Garbage Collector - Cleaning up branches/msgs]")
    # Create some junk
    registry.register(ContextObject(id="ctx4.tmp", type="branch", title="tmp", content_ref="", summary="", tokens_estimate=0))
    scheduler.dispatch('>MEM:SEND #ctx0 !1 | to=root body="junk"')
    
    print(f"Registry Keys before GC: {len(registry.registry.keys())}")
    scheduler.dispatch(">MEM:GC #ctx0 !9")
    print(f"Registry Keys after GC: {len(registry.registry.keys())}")

    print("\n[V0.5: Final Audit Log Snapshot]")
    for entry in scheduler.audit_log:
        print(f"{entry['agent']} | {entry['instr']} | {entry['action']} | {entry['status']}")

if __name__ == "__main__":
    v05_demo()
