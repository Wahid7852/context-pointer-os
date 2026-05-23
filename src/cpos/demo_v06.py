from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role

def v06_demo():
    print("--- Context Pointer OS Kernel v0.6: User Space & Hardening ---")
    
    # 1. Setup
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx4", type="log", title="System Log", content_ref="", summary="Logs", tokens_estimate=100))
    registry.register(ContextObject(id="ctx20", type="persona", title="Persona Core", content_ref="", summary="Secret", tokens_estimate=500))
    
    acl = AccessControlList()
    # Set roles for different agents
    acl.set_role("admin-agent", Role.ROOT)
    acl.set_role("user-agent", Role.USER)
    acl.set_role("guest-agent", Role.GUEST)
    
    store = ContextStore(registry)
    scheduler = Scheduler(store, acl)

    # 2. Test Shell Commands (ls/ps)
    print("\n[V0.6: Shell Command - ls (List Registry)]")
    res_ls = scheduler.dispatch(">MEM:LS #ctx0 !1")
    print(res_ls["result"])

    print("\n[V0.6: Shell Command - ps (List RAM)]")
    scheduler.dispatch(">MEM:LOAD #ctx4 !5")
    res_ps = scheduler.dispatch(">MEM:PS #ctx0 !1")
    print(res_ps["result"])

    # 3. Test Hardening (Roles & sensitive types)
    print("\n[V0.6: Hardening - Guest trying to access Persona]")
    scheduler.set_agent("guest-agent")
    res_guest = scheduler.dispatch(">MEM:LOAD #ctx20 !9")
    print(f"Guest Result: {res_guest['status']} ({res_guest.get('result')})")

    print("\n[V0.6: Hardening - User accessing Persona]")
    scheduler.set_agent("user-agent")
    # Grant specific permission to user-agent
    acl.grant("user-agent", "ctx20")
    res_user = scheduler.dispatch(">MEM:LOAD #ctx20 !9")
    print(f"User Result: {res_user['status']} ({res_user.get('result')})")

    print("\n[V0.6: Final Audit Log Snapshot]")
    for entry in scheduler.audit_log:
        print(f"{entry['agent']} | {entry['instr']} | {entry['action']} | {entry['status']}")

if __name__ == "__main__":
    v06_demo()
