import os
import time
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v3.2 - Real-time Terminal ")
    print("================================================")
    
    workspace = "/tmp/cpos_v32"
    os.makedirs(workspace, exist_ok=True)
    
    os_kernel = CPOS(workspace=workspace, node_id="main-brain")
    os_kernel.step(">SEC:MODE #ctx0 !9 | mode=predictive", agent="root")

    # 1. Register multiple contexts
    for i in range(1, 6):
        os_kernel.registry.register(ContextObject(
            id=f"ctx_{i}", type="memory", title=f"Knowledge Piece {i}", summary="...", data=f"Data {i}"
        ))

    # 2. Simulate activity and monitor
    print("\n[Scenario: Simulating Cognitive Activity]")
    
    # Sequential access pattern for Neural learning
    os_kernel.step(">MEM:LOAD #ctx_1 !5", agent="root")
    os_kernel.step(">MEM:LOAD #ctx_2 !5", agent="root")
    
    print("\nDisplaying Cognitive Monitor (v0.7)...")
    os_kernel.monitor()
    
    # 3. Simulate high heat
    print("\n[Scenario: High Intensity Recall]")
    for _ in range(5):
        os_kernel.step(">MEM:RAW #ctx_1 !5", agent="root")
    
    os_kernel.monitor()

    # 4. Final Snapshot with Pulse visualization
    os_kernel.save_report("v32_terminal_report.html")
    print("\n[COMPLETE] CPOS v3.2 Real-time Terminal verified.")

if __name__ == "__main__":
    main()
