import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v14_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.4 - SHELL & SNAPSHOT   ")
    print("================================================")
    
    workspace = "/tmp/cpos_v14"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    os_kernel.acl.set_role("root", Role.ROOT)

    # 1. Setup Initial State
    print("\n[V1.4: Initializing System State]")
    os_kernel.registry.register(ContextObject(
        id="ctx1", type="data", title="Golden Data", content_ref="", 
        summary="S", tokens_estimate=10, data="PRE-SNAPSHOT_VALUE"
    ))
    os_kernel.step(">MEM:LOAD #ctx1 !9")

    # 2. System Snapshot
    print("\n[V1.4: Creating System Snapshot (Image)]")
    res_snap = os_kernel.step(">MEM:SYS #ctx0 !9 | func=snapshot")
    print(f"Result: {res_snap['result']}")
    
    snapshot_path = res_snap["result"].split("saved to ")[1]

    # 3. State Mutation (Post-Snapshot)
    print("\n[V1.4: Mutating State after Snapshot]")
    os_kernel.step(">MEM:UPDATE #ctx1 !9 | data=POST-SNAPSHOT_CORRUPTION")
    print(f"Current Value in RAM: {os_kernel.registry.get('ctx1').data}")

    # 4. System Restore
    print("\n[V1.4: Restoring System from Snapshot...]")
    # We create a NEW kernel and restore into it
    recovery_kernel = CPOS(workspace=workspace)
    recovery_kernel.restore(snapshot_path)
    
    restored_obj = recovery_kernel.registry.get("ctx1")
    print(f"Restored Value in Registry: {restored_obj.data if restored_obj else 'None'}")
    
    if restored_obj and restored_obj.data == "PRE-SNAPSHOT_VALUE":
        print("Success: System state rolled back successfully.")
    else:
        print("Failure: Restore logic mismatch.")

    # 5. Shell Demo (Automatic)
    print("\n[V1.4: Cognitive Shell Logic Execution]")
    # Simulated shell inputs
    commands = [
        ">MEM:LS #ctx0 !1",
        ">MEM:SYS #ctx0 !9 | func=listdir"
    ]
    for cmd in commands:
        print(f"shell@root> {cmd}")
        r = os_kernel.step(cmd)
        print(f"[OUTPUT]\n{r.get('result')}\n")

    os_kernel.save_report("v14_snapshot_report.html")
    print("\n[COMPLETE] v1.4 Demo Finished.")

if __name__ == "__main__":
    v14_demo()
