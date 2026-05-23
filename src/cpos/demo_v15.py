import os
import json
import time
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v15_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.5 - MULTI-AGENT IPC    ")
    print("================================================")
    
    workspace = "/tmp/cpos_v15"
    os.makedirs(workspace, exist_ok=True)
    os_kernel = CPOS(workspace=workspace)
    
    # 1. Setup Multi-Agent Environment
    print("\n[V1.5: Setting up Agents and Permissions]")
    os_kernel.acl.set_role("root", Role.ROOT)
    os_kernel.acl.set_role("security_agent", Role.USER)
    os_kernel.acl.set_role("memory_agent", Role.USER)
    
    # Shared Memory Allocation
    print("[V1.5: Allocating Shared Memory (SHM)]")
    res_shm = os_kernel.step(">MEM:SYS #ctx0 !9 | func=shm_alloc", agent="root")
    shm_id = res_shm["result"].split(": ")[1]
    
    # Grant access to agents
    os_kernel.acl.grant("security_agent", shm_id)
    os_kernel.acl.grant("memory_agent", shm_id)

    # 2. Concurrent Task Simulation (Priority-Based)
    print("\n[V1.5: Simulated Concurrent Tasks with Priority Queue]")
    # memory_agent: Low priority background load
    # security_agent: High priority audit
    tasks = [
        {"agent": "memory_agent", "cmd": ">MEM:LOAD #ctx1 !1", "desc": "Background Sync"},
        {"agent": "security_agent", "cmd": ">MEM:UPDATE #ctx7 !9 | status=scanning", "desc": "Security Audit (High Priority)"},
        {"agent": "memory_agent", "cmd": ">MEM:LOAD #ctx2 !2", "desc": "Context Fetch"}
    ]
    
    # Injecting tasks into kernel
    for t in tasks:
        print(f"Queueing: [{t['agent']}] {t['desc']} (Cmd: {t['cmd']})")
        # In this demo, we bypass the immediate 'pop' of dispatch to show queueing
        # Actually, let's use the new dispatch which sorts and pops.
        # To show priority, we'll manually append to task_queue then call dispatch.
        from cpos.eap import EAPParser
        instr = EAPParser.parse(t['cmd'])
        os_kernel.scheduler.task_queue.append(instr)
    
    print("\n[V1.5: Kernel Tick - Executing by Priority]")
    # Execute 3 times to clear the queue
    for i in range(3):
        res = os_kernel.scheduler.dispatch(">MEM:LS #ctx0 !1") # Dummy input to trigger a tick
        print(f"Tick {i+1}: Executed target {os_kernel.scheduler.audit_log[-1]['target']} with Priority {os_kernel.scheduler.audit_log[-1]['instr'][-1]}")

    # 3. Inter-Process Communication (IPC)
    print("\n[V1.5: Inter-Process Communication (IPC) - Message Send]")
    ipc_res = os_kernel.step(f'>MEM:SEND #ctx0 !5 | to=memory_agent body="Security audit complete. SHM updated."', agent="security_agent")
    print(f"IPC Result: {ipc_res['result']}")
    
    msg_id = ipc_res["result"].split(" as ")[1]
    
    # 4. Agent Reception Check
    print("\n[V1.5: Memory Agent checking incoming messages]")
    msgs = os_kernel.step(">MEM:PS #ctx0 !1", agent="memory_agent")
    print(f"Active Contexts for memory_agent:\n{msgs['result']}")
    
    if msg_id in msgs['result']:
        print(f"Success: Message {msg_id} correctly delivered to memory_agent.")
    
    os_kernel.save_report("v15_ipc_report.html")
    print("\n[COMPLETE] v1.5 Demo Finished.")

if __name__ == "__main__":
    v15_demo()
