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
    scheduler.retrieval_policy.cognitive_budget = 9999.0
    return registry, store, acl, scheduler

def test_trust_and_invalidation():
    registry, store, acl, scheduler = setup_os()
    registry.register(ContextObject(id="ctx1", type="memory", title="T1", summary="S1", trust_score=0.5))
    scheduler.dispatch('>MEM:TRUST #ctx1 !5 | score=0.8')
    assert registry.get("ctx1").trust_score == 0.8
    scheduler.dispatch('>MEM:LOAD #ctx1 !5')
    scheduler.dispatch('>MEM:INVALIDATE #ctx1 !9')
    assert registry.get("ctx1").status == "invalidated"
    res = scheduler.dispatch('>MEM:LOAD #ctx1 !5')
    assert res["status"] == "error"

def test_retrieval_governance():
    registry, store, acl, scheduler = setup_os()
    registry.register(ContextObject(id="ctx_pub", type="spec", title="P", summary="S", data="PUB_DATA", trust_score=1.0, sensitivity_level="public"))
    registry.register(ContextObject(id="ctx_sec", type="spec", title="S", summary="S", data="SEC_DATA", trust_score=1.0, sensitivity_level="restricted"))
    acl.set_role("user", Role.USER); acl.grant_type("user", "spec"); scheduler.set_agent("user")
    scheduler.dispatch(">MEM:LOAD #ctx_pub !5"); scheduler.dispatch(">MEM:LOAD #ctx_sec !5")
    content = scheduler.get_active_content()
    assert "PUB_DATA" in content
    # The actual redacted string in the code is "[REDACTED: Sensitivity exceeds current policy]"
    assert "[REDACTED: Sensitivity exceeds current policy]" in content

def test_recursive_dependencies():
    registry, store, acl, scheduler = setup_os()
    registry.register(ContextObject(id="ctx_c", type="code", title="C", summary="S", data="D"))
    registry.register(ContextObject(id="ctx_b", type="code", title="B", summary="S", data="D", dependencies=["ctx_c"]))
    registry.register(ContextObject(id="ctx_a", type="code", title="A", summary="S", data="D", dependencies=["ctx_b"]))
    scheduler.dispatch(">MEM:LOAD #ctx_a !5")
    assert "ctx_c" in store.active_contexts

def test_pointer_exchange():
    registry, store, acl, scheduler = setup_os()
    registry.register(ContextObject(id="ctx_data", type="code", title="D", summary="S", data="SECRET"))
    acl.set_role("alice", Role.USER); acl.set_role("bob", Role.USER); acl.grant("alice", "ctx_data")
    scheduler.set_agent("alice"); res = scheduler.dispatch('>MEM:EXCHANGE #ctx_data !5 | to=bob')
    ptr_id = res['result'].split("via ")[1]
    scheduler.set_agent("bob"); scheduler.dispatch(f">MEM:LOAD #{ptr_id} !5"); scheduler.dispatch(">MEM:LOAD #ctx_data !5")
    assert "SECRET" in scheduler.get_active_content()

def test_speculative_branching_v03():
    registry, store, acl, scheduler = setup_os()
    registry.register(ContextObject(id="ctx1", type="reasoning", title="R", summary="S", data="OLD", trust_score=0.8))
    acl.grant("root", "ctx1")
    # FORK
    res_fork = scheduler.dispatch(">REA:FORK #ctx1 !5 | hyp1")
    assert res_fork["status"] == "ok"
    hyp_id = "ctx1.hyp1"
    # UPDATE
    res_write = scheduler.dispatch(f">REA:UPDATE #{hyp_id} !5 | data=NEW")
    assert res_write["status"] == "ok"
    assert registry.get(hyp_id).data == "NEW"
    # COMMIT
    res_commit = scheduler.dispatch(f">REA:COMMIT #{hyp_id} !9")
    assert res_commit["status"] == "ok"
    assert registry.get("ctx1").data == "NEW"
