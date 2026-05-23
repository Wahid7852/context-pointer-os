import os
import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.storage import StorageManager

def v03_demo():
    print("--- Context Pointer OS Kernel v0.3: Branching & Speculation ---")
    
    # 1. Setup
    registry = ContextRegistry()
    registry.register(ContextObject(
        id="ctx4", type="security_log", title="Main Log",
        content_ref="storage://logs/main.txt", summary="Original Security Log",
        tokens_estimate=500, data="SAFE"
    ))
    
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    # Load original
    scheduler.dispatch(">MEM:LOAD #ctx4 !8")
    print(f"Original Context (#ctx4): {registry.get('ctx4').data}")

    # 2. Branch for Speculation (Hypothesis A)
    print("\n[V0.3: Branching for Speculation]")
    scheduler.dispatch(">MEM:BRANCH #ctx4 !9 | hyp_a")
    
    # The branch ID will be ctx4.hyp_a
    branch_id = "ctx4.hyp_a"
    print(f"Active Memory Map: {list(store.active_contexts.keys())}")

    # 3. Modify only the branch
    print("\n[V0.3: Modifying Branch (Simulating discovery)]")
    # Using UPDATE on the branch
    res = scheduler.dispatch(f">MEM:UPDATE #{branch_id} !9 | data=INFECTED")
    print(f"Dispatch Result: {res}")
    
    print(f"Original Context (#ctx4): {registry.get('ctx4').data}")
    print(f"Branch Context ({branch_id}): {registry.get(branch_id).data}")

    # 4. Merge back to Root
    print("\n[V0.3: Merging successful branch back to Root]")
    res = scheduler.dispatch(f">MEM:MERGE #{branch_id} !9")
    print(f"Dispatch Result: {res}")
    
    print(f"Merged Root Context (#ctx4): {registry.get('ctx4').data}")
    print(f"Root Dirty Flag: {registry.get('ctx4').state.dirty}")
    print(f"Active Memory Map (Post-merge): {list(store.active_contexts.keys())}")

    # 5. Forgetting (Snapshot Cleanup)
    print("\n[V0.3: Forgetting a context]")
    scheduler.dispatch(f">MEM:FORGET #{branch_id} !1")
    print(f"Registry keys: {list(registry.registry.keys())}")

if __name__ == "__main__":
    v03_demo()
