import json
import uuid
import copy
from typing import Dict, Any, Optional, List
from .registry import ContextObject

class NodeLink:
    """[CPOS v0.4+] Inter-Node Communication Layer. Simulates distributed kernel connectivity."""
    
    def __init__(self, node_id: str, domain: str = "local"):
        self.node_id = node_id
        self.domain = domain
        self.full_address = f"{node_id}.{domain}"
        # Remote node registry: address -> NodeLink instance (simulated)
        self.peers: Dict[str, 'NodeLink'] = {}
        # [CPOS v0.4] Authenticated peers: address -> bool
        self.auth_nodes: Dict[str, bool] = {}
        # [CPOS v5.0] Peer Load tracking: address -> float (0.0 to 100.0)
        self.peer_loads: Dict[str, float] = {}
        # Local Kernel reference (assigned by CPOS)
        self.kernel = None

    def connect(self, peer: 'NodeLink'):
        """Establishes a physical connection to another node."""
        self.peers[peer.full_address] = peer
        peer.peers[self.full_address] = self
        print(f"--- [NODE] {self.full_address} connected to {peer.full_address} ---")

    def handshake(self, remote_addr: str, key: str) -> bool:
        """Performs a secure handshake with a remote node."""
        if remote_addr not in self.peers:
            return False
            
        peer = self.peers[remote_addr]
        print(f"--- [AUTH] {self.full_address} initiating handshake with {remote_addr} ---")
        
        # [CPOS v5.0] Report local load during handshake
        local_load = self._get_local_load()
        success = peer._handle_handshake_request(self.full_address, key, local_load)
        if success:
            self.auth_nodes[remote_addr] = True
            print(f"--- [AUTH] {self.full_address} authenticated by {remote_addr} ---")
        return success

    def _handle_handshake_request(self, requester_addr: str, key: str, requester_load: float = 0.0) -> bool:
        """Verifies an incoming handshake request."""
        if not self.kernel: return False
        
        # Verify the key (Simulated: in this prototype, any key > 8 chars is 'ok')
        if key and len(key) > 8:
            self.auth_nodes[requester_addr] = True
            self.peer_loads[requester_addr] = requester_load
            print(f"--- [AUTH] {self.full_address} granted access to {requester_addr} (Load: {requester_load}%) ---")
            return True
        return False

    def _get_local_load(self) -> float:
        """Simulates fetching current node load from Environmental Gateway."""
        if self.kernel and self.kernel.gateways:
            obj = self.kernel.gateways.resolve("env", "system/cpu_load")
            if obj and obj.data:
                try:
                    return float(obj.data.replace("CURRENT_VALUE: ", "").replace("%", ""))
                except: pass
        return 0.0

    def get_least_loaded_peer(self) -> Optional[str]:
        """[CPOS v5.0] Returns the address of the authenticated peer with the lowest load."""
        auth_peers = [addr for addr, is_auth in self.auth_nodes.items() if is_auth]
        if not auth_peers: return None
        
        # Sort by load
        sorted_peers = sorted(auth_peers, key=lambda x: self.peer_loads.get(x, 100.0))
        return sorted_peers[0]

    def fetch_remote_context(self, remote_addr: str, ctx_type: str, ctx_id: str) -> Optional[ContextObject]:
        """Fetches context metadata and data from a remote node. Requires handshake."""
        if remote_addr not in self.peers:
            print(f"--- [NODE ERROR] Peer {remote_addr} not reachable ---")
            return None
        
        if not self.auth_nodes.get(remote_addr):
            print(f"--- [AUTH ERROR] Peer {remote_addr} not authenticated. Call CONNECT first. ---")
            return None
            
        peer = self.peers[remote_addr]
        print(f"--- [NODE] {self.full_address} fetching {ctx_type}/{ctx_id} from {remote_addr} ---")
        
        return peer._handle_fetch_request(self.full_address, ctx_type, ctx_id)

    def query_remote_knowledge(self, remote_addr: str, query: str) -> List[Dict[str, Any]]:
        """Queries a remote node for context objects matching a semantic query."""
        if remote_addr not in self.peers or not self.auth_nodes.get(remote_addr):
            return []
        
        peer = self.peers[remote_addr]
        print(f"--- [DISCOVERY] {self.full_address} querying {remote_addr} for '{query}' ---")
        return peer._handle_query_request(self.full_address, query)

    def _handle_query_request(self, requester_addr: str, query: str) -> List[Dict[str, Any]]:
        """Handles an incoming semantic query request from a peer."""
        if not self.kernel or not self.auth_nodes.get(requester_addr):
            return []
        
        # Perform local semantic search
        matches = self.kernel.registry.semantic_search(query, limit=2)
        results = []
        for obj, score in matches:
            if obj.sensitivity_level in ["public", "internal"]:
                results.append({
                    "id": obj.id,
                    "type": obj.type,
                    "title": obj.title,
                    "summary": obj.summary,
                    "score": score,
                    "ptr_uri": f"ptr://{self.full_address}/{obj.type}/{obj.id}"
                })
        return results

    def _handle_fetch_request(self, requester_addr: str, ctx_type: str, ctx_id: str) -> Optional[ContextObject]:
        """Handles an incoming request for context."""
        if not self.kernel:
            return None
        
        # Check authentication
        if not self.auth_nodes.get(requester_addr):
            print(f"--- [AUTH ERROR] Unauthenticated access from {requester_addr} blocked ---")
            return None

        obj = self.kernel.registry.get(ctx_id)
        if not obj or obj.type != ctx_type:
            return None
        
        # [CPOS v0.4] Ensure data is loaded before sending to peer
        if not obj.data and obj.content_ref:
            self.kernel.store.load(ctx_id)
        
        # Check sensitivity
        if obj.sensitivity_level in ["private", "restricted"]:
            print(f"--- [SECURITY] Remote access denied for {requester_addr} to {ctx_id} ---")
            return None
            
        return copy.deepcopy(obj)

    def broadcast_invalidation(self, ctx_id: str, reason: str, skip_addr: Optional[str] = None):
        """Notifies all peers that a pointer is no longer valid."""
        for addr, peer in self.peers.items():
            if addr == skip_addr: continue
            peer._handle_invalidation_notice(self.full_address, ctx_id, reason)

    def _handle_invalidation_notice(self, sender_addr: str, ctx_id: str, reason: str):
        """Reacts to remote invalidation."""
        if not self.kernel: return
        
        # If we have a local copy or reference to this remote pointer, invalidate it
        obj = self.kernel.registry.get(ctx_id)
        if obj and obj.status != "invalidated":
            print(f"--- [NODE] {self.full_address} received invalidation for {ctx_id} from {sender_addr} (Reason: {reason}) ---")
            # Invalidate locally without re-broadcasting back to the sender
            self.kernel.registry.invalidate(ctx_id, f"Remote Invalidation from {sender_addr}: {reason}", skip_broadcast_addr=sender_addr)
            # Also unload from RAM if active
            self.kernel.store.unload(ctx_id)
