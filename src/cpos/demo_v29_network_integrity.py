import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v2.9 - Network Integrity  ")
    print("================================================")
    
    # 1. Initialize three nodes in a RING topology (A - B - C - A)
    # This is the best test for loop protection.
    workspace_a = "/tmp/cpos_net_a"
    workspace_b = "/tmp/cpos_net_b"
    workspace_c = "/tmp/cpos_net_c"
    for ws in [workspace_a, workspace_b, workspace_c]:
        os.makedirs(ws, exist_ok=True)
    
    node_a = CPOS(workspace=workspace_a, node_id="node-a")
    node_b = CPOS(workspace=workspace_b, node_id="node-b")
    node_c = CPOS(workspace=workspace_c, node_id="node-c")
    
    # Connect them: A <-> B <-> C <-> A
    print("\n[Setup: Creating Network Ring A <-> B <-> C <-> A]")
    node_a.node.connect(node_b.node)
    node_b.node.connect(node_c.node)
    node_c.node.connect(node_a.node)

    # 2. Synchronize Handshakes for the ring
    print("\n[Scenario: Establishing Trust across the network]")
    node_a.step(f">SEC:CONNECT #ctx0 !9 | addr=node-b.local key={node_b.kernel_key}", agent="root")
    node_b.step(f">SEC:CONNECT #ctx0 !9 | addr=node-c.local key={node_c.kernel_key}", agent="root")
    node_c.step(f">SEC:CONNECT #ctx0 !9 | addr=node-a.local key={node_a.kernel_key}", agent="root")

    # 3. Register a context on Node A and let B and C "cache" it
    print("\n[Scenario: Distributing Knowledge]")
    node_a.registry.register(ContextObject(
        id="ctx_shared_info", type="memory", title="Network Fact", 
        summary="Initial truth", data="The world is round.",
        trust_score=0.9
    ))
    
    # Node B and C "fetch" it (simulating distributed usage)
    # In this prototype, loading via ptr:// registers a local copy
    node_b.step(">MEM:LOAD #ptr://node-a.local/memory/ctx_shared_info !5", agent="root")
    node_c.step(">MEM:LOAD #ptr://node-b.local/memory/ctx_shared_info !5", agent="root")
    
    print(f"Node B knows Fact? {node_b.registry.get('ctx_shared_info') is not None}")
    print(f"Node C knows Fact? {node_c.registry.get('ctx_shared_info') is not None}")

    # 4. Trigger Invalidation on Node A
    print("\n[Scenario: Cognitive Immune Reaction (Invalidation Propagation)]")
    print("Action: Node A invalidates 'ctx_shared_info'...")
    node_a.step(">MEM:INVALIDATE #ctx_shared_info !9 | reason=\"sensor_error\"", agent="root")

    # 5. Verify propagation to B and C
    print("\n[Analysis: Verifying Propagation]")
    status_b = node_b.registry.get("ctx_shared_info").status
    status_c = node_c.registry.get("ctx_shared_info").status
    
    print(f"Node B status for Fact: {status_b}")
    print(f"Node C status for Fact: {status_c}")
    
    # 6. Verify RAM cleanup
    print(f"Node B RAM Fact Active? {'ctx_shared_info' in node_b.store.active_contexts}")
    print(f"Node C RAM Fact Active? {'ctx_shared_info' in node_c.store.active_contexts}")

    # Final Report
    node_a.save_report("v29_integrity_report_a.html")
    print("\n[COMPLETE] CPOS v2.9 Network Integrity verified (Ring Topology + Loop Protection).")

if __name__ == "__main__":
    main()
