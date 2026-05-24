import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role
from cpos.memory_policy import MemoryPolicy

def test_kernel_boot_sequence():
    registry = ContextRegistry()
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    # Simulate boot script
    boot_script = [
        ">MEM:LOAD #ctx1 !9",
        ">SEC:POLICY #ctx0 !9 | min_trust=0.8"
    ]
    
    registry.register(ContextObject(id="ctx1", type="memory", title="Boot", summary="S", data="D"))
    
    for cmd in boot_script:
        scheduler.dispatch(cmd)
        
    assert "ctx1" in store.active_contexts
    assert scheduler.retrieval_policy.minimum_trust_score == 0.8

def test_branching():
    """Tests speculative branching and merging."""
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="log", title="Root", summary="Sum", data="ORIGINAL"))
    store = ContextStore(registry)
    scheduler = Scheduler(store)

    # Branch
    scheduler.dispatch(">MEM:BRANCH #ctx1 !5 | hyp_a")
    branch_id = "ctx1.hyp_a"
    assert branch_id in registry.registry

    # Modify branch
    scheduler.dispatch(f">MEM:UPDATE #{branch_id} !5 | data=MODIFIED")
    assert registry.get(branch_id).data == "MODIFIED"
    assert registry.get("ctx1").data == "ORIGINAL"

    # Merge
    scheduler.dispatch(f">MEM:MERGE #{branch_id} !5")
    assert registry.get("ctx1").data == "MODIFIED"

def test_acl_enforcement():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="secure", title="T", summary="S", data="D"))
    acl = AccessControlList()
    store = ContextStore(registry)
    scheduler = Scheduler(store, acl)
    
    acl.set_role("user", Role.USER)
    scheduler.set_agent("user")
    
    # Attempt load without permission
    res = scheduler.dispatch(">MEM:LOAD #ctx1 !5")
    assert res["status"] == "error"
    assert res["result"] == "ERR_PERMISSION_DENIED"

def test_homeostasis_enforcement():
    registry = ContextRegistry()
    for i in range(10):
        registry.register(ContextObject(id=f"ctx{i}", type="data", title="T", summary="S", tokens_estimate=100, data="X"*100))
        
    store = ContextStore(registry)
    policy = MemoryPolicy(store, token_limit=500)
    
    for i in range(8):
        store.load(f"ctx{i}")
        
    # Enforce limit
    targets = policy.enforce()
    assert len(targets) > 0
    assert len(store.active_contexts) <= 5
