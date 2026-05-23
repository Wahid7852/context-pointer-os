import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v13_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.3 - RESOURCE & SEARCH  ")
    print("================================================")
    
    workspace = "/tmp/cpos_v13"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace, token_limit=1000)
    os_kernel.acl.set_role("root", Role.ROOT)

    # 1. Cognitive Swap Test
    print("\n[V1.3: Cognitive Swap Test]")
    # Register a large context
    os_kernel.registry.register(ContextObject(
        id="ctx_big", type="archive", title="Old Massive Log", 
        content_ref="", summary="Massive log entry", 
        tokens_estimate=2000, importance=0.8, data="MASSIVE_DATA_PAYLOAD_" * 100
    ))
    
    print("Loading large context to RAM...")
    os_kernel.step(">MEM:LOAD #ctx_big !5")
    print(f"RAM Usage BEFORE Enforce: {sum(o.tokens_estimate for o in os_kernel.store.active_contexts.values())} tokens")
    
    # Trigger swap
    print("Triggering Homeostasis (Swap-Out)...")
    os_kernel.policy.enforce()
    
    big_obj = os_kernel.registry.get("ctx_big")
    print(f"ctx_big state: paged={big_obj.state.paged}, data_preview={str(big_obj.data)[:30]}...")
    
    # Reload (Swap-In)
    print("\nRe-loading ctx_big (Swap-In)...")
    os_kernel.step(">MEM:LOAD #ctx_big !5")
    print(f"ctx_big state: paged={big_obj.state.paged}, data_preview={str(big_obj.data)[:30]}...")

    # 2. Deep Search (Grep) Test
    print("\n[V1.3: Deep Search (grep) Test]")
    os_kernel.step(">MEM:UPDATE #ctx_big !5 | data=Contains secret keyword 'KAGIONEK0'")
    
    print("Searching for 'KAGIONEK0' across all memory and logs...")
    res_grep = os_kernel.step(">MEM:SYS #ctx0 !9 | func=grep q=\"KAGIONEK0\"")
    print(f"Grep Result: {res_grep['result']}")

    # 3. Kernel Journaling Check
    print("\n[V1.3: Kernel Journaling Check]")
    journal_path = os.path.join(workspace, "kernel_journal.jsonl")
    if os.path.exists(journal_path):
        with open(journal_path, "r") as f:
            lines = f.readlines()
            print(f"Journal Entries found: {len(lines)}")
            print(f"Last entry action: {json.loads(lines[-1])['action']}")
    else:
        print("Journal file not found!")

    os_kernel.save_report("v13_swap_search_report.html")
    print("\n[COMPLETE] v1.3 Demo Finished.")

if __name__ == "__main__":
    v13_demo()
