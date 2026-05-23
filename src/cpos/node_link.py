import json
import uuid
import copy
from typing import Dict, Any, Optional, List
from .registry import ContextObject

class NodeLink:
    """[CPOS v0.4] Inter-Node Communication Layer. Simulates distributed kernel connectivity."""
    
    def __init__(self, node_id: str, domain: str = "local"):
        self.node_id = node_id
        self.domain = domain
        self.full_address = f"{node_id}.{domain}"
        # Remote node registry: address -> NodeLink instance (simulated)
        self.peers: Dict[str, 'NodeLink'] = {}
        # [CPOS v0.4] Authenticated peers: address -> bool
        self.auth_nodes: Dict[str, bool] = {}
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
        
        # In a real system, this would be an encrypted challenge-response
        success = peer._handle_handshake_request(self.full_address, key)
        if success:
            self.auth_nodes[remote_addr] = True
            print(f"--- [AUTH] {self.full_address} authenticated by {remote_addr} ---")
        return success

    def _handle_handshake_request(self, requester_addr: str, key: str) -> bool:
        """Verifies an incoming handshake request."""
        if not self.kernel: return False
        
        # Verify the key (Simulated: in this prototype, any key > 8 chars is 'ok')
        if key and len(key) > 8:
            self.auth_nodes[requester_addr] = True
            print(f"--- [AUTH] {self.full_address} granted access to {requester_addr} ---")
            return True
        return False

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
        
        # Check sensitivity (Deny private/restricted to remote nodes in this prototype)
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
