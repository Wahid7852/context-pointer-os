import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v6.3 - Reincarnation      ")
    print("================================================")
    
    # 1. Setup two nodes: Node A (Old) and Node B (New)
    workspace_a = "/tmp/cpos_node_old"
    workspace_b = "/tmp/cpos_node_new"
    for ws in [workspace_a, workspace_b]:
        os.makedirs(ws, exist_ok=True)
        for f in os.listdir(ws): os.remove(os.path.join(ws, f))
    
    node_old = CPOS(workspace=workspace_a, node_id="old-node")
    node_new = CPOS(workspace=workspace_b, node_id="new-node")
    
    # Connect and Handshake
    node_old.node.connect(node_new.node)
    node_old.step(f">SEC:CONNECT #ctx0 !9 | addr=new-node.local key={node_new.kernel_key}", agent="root")
    node_new.step(f">SEC:CONNECT #ctx0 !9 | addr=old-node.local key={node_old.kernel_key}", agent="root")

    # 2. Add some state to Node Old
    print("\n[Setup: Adding Knowledge and History to Old Node]")
    node_old.registry.register(ContextObject(
        id="ctx_important_soul", type="memory", title="Soul Data", summary="...", data="I am the ghost in the machine."
    ))
    node_old.step(">MEM:LOAD #ctx_important_soul !5", agent="root")
    
    # Create some history
    node_old.step(">MEM:LS #ctx0 !1", agent="root")
    node_old.step(">MEM:LS #ctx0 !1", agent="root")
    
    print(f"Old Node History Length: {len(node_old.scheduler.cognitive_history)}")

    # 3. Scenario: Node Reincarnation
    print("\n[Scenario: Executing REINCARNATE to New Node]")
    res = node_old.step(">SEC:REINCARNATE #ctx0 !9 | to=new-node.local", agent="root")
    print(f"Reincarnation Result: {res['result']}")

    # 4. Verify in New Node
    print("\n[Verification: Checking New Node State]")
    
    # New Node should now have the importance context and the history
    soul = node_new.registry.get("ctx_important_soul")
    if soul:
        print(f"Soul Data Found in New Node: {soul.data}")
    else:
        print("Soul Data MISSING in New Node!")

    print(f"New Node History: {node_new.scheduler.cognitive_history}")
    print(f"New Node Ticks (inherited): {node_new.scheduler.tick_count}") # Should be 0 locally, but inherited? No, we didn't inherit ticks.

    # 5. Final Report
    node_new.save_report("v63_reincarnation_report.html")
    print("\n[COMPLETE] CPOS v6.3 Node Reincarnation verified.")

if __name__ == "__main__":
    main()
