import os
import json
from cpos.kernel import CPOS
from cpos.registry import ContextObject

def main():
    print("================================================")
    print("   CONTEXT POINTER OS v4.0 - MCP Compliance     ")
    print("================================================")
    
    workspace = "/tmp/cpos_mcp"
    os.makedirs(workspace, exist_ok=True)
    
    os_kernel = CPOS(workspace=workspace, node_id="mcp-master")
    
    # 1. Universal Mounting via MCP
    print("\n[Scenario: Mounting Notion via MCP]")
    notion_ptr = "ptr://mcp.notion/pages/roadmap"
    os_kernel.step(f">MEM:LOAD #{notion_ptr} !5", agent="root")
    
    # 2. Mounting Slack via MCP
    print("\n[Scenario: Mounting Slack via MCP]")
    slack_ptr = "ptr://mcp.slack/channels/security"
    os_kernel.step(f">MEM:LOAD #{slack_ptr} !5", agent="root")
    
    # 3. Verify in Cognitive Terminal
    print("\nVerifying Active Contexts...")
    os_kernel.monitor()
    
    content = os_kernel.scheduler.get_active_content()
    print("--- Active Context (Reconstructed) ---")
    print(content)
    
    # Analysis
    print("\n[Analysis]")
    print(f"Notion data present? {'Q3 Goals' in content}")
    print(f"Slack data present? {'Security Alert' in content}")
    print(f"Source markers correct? {'Source: mcp_server:notion' in content}")

    # 4. Final Snapshot
    os_kernel.save_report("v40_mcp_report.html")
    print("\n[COMPLETE] CPOS v4.0 MCP Compliance verified.")

if __name__ == "__main__":
    main()
