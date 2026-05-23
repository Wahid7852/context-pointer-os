import pytest
from src.cpos.registry import ContextRegistry, ContextObject
from src.cpos.context_store import ContextStore
from src.cpos.scheduler import Scheduler
from src.cpos.acl import Role

@pytest.fixture
def setup_cpos():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="memory", title="T1", content_ref="", summary="S1", tokens_estimate=10, data="Initial"))
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    return scheduler, store, registry

def test_scheduler_load_flow(setup_cpos):
    scheduler, store, _ = setup_cpos
    # Using AIT code: m1l5 (memory, ctx1, load, priority 5)
    res = scheduler.dispatch("m1l5")
    assert res["status"] == "ok"
    assert "ctx1" in store.active_contexts

def test_scheduler_write_flow(setup_cpos):
    scheduler, _, registry = setup_cpos
    # Note: EAP uses UPDATE for write
    res = scheduler.dispatch(">MEM:UPDATE #ctx1 !5 | NewData")
    assert res["status"] == "ok"
    assert registry.get("ctx1").data == "NewData"

def test_scheduler_permission_denied(setup_cpos):
    scheduler, _, registry = setup_cpos
    registry.register(ContextObject(id="ctx7", type="neurostate", title="NS", content_ref="", summary="S", tokens_estimate=10, data='{"calm": 1.0}'))
    
    scheduler.set_agent("guest_user", pid=101)
    scheduler.acl.set_role("guest_user", Role.GUEST)
    
    # Guest cannot write to neurostate (sensitive type)
    # Using NEU as per EAP.DOMAIN_MAP
    res = scheduler.dispatch(">NEU:UPDATE #ctx7 !9 | calm=0.0")
    assert res["status"] == "error"
    # Result should be ERR_PERMISSION_DENIED
    assert res["result"] == "ERR_PERMISSION_DENIED"

def test_scheduler_isolation_violation(setup_cpos):
    scheduler, _, registry = setup_cpos
    obj = registry.get("ctx1")
    obj.owner_pid = 200
    
    scheduler.set_agent("user", pid=201)
    res = scheduler.dispatch("m1l5")
    assert res["status"] == "error"
    assert res["result"] == "ERR_PROCESS_ISOLATION_VIOLATION"
