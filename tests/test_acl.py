import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.acl import AccessControlList, Role

def test_acl_guest_denied():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctxP", type="persona", title="P", content_ref="", summary="S", tokens_estimate=10))
    acl = AccessControlList()
    acl.set_role("guest", Role.GUEST)
    scheduler = Scheduler(ContextStore(registry), acl)
    
    scheduler.set_agent("guest")
    res = scheduler.dispatch(">MEM:LOAD #ctxP !9")
    assert res["status"] == "error"
    assert "PERMISSION_DENIED" in res["result"]

def test_acl_root_allowed():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctxP", type="persona", title="P", content_ref="", summary="S", tokens_estimate=10))
    scheduler = Scheduler(ContextStore(registry)) # defaults to root
    res = scheduler.dispatch(">MEM:LOAD #ctxP !9")
    assert res["status"] == "ok"
