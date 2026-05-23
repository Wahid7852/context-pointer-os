import json
from typing import Dict, Any, Optional, List
from .registry import ContextObject
from .storage import DeviceDriver

class ExternalGateway(DeviceDriver):
    """Base class for [CPOS v0.4] Cognitive Gateways. 
    Bridges external systems (APIs, DBs) into the CPOS pointer space."""
    
    def fetch_object(self, path: str) -> Optional[ContextObject]:
        """Fetches metadata and data, converting it to a ContextObject."""
        return None

class MockGitHubGateway(ExternalGateway):
    """Simulated GitHub Gateway for CPOS v0.4 demonstration."""
    
    def fetch_object(self, path: str) -> Optional[ContextObject]:
        # path format: kagioneko/context-pointer-os/issues/1
        parts = path.split("/")
        if len(parts) < 3: return None
        
        issue_id = parts[-1]
        repo = "/".join(parts[:-2])
        
        # Simulated API response
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

class GatewayManager:
    """The 'Bridge Controller'. Manages external cognitive gateways."""
    
    def __init__(self):
        self.gateways: Dict[str, ExternalGateway] = {
            "github": MockGitHubGateway()
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
