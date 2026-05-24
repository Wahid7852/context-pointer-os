import pytest
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler

def test_persona_fusion():
    registry = ContextRegistry()
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    
    # 1. Register two personas
    registry.register(ContextObject(
        id="p1", type="persona", title="Coder", summary="S1", data="CODE_RULES"
    ))
    registry.register(ContextObject(
        id="p2", type="persona", title="Security", summary="S2", data="SEC_RULES"
    ))
    
    # 2. Execute FUSE
    res = scheduler.dispatch(">PER:FUSE #p1 !9 | with=p2")
    assert res["status"] == "ok"
    fused_id = res["result"].split(": ")[1]
    
    # 3. Verify fused object
    fused = registry.get(fused_id)
    assert fused.type == "persona"
    assert "Fused: Coder + Security" in fused.title
    assert "CODE_RULES" in fused.data
    assert "SEC_RULES" in fused.data
