import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def main():
    print("================================================")
    print("   CONTEXT POINTER OS - Cognitive Graph Demo    ")
    print("================================================")
    
    workspace = "/tmp/cpos_graph_demo"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)

    # 1. Setup complex relationships
    # Base Knowledge
    os_kernel.registry.register(ContextObject(
        id="ctx_base", type="memory", title="World Model", summary="Foundational knowledge", data="World is round."
    ))
    
    # Dependent Code
    os_kernel.registry.register(ContextObject(
        id="ctx_physics", type="code", title="Physics Engine", summary="Simulates gravity", 
        data="g=9.8", dependencies=["ctx_base"]
    ))

    # Speculative Branches
    os_kernel.step(">MEM:LOAD #ctx_base !5")
    os_kernel.step(">MEM:BRANCH #ctx_base !5 | hypothesis_flat")
    os_kernel.step(">MEM:BRANCH #ctx_base !5 | hypothesis_cube")
    
    # Cross-references/Dependencies in branches
    os_kernel.registry.get("ctx_base.hypothesis_flat").dependencies = ["ctx_physics"]

    # 2. Simulate activity to generate 'Heat' and audit logs
    os_kernel.step(">MEM:LOAD #ctx_physics !9")
    for _ in range(5):
        os_kernel.step(">MEM:LOAD #ctx_base.hypothesis_flat !5")

    # 3. Render the new Dashboard v3.0
    os_kernel.save_report("cpos_graph_report.html")
    print("\n[COMPLETE] Graph report rendered to cpos_graph_report.html")
    print("Open this file in a browser to see the interactive Pointer Relationship Graph.")

if __name__ == "__main__":
    main()
