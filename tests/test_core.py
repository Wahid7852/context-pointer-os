import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role
from cpos.memory_policy import MemoryPolicy

def test_m4l8_flow():
    """Tests the basic Load flow (m4l8)."""
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx4", type="log", title="Test Log", content_ref="", summary="Sum", tokens_estimate=100))
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    res = scheduler.dispatch("m4l8")
    assert res["status"] == "ok"
    assert "ctx4" in store.active_contexts

def test_branching():
    """Tests speculative branching and merging."""
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="log", title="Root", content_ref="", summary="Sum", tokens_estimate=100, data="ORIGINAL"))
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

def test_acl_roles():
    """Tests role-based access control."""
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx20", type="persona", title="Persona", content_ref="", summary="Sum", tokens_estimate=100))
    store = ContextStore(registry)
    acl = AccessControlList()
    acl.set_role("guest", Role.GUEST)
    scheduler = Scheduler(store, acl)
    
    # Guest should be denied persona access
    scheduler.set_agent("guest")
    res = scheduler.dispatch(">MEM:LOAD #ctx20 !9")
    assert res["status"] == "error"
    assert res["result"] == "ERR_PERMISSION_DENIED"

def test_paging():
    """Tests automated virtual memory paging."""
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctxH", type="log", title="Huge", content_ref="", summary="Summary of Huge", tokens_estimate=1000, importance=0.8, data="DATA"))
    store = ContextStore(registry)
    policy = MemoryPolicy(store, token_limit=500)
    
    store.load("ctxH")
    policy.enforce()
    
    # Should be swapped to summary
    assert "[SUMMARY ONLY]" in registry.get("ctxH").data
