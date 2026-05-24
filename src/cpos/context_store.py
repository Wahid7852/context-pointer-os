from typing import Dict, Optional
from .registry import ContextObject, ContextRegistry
from .storage import StorageManager

class ContextStore:
    """The 'RAM' of the OS. Manages currently loaded contexts for the LLM CPU."""
    def __init__(self, registry: ContextRegistry, storage: Optional[StorageManager] = None):
        self.registry = registry
        self.storage = storage
        self.active_contexts: Dict[str, ContextObject] = {}
        self.node = None # [CPOS v0.4] Reference to NodeLink
        self.gateways = None # [CPOS v0.4] Reference to GatewayManager

    def load(self, ctx_id: str, priority: int = 5, _seen: Optional[set] = None) -> bool:
        # [CPOS v0.4/v1.0] Handle Distributed or External Pointer URI
        if ctx_id.startswith("ptr://"):
            try:
                # [CPOS v1.0] MCP Protocol Support
                # Format: ptr://mcp.<server>/<path>
                if ctx_id.startswith("ptr://mcp.") and self.gateways:
                    parts = ctx_id[10:].split("/", 1)
                    server_id = parts[0]
                    path = parts[1] if len(parts) > 1 else ""
                    
                    # Route to the internal 'mcp' gateway
                    remote_obj = self.gateways.resolve("mcp", f"{server_id}/{path}")
                    if remote_obj:
                        self.registry.register(remote_obj)
                        ctx_id = remote_obj.id
                        print(f"--- [STORE] MCP Context {ctx_id} mounted via {server_id} ---")
                    else:
                        print(f"--- [STORE ERROR] Failed to resolve MCP context {ctx_id} ---")
                        return False

                # [CPOS v5.0] Environmental Awareness Support
                # Format: ptr://env.<category>/<sensor_id>
                elif ctx_id.startswith("ptr://env.") and self.gateways:
                    parts = ctx_id[10:].split("/", 1)
                    category = parts[0]
                    sensor = parts[1] if len(parts) > 1 else ""
                    
                    # Route to the internal 'env' gateway
                    remote_obj = self.gateways.resolve("env", f"{category}/{sensor}")
                    if remote_obj:
                        self.registry.register(remote_obj)
                        ctx_id = remote_obj.id
                        print(f"--- [STORE] Environmental Context {ctx_id} mounted ---")
                    else:
                        print(f"--- [STORE ERROR] Failed to resolve environmental context {ctx_id} ---")
                        return False

                # Format: ptr://ext.<gateway>/path (Generic Gateway)
                elif ctx_id.startswith("ptr://ext.") and self.gateways:
                    parts = ctx_id[10:].split("/", 1)
                    gateway_name = parts[0]
                    path = parts[1] if len(parts) > 1 else ""
                    
                    remote_obj = self.gateways.resolve(gateway_name, path)
                    if remote_obj:
                        self.registry.register(remote_obj)
                        ctx_id = remote_obj.id
                        print(f"--- [STORE] External context {ctx_id} loaded via {gateway_name} ---")
                    else:
                        print(f"--- [STORE ERROR] Failed to resolve external context {ctx_id} ---")
                        return False
                
                # [CPOS v8.0] Genetic Kernel: Source Code Support
                # Format: ptr://src.<path_to_file>
                elif ctx_id.startswith("ptr://src.") and self.gateways:
                    path = ctx_id[10:]
                    remote_obj = self.gateways.resolve("src", path)
                    if remote_obj:
                        self.registry.register(remote_obj)
                        ctx_id = remote_obj.id
                        print(f"--- [STORE] System source {ctx_id} mounted ---")
                    else:
                        print(f"--- [STORE ERROR] Failed to mount system source {ctx_id} ---")
                        return False

                # Format: ptr://node_addr/type/id (Kernel-to-Kernel)
                elif self.node:
                    parts = ctx_id[6:].split("/")
                    remote_addr, ctx_type, remote_id = parts
                    
                    # Check if we already have it in registry (cached metadata)
                    if not self.registry.get(remote_id):
                        # Fetch from remote node
                        remote_obj = self.node.fetch_remote_context(remote_addr, ctx_type, remote_id)
                        if remote_obj:
                            # Register locally (metadata and data)
                            if remote_obj.data:
                                remote_obj.state.loaded = True
                            self.registry.register(remote_obj)
                            print(f"--- [STORE] Remote pointer {ctx_id} registered locally ---")
                        else:
                            print(f"--- [STORE ERROR] Failed to fetch remote context {ctx_id} ---")
                            return False
                    
                    # Now that it's in registry, load it normally using the remote_id
                    ctx_id = remote_id 
            except Exception as e:
                print(f"--- [STORE ERROR] Pointer resolution failed: {str(e)} ---")
                return False

        obj = self.registry.get(ctx_id)
        if not obj:
            return False
        
        # Circular dependency protection
        if _seen is None: _seen = set()
        if ctx_id in _seen: return True
        _seen.add(ctx_id)

        # CPOS v0.1: Check pointer status
        if obj.status in ["invalidated", "deleted"]:
            print(f"Load Error: Cannot load pointer '{ctx_id}' with status '{obj.status}'.")
            if obj.replacement_pointer:
                print(f"Hint: Use replacement pointer '{obj.replacement_pointer}' instead.")
            return False

        if obj.status == "archived":
            print(f"Load Warning: Loading archived pointer '{ctx_id}'.")

        # 1. Handle Swap-In
        if obj.state.paged and self.storage and obj.swap_ref:
            content = self.storage.read(obj.swap_ref)
            if content:
                obj.data = content
                obj.state.paged = False
                print(f"Swap-In: {ctx_id} restored from .swap")

        # 2. Standard Load from storage
        # v2.0: For device types, we always reload to get fresh I/O results
        is_device = obj.type == "device" or (obj.content_ref and "://" in obj.content_ref)
        if (not obj.state.loaded or is_device) and self.storage and obj.content_ref:
            content = self.storage.read(obj.content_ref)
            if content:
                obj.data = content
                obj.state.loaded = True
        
        self.active_contexts[ctx_id] = obj

        # CPOS v0.2: Recursive Dependency Loading
        if hasattr(obj, 'dependencies') and obj.dependencies:
            for dep_id in obj.dependencies:
                # Load dependency with the same priority
                self.load(dep_id, priority=priority, _seen=_seen)

        return True

    def load_summary(self, ctx_id: str):
        obj = self.registry.get(ctx_id)
        if obj:
            obj.state.loaded = True
            obj.data = f"[SUMMARY ONLY] {obj.summary}"
            self.active_contexts[ctx_id] = obj

    def unload(self, ctx_id: str):
        if ctx_id in self.active_contexts:
            del self.active_contexts[ctx_id]

    def get_active_content(self) -> str:
        """Serializes all active contexts for the LLM prompt."""
        output = []
        for ctx_id, obj in self.active_contexts.items():
            content = f"[{ctx_id}: {obj.title}]\n{obj.summary}"
            if obj.data:
                content += f"\nRAW: {obj.data}"
            output.append(content)
        return "\n\n".join(output)
