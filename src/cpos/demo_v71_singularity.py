import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v7.1 - Singularity        ")
    print("================================================")
    
    workspace = "/tmp/cpos_v71"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    
    # 1. Setup system command pointer
    os_kernel.registry.register(ContextObject(
        id="ctx_cmd_ls", type="code", title="System Check", 
        summary="Linux ls command", data="ls -la /tmp",
        trust_score=1.0 # High trust required for EXEC
    ))

    # 2. Scenario: EXEC is OFF by default
    print("\n[Scenario: Attempting EXEC with default policy]")
    res_fail = os_kernel.step(">SEC:EXEC #ctx_cmd_ls !9", agent="root")
    print(f"Result: {res_fail['status']} - {res_fail['result']}")

    # 3. Scenario: Enable EXEC and test
    print("\n[Scenario: Enabling EXEC via POLICY]")
    os_kernel.step(">SEC:POLICY #ctx0 !9 | exec=true", agent="root")
    res_success = os_kernel.step(">SEC:EXEC #ctx_cmd_ls !9", agent="root")
    print(f"Result: {res_success['status']} - {res_success['result']}")

    # 4. Scenario: Neural Glitch
    print("\n[Scenario: Neural Glitch Induction]")
    # Enable glitch mode
    os_kernel.step(">SEC:POLICY #ctx0 !9 | glitch=true", agent="root")
    
    # Induce high corruption into NeuroState (ctx7)
    os_kernel.registry.register(ContextObject(
        id="ctx7", type="neurostate", title="Core Psyche", 
        summary="...", data='{"calm": 0.1, "corruption": 0.95}'
    ))
    
    print("\nMonitor output with HIGH CORRUPTION + GLITCH MODE:")
    os_kernel.monitor()

    # 5. Disable Glitch and see clean monitor
    print("\n[Scenario: Disabling GLITCH via POLICY]")
    os_kernel.step(">SEC:POLICY #ctx0 !9 | glitch=false", agent="root")
    os_kernel.monitor()

    # Final Report
    os_kernel.save_report("v71_singularity_report.html")
    print("\n[COMPLETE] CPOS v7.1 Singularity Agency verified.")

if __name__ == "__main__":
    main()
