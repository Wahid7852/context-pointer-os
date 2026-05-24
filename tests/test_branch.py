import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler

def test_speculative_branch_merge():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="data", title="R", summary="S", data="A"))
    scheduler = Scheduler(ContextStore(registry))

    # Branch
    scheduler.dispatch(">MEM:BRANCH #ctx1 !5 | b1")
    assert "ctx1.b1" in registry.registry

    # Update branch
    scheduler.dispatch(">MEM:UPDATE #ctx1.b1 !5 | data=B")
    assert registry.get("ctx1.b1").data == "B"
    assert registry.get("ctx1").data == "A"

    # Merge
    scheduler.dispatch(">MEM:MERGE #ctx1.b1 !5")
    # In v0.1+, merge/commit updates the parent and deletes the branch
    assert registry.get("ctx1").data == "B"
    assert registry.get("ctx1.b1").status == "deleted"
