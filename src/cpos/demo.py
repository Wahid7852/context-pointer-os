from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList
from cpos.memory_policy import MemoryPolicy

def main():
    print("--- Context Pointer OS Kernel v0.1 Booting ---")
    
    # 1. Initialize Memory Map (Registry)
    registry = ContextRegistry()
    registry.register(ContextObject(
        id="ctx4", type="security_log", title="XSS investigation log",
        content_ref="storage://logs/xss.json", summary="XSS vulnerabilities detected",
        tokens_estimate=2000, importance=0.9
    ))
    registry.register(ContextObject(
        id="ctx20", type="persona", title="Persona Internal State",
        content_ref="storage://persona/v1.json", summary="Internal thoughts and emotions",
        tokens_estimate=1500, importance=0.7
    ))
    registry.register(ContextObject(
        id="ctx30", type="task_cache", title="Old Task Cache",
        content_ref="storage://tasks/old.json", summary="Generic task history",
        tokens_estimate=3000, importance=0.3
    ))

    # 2. Setup ACL
    acl = AccessControlList()
    acl.grant_type("security-agent", "security_log")
    acl.grant_type("security-agent", "task_cache")
    # persona is NOT granted to security-agent

    # 3. Initialize RAM and Scheduler
    store = ContextStore(registry)
    scheduler = Scheduler(store, acl)
    policy = MemoryPolicy(store, token_limit=4000)

    # 4. Test ACL
    print("\n[ACL Test: security-agent tries to load persona]")
    scheduler.set_agent("security-agent")
    res1 = scheduler.dispatch(">MEM:LOAD #ctx20 !9")
    print(f"Result: {res1}")

    print("\n[ACL Test: security-agent loads security_log]")
    res2 = scheduler.dispatch(">MEM:LOAD #ctx4 !9")
    print(f"Result: {res2}")

    # 5. Test Memory Policy (Token pressure)
    print("\n[Memory Policy Test: Loading more to trigger pressure]")
    scheduler.dispatch(">MEM:LOAD #ctx30 !5")
    
    active_ids = list(store.active_contexts.keys())
    total_tokens = sum(obj.tokens_estimate for obj in store.active_contexts.values())
    print(f"Before Enforce: {active_ids} (Total: {total_tokens} tokens)")
    
    print("Enforcing Policy...")
    unloaded = policy.enforce()
    
    active_ids = list(store.active_contexts.keys())
    total_tokens = sum(obj.tokens_estimate for obj in store.active_contexts.values())
    print(f"After Enforce: {active_ids} (Total: {total_tokens} tokens)")
    print(f"Unloaded: {unloaded}")

    print("\n[Final Audit Log Snapshot]")
    for entry in scheduler.audit_log:
        print(f"{entry['agent']} | {entry['instr']} | {entry['status']} | {entry['result']}")

if __name__ == "__main__":
    main()
