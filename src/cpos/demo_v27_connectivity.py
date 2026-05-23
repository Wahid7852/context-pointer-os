import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v2.7 - Node Connectivity  ")
    print("================================================")
    
    # 1. Initialize two nodes (simulated as separate Kernel instances)
    workspace_a = "/tmp/cpos_node_a"
    workspace_b = "/tmp/cpos_node_b"
    os.makedirs(workspace_a, exist_ok=True)
    os.makedirs(workspace_b, exist_ok=True)
    
    # Node A: Security Node
    node_a = CPOS(workspace=workspace_a, node_id="sec-node", domain="local")
    # Node B: Audit Node
    node_b = CPOS(workspace=workspace_b, node_id="audit-node", domain="local")
    node_b.scheduler.retrieval_policy.allowed_context_types.append("security")
    
    # Connect them via NodeLink
    node_a.node.connect(node_b.node)

    # 2. Setup Context on Node A (Security Node)
    print("\n[Scenario: Setup Context on Node A]")
    node_a.registry.register(ContextObject(
        id="ctx_incident_42", type="security", title="Incident 42", 
        summary="Remote login attempt", data="IP: 192.168.1.100",
        trust_score=0.9, sensitivity_level="internal"
    ))

    # 3. Node B (Audit Node) loads the remote pointer from Node A
    print("\n[Scenario: Node B attempts to load without Handshake]")
    node_b.acl.grant_type("audit-agent", "security")
    remote_ptr = "ptr://sec-node.local/security/ctx_incident_42"
    res_fail = node_b.step(f">MEM:LOAD #{remote_ptr} !5", agent="audit-agent")
    print(f"Unauthorized Load Result: {res_fail['status']}")

    print("\n[Scenario: Node B performs Secure Handshake with Node A]")
    # Use Node A's kernel key for the handshake
    handshake_key = node_a.kernel_key
    node_b.step(f">SEC:CONNECT #ctx0 !9 | addr=sec-node.local key={handshake_key}", agent="root")
    
    print("\n[Scenario: Node B loads Remote Pointer after Handshake]")
    node_b.step(f">MEM:LOAD #{remote_ptr} !5", agent="audit-agent")
    
    # Check RAM on Node B
    active_b = node_b.scheduler.get_active_content()
    print("--- Node B Active Context ---")
    print(active_b)
    print(f"Node B has remote data? {'IP: 192.168.1.100' in active_b}")

    # 4. Scenario: Remote Invalidation Propagation
    print("\n[Scenario: Node A invalidates the info, propagating to Node B]")
    node_a.step(">MEM:INVALIDATE #ctx_incident_42 !9 | reason=\"false_positive\"", agent="root")
    
    # Check status on Node B
    obj_b = node_b.registry.get("ctx_incident_42")
    print(f"Node B pointer status: {obj_b.status}")
    print(f"Node B invalidation reason: {obj_b.invalidated_reason}")
    
    # Verify Node B auto-unloaded the invalidated pointer
    active_b_after = node_b.scheduler.get_active_content()
    print(f"Node B still has it in RAM? {'ctx_incident_42' in active_b_after}")

    # 5. Final Report
    node_b.save_report("v27_connectivity_report.html")
    print("\n[COMPLETE] CPOS v2.7 Distributed Connectivity verified.")

if __name__ == "__main__":
    main()
