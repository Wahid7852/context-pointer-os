import os
import json
from cpos.registry import ContextRegistry, ContextObject
from cpos.context_store import ContextStore
from cpos.scheduler import Scheduler
from cpos.boot import CognitiveBootloader
from cpos.dashboard import render_dashboard

def v09_demo():
    print("--- Context Pointer OS Kernel v0.9: Bootloader & Dashboard ---")
    
    # 1. Setup
    registry = ContextRegistry()
    registry.register(ContextObject(id="ctx7", type="neurostate", title="NeuroState", content_ref="", summary="State", tokens_estimate=100, data='{"calm": 0.8}'))
    
    store = ContextStore(registry)
    scheduler = Scheduler(store)
    bootloader = CognitiveBootloader(scheduler)

    # 2. Test Bootloader
    # BIOS Script: Mount device, Load core contexts
    bios_script = [
        ">MEM:LOAD #ctx7 !9",
        ">MEM:LS #ctx0 !1",
        ">MEM:SEND #ctx0 !5 | to=root body=\"Kernel Boot Successful\""
    ]
    
    if bootloader.boot(bios_script):
        print("AI System Online.")

    # 3. Simulate some activity (to heat things up)
    print("\n[V0.9: Activity Simulation]")
    for _ in range(6):
        scheduler.dispatch(">MEM:LOAD #ctx7 !5")
    
    # 4. Render Dashboard
    dashboard_path = "cpos_dashboard.html"
    render_dashboard(registry, store, scheduler.audit_log, dashboard_path)
    print(f"Check the file: {os.path.abspath(dashboard_path)}")

if __name__ == "__main__":
    v09_demo()
