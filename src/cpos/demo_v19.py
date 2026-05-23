import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v19_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.9 - ANTI-TAMPER LOG    ")
    print("================================================")
    
    workspace = "/tmp/cpos_v19"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    os_kernel.acl.set_role("root", Role.ROOT)

    # 1. GENERATE SOME LOG ENTRIES
    print("\n[V1.9: Generating Secure Audit Trail]")
    os_kernel.step(">MEM:LOAD #ctx1 !5")
    os_kernel.step(">MEM:UPDATE #ctx1 !9 | data=SecureValue")
    os_kernel.step(">MEM:LS #ctx0 !1")
    
    # Check initial integrity
    is_ok = os_kernel.scheduler.verify_journal()
    print(f"Initial Journal Integrity: {'VALID' if is_ok else 'INVALID'}")

    # 2. SIMULATE TAMPERING
    print("\n[SCENARIO: Unauthorized Log Tampering]")
    print("An attacker attempts to modify a past log entry to hide an action.")
    
    # Target the second entry (UPDATE)
    audit_log = os_kernel.scheduler.audit_log
    if len(audit_log) >= 2:
        original_result = audit_log[1]["result"]
        print(f"Original Entry [1] Result: {original_result}")
        
        # Tamper: Change the result message
        audit_log[1]["result"] = "Updated (Attacker modified this log)"
        print(f"Tampered Entry [1] Result: {audit_log[1]['result']}")

    # 3. INTEGRITY VERIFICATION
    print("\n[V1.9: Verifying Journal Integrity...]")
    is_valid_after_tamper = os_kernel.scheduler.verify_journal()
    print(f"Journal Integrity after tamper: {'VALID' if is_valid_after_tamper else 'CORRUPTED'}")
    
    if not is_valid_after_tamper:
        print("[SUCCESS] Kernel detected log tampering via HMAC chain mismatch.")
    else:
        print("[FAILURE] Kernel failed to detect tampering.")

    # 4. SIMULATE DELETION
    print("\n[SCENARIO: Log Deletion Attack]")
    print("An attacker deletes the last entry to hide recent activity.")
    audit_log.pop()
    
    is_valid_after_deletion = os_kernel.scheduler.verify_journal()
    print(f"Journal Integrity after deletion: {'VALID' if is_valid_after_deletion else 'CORRUPTED'}")
    
    if not is_valid_after_deletion:
        print("[SUCCESS] Kernel detected log deletion (Chain broken).")

    os_kernel.save_report("v19_antitamper_report.html")
    print("\n[COMPLETE] v1.9 Demo Finished.")

if __name__ == "__main__":
    v19_demo()
