import pytest
from src.cpos.registry import ContextRegistry, ContextObject
from src.cpos.context_store import ContextStore
from src.cpos.scheduler import Scheduler

def test_scheduler_priority_queue():
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx1", type="memory", title="T1", content_ref="", summary="S1", tokens_estimate=10))
    registry.register(ContextObject(id="ctx2", type="memory", title="T2", content_ref="", summary="S2", tokens_estimate=10))
    scheduler = Scheduler(ContextStore(registry))
    
    # 1. Dispatch a low priority task. Queue is empty, so it executes immediately.
    scheduler.dispatch("m1l1") # Priority 1
    assert scheduler.audit_log[-1]["target"] == "ctx1"

    # 2. Pre-populate the queue to test priority sorting on next dispatch
    from src.cpos.ait import AITInstruction
    # We want ctx2 (priority 9) to be executed next even if we dispatch a priority 1 task
    scheduler.task_queue.append(AITInstruction("memory", "ctx2", "load", 9)) 
    
    # Next dispatch: 
    # - "m1l1" (priority 1) is added to queue. Queue has [ctx2(9), ctx1(1)]
    # - Sorts queue.
    # - Pops highest priority: ctx2(9).
    res = scheduler.dispatch("m1l1")
    assert res["status"] == "ok"
    assert scheduler.audit_log[-1]["target"] == "ctx2"
    
    # Remaining in queue should be the two priority 1 tasks (one from manual append, one from dispatch)
    # Wait, in my previous failed test, len was 2. 
    # Let's check the logic:
    # Manual append: ctx2(9) -> queue: [ctx2(9)]
    # Dispatch("m1l1"): adds ctx1(1) -> queue: [ctx2(9), ctx1(1)] -> pops ctx2(9) -> queue: [ctx1(1)]
    # So len should be 1. 
    # My previous test had:
    # manual append ctx1(1)
    # manual append ctx2(9) -> queue [ctx1(1), ctx2(9)]
    # dispatch "m1l1" -> adds ctx1(1) -> queue [ctx2(9), ctx1(1), ctx1(1)] -> pops ctx2(9) -> queue [ctx1(1), ctx1(1)] -> len 2.
    
    assert len(scheduler.task_queue) == 1
    assert scheduler.task_queue[0].target_id == "ctx1"

def test_interrupt_preemption():
    registry = ContextRegistry()
    # NeuroState ctx7
    registry.register(ContextObject(id="ctx7", type="neurostate", title="NS", content_ref="", summary="S", tokens_estimate=10, data='{"corruption": 0.9}'))
    registry.register(ContextObject(id="ctx1", type="memory", title="T1", content_ref="", summary="S1", tokens_estimate=10))
    scheduler = Scheduler(ContextStore(registry))
    
    # This dispatch should trigger a NeuroState interrupt before executing the memory load
    res = scheduler.dispatch("m1l5")
    
    # Check audit log: should have NeuroState write (interrupt) then Memory load
    assert len(scheduler.audit_log) >= 2
    assert scheduler.audit_log[-2]["target"] == "ctx7"
    assert scheduler.audit_log[-2]["action"] == "write"
    assert scheduler.audit_log[-1]["target"] == "ctx1"
