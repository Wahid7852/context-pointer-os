from typing import List
from .scheduler import Scheduler

class CognitiveBootloader:
    """The 'BIOS'. Executes a sequence of instructions to initialize the agent's world."""
    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler

    def boot(self, boot_script: List[str]):
        print(f"--- [BOOTLOADER] Starting Cognitive Sequence ({len(boot_script)} steps) ---")
        for i, line in enumerate(boot_script):
            print(f"[BOOT] Step {i+1}: {line}")
            res = self.scheduler.dispatch(line)
            if res["status"] != "ok":
                print(f"[BOOT ERROR] Failed at step {i+1}: {res.get('result')}")
                return False
        print("--- [BOOTLOADER] Sequence Completed Successfully ---")
        return True
