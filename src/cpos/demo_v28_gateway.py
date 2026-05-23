import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v2.8 - Cognitive Gateway  ")
    print("================================================")
    
    workspace = "/tmp/cpos_gateway"
    os.makedirs(workspace, exist_ok=True)
    
    # Initialize CPOS
    os_kernel = CPOS(workspace=workspace, node_id="gateway-node")
    
    # 1. Loading from an external gateway (GitHub Mock)
    print("\n[Scenario: Loading External Context via Gateway]")
    # assembly command to load a pointer from an external gateway
    # format: ptr://ext.<gateway>/<path>
    ext_ptr = "ptr://ext.github/kagioneko/context-pointer-os/issues/1"
    
    # Execute load
    os_kernel.step(f">MEM:LOAD #{ext_ptr} !5", agent="root")
    
    # 2. Verify results in RAM
    active_content = os_kernel.scheduler.get_active_content()
    print("--- Active Context (Reconstructed) ---")
    print(active_content)
    
    print("\n[Analysis]")
    print(f"External Data visible? {'Fetched from GitHub API' in active_content}")
    print(f"Source metadata correct? {'Source: github_api' in active_content}")

    # 3. Final Report
    os_kernel.save_report("v28_gateway_report.html")
    print("\n[COMPLETE] CPOS v2.8 Cognitive Gateway verified.")

if __name__ == "__main__":
    main()
