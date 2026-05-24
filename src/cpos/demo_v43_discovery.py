import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v4.3 - Knowledge Discovery")
    print("================================================")
    
    # 1. Initialize two nodes: Node A (User) and Node B (Expert)
    workspace_a = "/tmp/cpos_disc_a"
    workspace_b = "/tmp/cpos_disc_b"
    for ws in [workspace_a, workspace_b]:
        os.makedirs(ws, exist_ok=True)
    
    node_a = CPOS(workspace=workspace_a, node_id="user-node")
    node_b = CPOS(workspace=workspace_b, node_id="expert-node")
    
    # Connect and Handshake
    node_a.node.connect(node_b.node)
    node_a.step(f">SEC:CONNECT #ctx0 !9 | addr=expert-node.local key={node_b.kernel_key}", agent="root")
    node_b.step(f">SEC:CONNECT #ctx0 !9 | addr=user-node.local key={node_a.kernel_key}", agent="root")

    # 2. Setup "Expert Knowledge" on Node B
    print("\n[Setup: Adding Expert Knowledge to Node B]")
    node_b.registry.register(ContextObject(
        id="ctx_quantum_basics", type="memory", title="Quantum Computing 101", 
        summary="Foundational principles of quantum bits and gates.", 
        data="Superposition and Entanglement are core concepts.",
        trust_score=1.0, sensitivity_level="internal"
    ))

    # 3. Node A performs a DISTRIBUTED QUERY
    print("\n[Scenario: Node A queries the network for 'quantum bits']")
    # Node A doesn't have this info locally. It asks the network.
    res = node_a.step('>MEM:QUERY #ctx0 !5 | q="quantum bits" remote=true', agent="root")
    
    print("\n--- Discovery Results on Node A ---")
    print(res['result'])

    # 4. Scenario: Autonomous Loading of discovered pointer
    print("\n[Scenario: Node A loading the discovered remote pointer]")
    # In a real swarm, the agent would parse the 'ptr_uri' from the query result
    # For this demo, we simulate loading the URI found in Node B
    remote_uri = "ptr://expert-node.local/memory/ctx_quantum_basics"
    node_a.step(f">MEM:LOAD #{remote_uri} !5", agent="root")
    
    # Verify RAM on Node A
    content_a = node_a.scheduler.get_active_content()
    print("\n--- Node A Active Context (After Discovery) ---")
    print(content_a)
    print(f"\nNode A acquired expert data? {'Superposition' in content_a}")

    # Final Report
    node_a.save_report("v43_discovery_report.html")
    print("\n[COMPLETE] CPOS v4.3 P2P Knowledge Discovery verified.")

if __name__ == "__main__":
    main()
