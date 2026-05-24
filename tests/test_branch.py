import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler

def test_branch_creation():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="data", title="Root", summary="S", data="A"))
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    # Execute branch
    res = scheduler.dispatch(">MEM:BRANCH #ctx1 !5 | hyp1")
    assert res["status"] == "ok"
    assert "ctx1.hyp1" in registry.registry
    assert "ctx1.hyp1" in store.active_contexts
    
    # Check inheritance
    branch = registry.get("ctx1.hyp1")
    assert branch.data == "A"
    assert branch.metadata["is_hypothesis"] is True

def test_branch_isolation():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="data", title="Root", summary="S", data="A"))
    scheduler = Scheduler(ContextStore(registry))
    
    scheduler.dispatch(">MEM:BRANCH #ctx1 !5 | b1")
    scheduler.dispatch(">MEM:UPDATE #ctx1.b1 !5 | data=B")
    
    assert registry.get("ctx1.b1").data == "B"
    assert registry.get("ctx1").data == "A"
