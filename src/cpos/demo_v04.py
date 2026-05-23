import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList
from cpos.memory_policy import MemoryPolicy

def v04_demo():
    print("--- Context Pointer OS Kernel v0.4: IPC & Cognitive Scheduling ---")
    
    # 1. Setup
    registry = ContextRegistry()
    # ctx7: NeuroState (with low calm)
    registry.register(ContextObject(
        id="ctx7", type="neurostate", title="NeuroState",
        content_ref="internal://neurostate", summary="Core state",
        tokens_estimate=100, data=json.dumps({"calm": 0.2, "openness": 0.5})
    ))
    # ctx4: Large log
    registry.register(ContextObject(
        id="ctx4", type="log", title="Large Log",
        content_ref="storage://log.txt", summary="Big data here",
        tokens_estimate=2000, importance=0.5
    ))
    
    acl = AccessControlList()
    store = ContextStore(registry)
    scheduler = Scheduler(store, acl)
    
    # 2. Test IPC (Agent Messaging)
    print("\n[V0.4: IPC - Security Agent sends message to Persona Agent]")
    scheduler.set_agent("security-agent")
    res_ipc = scheduler.dispatch('>MEM:SEND #ctx0 !8 | to=persona-agent body="Detected high stress in trace"')
    print(f"IPC Result: {res_ipc}")
    
    msg_id = res_ipc["result"].split(" as ")[1]
    
    # Verify Persona Agent can read it, but Security Agent cannot (unless sender)
    print(f"\n[V0.4: ACL - Persona Agent loading {msg_id}]")
    scheduler.set_agent("persona-agent")
    # msg_id is 'msg_0', so we need #ctxmsg_0
    res_load_persona = scheduler.dispatch(f">MEM:LOAD #ctx{msg_id} !8")
    print(f"Persona Result: {res_load_persona}")
    print(f"Loaded Content: {registry.get(msg_id).data}")
    
    # 3. Test Cognitive Scheduling (Priority Boost)
    print("\n[V0.4: Cognitive Scheduling - Low Calm Detected]")
    # calm is 0.2, so 'summarize' should get priority boost (+2)
    scheduler.set_agent("root")
    scheduler.dispatch(">MEM:SUM #ctx4 !5")
    
    last_audit = scheduler.audit_log[-1]
    print(f"Action: {last_audit['action']} | Target: {last_audit['target']}")
    # Machine code: m4m7 (Domain=m, Target=4, Action=m, Priority=5+2=7)
    print(f"Audit AIT (with Boost): {last_audit['instr']}")
    
    if last_audit['instr'].endswith('7'):
        print("Priority Boost Verified: 5 -> 7 (+2 boost due to low calm)")

if __name__ == "__main__":
    v04_demo()
