import pytest
from src.cpos.registry import ContextRegistry, ContextObject
from src.cpos.context_store import ContextStore
from src.cpos.scheduler import Scheduler

def test_speculative_branch_merge():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="data", title="R", content_ref="", summary="S", tokens_estimate=10, data="A"))
    scheduler = Scheduler(ContextStore(registry))
    
    # Branch using EAP
    res = scheduler.dispatch(">MEM:BRANCH #ctx1 !5 | b1")
    assert res["status"] == "ok"
    assert "ctx1.b1" in registry.registry
    
    # Update branch
    res = scheduler.dispatch(">MEM:UPDATE #ctx1.b1 !5 | B")
    assert res["status"] == "ok"
    assert registry.get("ctx1.b1").data == "B"
    assert registry.get("ctx1").data == "A"
    
    # Merge
    res = scheduler.dispatch(">MEM:MERGE #ctx1.b1 !5")
    assert res["status"] == "ok"
    assert registry.get("ctx1").data == "B"
    # Merged branch should be unloaded from active_contexts
    assert "ctx1.b1" not in scheduler.store.active_contexts
