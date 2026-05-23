import os
import sys
from .kernel import CPOS

class CognitiveShell:
    """The 'Virtual Terminal'. Interactive EAP interface for agents or humans."""
    def __init__(self, kernel: CPOS):
        self.kernel = kernel
        self.current_agent = "root"
        self.current_pid = 0

    def start(self):
        print("\n" + "="*50)
        print("   CPOS COGNITIVE SHELL v1.4")
        print("   Type 'exit' to quit, 'help' for examples.")
        print("="*50)
        
        while True:
            try:
                prompt = f"{self.current_agent}@pid{self.current_pid}> "
                line = input(prompt).strip()
                
                if not line: continue
                if line.lower() in ["exit", "quit"]: break
                if line.lower() == "help":
                    print("Examples:\n  >MEM:LS #ctx0 !1\n  >MEM:LOAD #ctx7 !9\n  >MEM:SYS #ctx0 !9 | func=snapshot")
                    continue
                
                # Handle session changes (e.g. su agent_name)
                if line.startswith("su "):
                    self.current_agent = line.split(" ")[1]
                    print(f"Switched to {self.current_agent}")
                    continue

                res = self.kernel.step(line, agent=self.current_agent, pid=self.current_pid)
                
                if res["status"] == "ok":
                    if res.get("result"):
                        print(f"\n[OUTPUT]\n{res['result']}\n")
                    else:
                        print("\n[OK]\n")
                else:
                    print(f"\n[ERROR] {res.get('code') or res.get('result')}\n")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Shell Error: {str(e)}")

def main():
    workspace = "/tmp/cpos_shell"
    os.makedirs(workspace, exist_ok=True)
    kernel = CPOS(workspace)
    shell = CognitiveShell(kernel)
    shell.start()

if __name__ == "__main__":
    main()
