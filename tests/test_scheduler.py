import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler

def test_scheduler_load_flow():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="log", title="T", content_ref="", summary="S", tokens_estimate=10))
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    res = scheduler.dispatch(">MEM:LOAD #ctx1 !5")
    assert res["status"] == "ok"
    assert "ctx1" in store.active_contexts

def test_scheduler_unknown_instr():
    scheduler = Scheduler(ContextStore(ContextRegistry()))
    res = scheduler.dispatch("INVALID")
    assert res["status"] == "error"
    assert res["code"] == "ERR_UNKNOWN_INSTRUCTION"
