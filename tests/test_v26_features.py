import pytest
import json
from datetime import datetime
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role
from cpos.memory_policy import RetrievalPolicy

def setup_os():
    registry = ContextRegistry()
    store = ContextStore(registry)
    acl = AccessControlList()
    scheduler = Scheduler(store, acl)
    return registry, store, acl, scheduler

def test_trust_and_invalidation():
    registry, store, acl, scheduler = setup_os()
    
    registry.register(ContextObject(
        id="ctx1", type="memory", title="T1", summary="S1", 
        content_ref="ref1", trust_score=0.5
    ))
    
    # 1. Test TRUST command
    scheduler.dispatch('>MEM:TRUST #ctx1 !5 | score=0.8 reason="verified"')
    assert registry.get("ctx1").trust_score == 0.8
    
    # 2. Test INVALIDATE command
    scheduler.dispatch('>MEM:LOAD #ctx1 !5')
    assert "ctx1" in store.active_contexts
    
    scheduler.dispatch('>MEM:INVALIDATE #ctx1 !9 | reason="outdated" replacement=ctx2')
    assert registry.get("ctx1").status == "invalidated"
    assert "ctx1" not in store.active_contexts # Should be unloaded
    
    # 3. Test Load prevention for invalidated
    res = scheduler.dispatch('>MEM:LOAD #ctx1 !5')
    assert res["status"] == "error"
    assert res["result"] == "ERR_LOAD_FAILED_CHECK_STATUS"

def test_retrieval_governance():
    registry, store, acl, scheduler = setup_os()
    
    # High Trust, Public
    registry.register(ContextObject(
        id="ctx_pub", type="spec", title="Pub", summary="S", data="PUB_DATA",
        trust_score=1.0, sensitivity_level="public"
    ))
    # Low Trust
    registry.register(ContextObject(
        id="ctx_low", type="spec", title="Low", summary="S", data="LOW_DATA",
        trust_score=0.3, sensitivity_level="internal"
    ))
    # Restricted
    registry.register(ContextObject(
        id="ctx_sec", type="spec", title="Sec", summary="S", data="SEC_DATA",
        trust_score=1.0, sensitivity_level="restricted"
    ))
    
    acl.set_role("user", Role.USER)
    acl.grant_type("user", "spec")
    scheduler.set_agent("user")
    
    scheduler.dispatch(">MEM:LOAD #ctx_pub !5")
    scheduler.dispatch(">MEM:LOAD #ctx_low !5")
    scheduler.dispatch(">MEM:LOAD #ctx_sec !5")
    
    # Default policy: min_trust=0.5, max_sensitivity=internal
    content = scheduler.get_active_content()
    
    assert "PUB_DATA" in content
    assert "[FILTERED] Trust Score 0.3" in content
    assert "[REDACTED: Sensitivity Level 'restricted'" in content

def test_recursive_dependencies():
    registry, store, acl, scheduler = setup_os()
    
    registry.register(ContextObject(id="ctx_c", type="code", title="C", summary="S", data="D"))
    registry.register(ContextObject(id="ctx_b", type="code", title="B", summary="S", data="D", dependencies=["ctx_c"]))
    registry.register(ContextObject(id="ctx_a", type="code", title="A", summary="S", data="D", dependencies=["ctx_b"]))
    
    scheduler.dispatch(">MEM:LOAD #ctx_a !5")
    
    assert "ctx_a" in store.active_contexts
    assert "ctx_b" in store.active_contexts
    assert "ctx_c" in store.active_contexts

def test_pointer_exchange():
    registry, store, acl, scheduler = setup_os()
    
    registry.register(ContextObject(
        id="ctx_data", type="code", title="Data", summary="S", data="SECRET",
        sensitivity_level="internal"
    ))
    acl.set_role("alice", Role.USER)
    acl.set_role("bob", Role.USER)
    acl.grant("alice", "ctx_data")
    
    # Alice exchanges with Bob
    scheduler.set_agent("alice")
    res = scheduler.dispatch('>MEM:EXCHANGE #ctx_data !5 | to=bob purpose="collab"')
    
    ptr_msg_id = res['result'].split("via ")[1]
    
    # Bob should now have access to ctx_data
    scheduler.set_agent("bob")
    res_load = scheduler.dispatch(f">MEM:LOAD #{ptr_msg_id} !5")
    assert res_load["status"] == "ok"
    
    res_load_data = scheduler.dispatch(">MEM:LOAD #ctx_data !5")
    assert res_load_data["status"] == "ok"
    assert "SECRET" in scheduler.get_active_content()

def test_speculative_branching_v03():
    registry, store, acl, scheduler = setup_os()
    
    registry.register(ContextObject(
        id="ctx_root", type="reasoning", title="Root", summary="S", data="OLD",
        trust_score=0.8
    ))
    
    # FORK
    scheduler.dispatch(">REA:FORK #ctx_root !5 | hyp1")
    hyp_id = "ctx_root.hyp1"
    assert registry.get(hyp_id).trust_score == 0.4
    
    # UPDATE Hypothesis
    scheduler.dispatch(f">REA:UPDATE #{hyp_id} !5 | data=NEW")
    assert registry.get("ctx_root").data == "OLD"
    
    # COMMIT
    scheduler.dispatch(f">REA:COMMIT #{hyp_id} !9")
    assert registry.get("ctx_root").data == "NEW"
    assert registry.get("ctx_root").trust_score > 0.8
    assert registry.get(hyp_id).status == "deleted"

def test_context_reconstructor_warnings():
    registry, store, acl, scheduler = setup_os()
    
    registry.register(ContextObject(id="ctx_p", type="code", title="P", summary="S", data="D"))
    registry.branch("ctx_p", "b1")
    
    scheduler.dispatch(">MEM:LOAD #ctx_p !5")
    scheduler.dispatch(">MEM:LOAD #ctx_p.b1 !5")
    
    content = scheduler.get_active_content()
    assert "SYSTEM CONTEXT WARNINGS" in content
    assert "Both parent 'ctx_p' and branch 'ctx_p.b1' are active" in content
