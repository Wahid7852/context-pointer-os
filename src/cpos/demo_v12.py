import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject
from cpos.acl import Role

def v12_demo():
    print("================================================")
    print("   CONTEXT POINTER OS v1.2 - CONNECTIVITY       ")
    print("================================================")
    
    workspace = "/tmp/cpos_v12"
    os_kernel = CPOS(workspace=workspace)
    
    # 0. Setup Roles & Permissions
    os_kernel.acl.set_role("root", Role.ROOT)
    os_kernel.acl.grant_type("agent1", "shared")
    os_kernel.acl.grant_type("agent2", "shared")
    os_kernel.acl.grant_type("agent1", "api") # Allow agent1 to see web data

    # 1. HTTP Driver Test (Connectivity)
    print("\n[V1.2: Network Interface Test]")
    # Mount http driver
    os_kernel.step(">MEM:DEV #ctx0 !9 | mount=https")
    
    # Register a live context (e.g. GitHub API for this repo metadata)
    os_kernel.registry.register(ContextObject(
        id="ctx_web", type="api", title="Repo Metadata", 
        content_ref="https://api.github.com/repos/kagioneko/context-pointer-os", 
        summary="Live info from GitHub", tokens_estimate=1000
    ))
    
    print("Fetching live data from GitHub API...")
    os_kernel.step(">MEM:LOAD #ctx_web !5")
    web_obj = os_kernel.registry.get("ctx_web")
    if web_obj and web_obj.data and "NET_ERR" not in web_obj.data:
        data = json.loads(web_obj.data)
        print(f"Success! Repo Name: {data.get('full_name')}")
        print(f"Description: {data.get('description')}")
    else:
        print(f"Network Access Failed. Result: {web_obj.data if web_obj else 'None'}")

    # 2. Shared Memory Test (Collaboration)
    print("\n[V1.2: Shared Memory (SHM) Test]")
    # Allocating a shared memory segment via Syscall
    res_shm = os_kernel.step(">MEM:SYS #ctx0 !9 | func=shm_alloc")
    print(f"System Response: {res_shm['result']}")
    
    if "Allocated SHM: " in res_shm["result"]:
        shm_id = res_shm["result"].split("Allocated SHM: ")[1]
    else:
        # Fallback if format is slightly different
        shm_id = res_shm["result"].split(":")[-1].strip()
    
    print(f"Acquired SHM ID: {shm_id}")
    
    # Agent 1 writes to SHM (Write can happen on registry or RAM, here we ensure it's loaded)
    os_kernel.step(f">MEM:LOAD #{shm_id} !9", agent="agent1", pid=101)
    os_kernel.step(f">MEM:UPDATE #{shm_id} !9 | data=Shared Knowledge Base Alpha", agent="agent1", pid=101)
    
    # Agent 2 loads SHM (Mapping it to their local RAM space)
    print(f"Agent 2 (PID 102) mapping {shm_id} to RAM...")
    os_kernel.step(f">MEM:LOAD #{shm_id} !9", agent="agent2", pid=102)
    
    # Agent 2 reads from SHM
    print("Agent 2 (PID 102) reading shared memory...")
    os_kernel.scheduler.set_agent("agent2", pid=102)
    view = os_kernel.scheduler.get_active_content()
    if "Shared Knowledge Base Alpha" in view:
        print("Success: Agent 2 can access the Collaborative SHM segment.")
    else:
        print("Failure: SHM access denied.")

    # 3. Final Report
    os_kernel.save_report("v12_connectivity_report.html")
    print("\n[COMPLETE] v1.2 Demo Finished.")

if __name__ == "__main__":
    v12_demo()
