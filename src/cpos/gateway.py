import json
import uuid
from typing import Dict, Any, Optional, List
from .registry import ContextObject
from .storage import DeviceDriver

class ExternalGateway(DeviceDriver):
    """Base class for [CPOS v0.4+] Cognitive Gateways. 
    Bridges external systems (APIs, DBs) into the CPOS pointer space."""
    
    def fetch_object(self, path: str) -> Optional[ContextObject]:
        """Fetches metadata and data, converting it to a ContextObject."""
        return None

class MockGitHubGateway(ExternalGateway):
    """Simulated GitHub Gateway for CPOS demonstration."""
    
    def fetch_object(self, path: str) -> Optional[ContextObject]:
        # path format: kagioneko/context-pointer-os/issues/1
        parts = path.split("/")
        if len(parts) < 3: return None
        
        issue_id = parts[-1]
        repo = "/".join(parts[:-2])
        
        return ContextObject(
            id=f"gh_issue_{issue_id}",
            type="code",
            title=f"GitHub Issue #{issue_id} in {repo}",
            summary=f"Bug report from external source: {repo}",
            data=f"DATA: Fix the recursive loading bug in the storage layer. (Fetched from GitHub API)",
            source=f"github_api:{repo}",
            trust_score=0.95,
            sensitivity_level="public"
        )

class MCPGateway(ExternalGateway):
    """[CPOS v1.0] Model Context Protocol (MCP) Bridge. 
    Standardizes connections to world-wide MCP compliant servers."""
    
    def fetch_object(self, path: str) -> Optional[ContextObject]:
        # path format: <server_id>/<resource_uri>
        # e.g., notion/pages/123
        parts = path.split("/", 1)
        if len(parts) < 2: return None
        
        server_id = parts[0]
        resource_uri = parts[1]
        
        # Simulated MCP Server Response
        mcp_data = {
            "notion": {
                "title": "Project Roadmap",
                "summary": "Internal roadmap fetched via MCP",
                "data": "Q3 Goals: Scale to 1M pointers. Q4: Neural Integration."
            },
            "slack": {
                "title": "Slack Thread: Security Alert",
                "summary": "Recent incident discussion",
                "data": "Agent 7 reported a suspicious syscall attempt at 10:45 AM."
            }
        }
        
        res = mcp_data.get(server_id, {
            "title": f"MCP Resource: {resource_uri}",
            "summary": f"Data from MCP server '{server_id}'",
            "data": f"RAW_DATA_FROM_{server_id.upper()}_{resource_uri}"
        })
        
        return ContextObject(
            id=f"mcp_{server_id}_{str(uuid.uuid4())[:8]}",
            type="mcp_resource",
            title=res["title"],
            summary=res["summary"],
            data=res["data"],
            source=f"mcp_server:{server_id}",
            trust_score=1.0, # MCP is highly trusted
            sensitivity_level="internal",
            metadata={"mcp_uri": resource_uri}
        )

class GatewayManager:
    """The 'Bridge Controller'. Manages external cognitive gateways."""
    
    def __init__(self):
        self.gateways: Dict[str, ExternalGateway] = {
            "github": MockGitHubGateway(),
            "mcp": MCPGateway() # [CPOS v1.0] MCP Support
        }

    def register_gateway(self, name: str, gateway: ExternalGateway):
        self.gateways[name] = gateway
        print(f"--- [GATEWAY] Registered Cognitive Gateway: {name} ---")

    def resolve(self, gateway_name: str, path: str) -> Optional[ContextObject]:
        """Resolves an external path to a ContextObject using the registered gateway."""
        if gateway_name in self.gateways:
            print(f"--- [GATEWAY] Resolving {path} via {gateway_name} ---")
            return self.gateways[gateway_name].fetch_object(path)
        return None
