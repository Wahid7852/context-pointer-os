from typing import List, Optional
from .ait import AITInstruction, AITCodec
from .eap import EAPParser
from .context_store import ContextStore
from .registry import ContextRegistry
from .acl import AccessControlList, Role

class Scheduler:
    """The 'Process Manager'. Executes AIT/EAP instructions with ACL, heat, and kernel key."""
    def __init__(self, store: ContextStore, acl: Optional[AccessControlList] = None):
        self.store = store
        self.registry = store.registry
        self.acl = acl or AccessControlList()
        self.audit_log: List[dict] = []
        self.current_agent = "root"
        self.interrupt_queue: List[AITInstruction] = []

    def set_agent(self, agent_name: str):
        self.current_agent = agent_name

    def get_active_content(self) -> str:
        """Serializes active contexts with role-based redaction."""
        output = []
        role = self.acl.get_role(self.current_agent)
        for ctx_id, obj in self.store.active_contexts.items():
            content = f"[{ctx_id}: {obj.title}]\n{obj.summary}"
            if obj.data:
                data_to_show = obj.data
                if role == Role.GUEST and obj.type in ["persona", "neurostate"]:
                    data_to_show = "[REDACTED]"
                content += f"\nDATA: {data_to_show}"
            output.append(content)
        return "\n\n".join(output)

    def dispatch(self, instruction_input: str):
        # 0. Watchdog Check
        ns_obj = self.registry.get("ctx7")
        if ns_obj and ns_obj.data:
            import json
            try:
                ns_data = json.loads(ns_obj.data)
                if float(ns_data.get("corruption", 0)) > 0.8:
                    self.interrupt_queue.append(AITInstruction("neurostate", "ctx7", "write", 9, '{"calm": 0.5, "corruption": 0.0}'))
            except: pass

        while self.interrupt_queue:
            self.execute(self.interrupt_queue.pop(0), is_interrupt=True)

        instr = EAPParser.parse(instruction_input) if instruction_input.startswith('>') else AITCodec.decode(instruction_input)
        if not instr: return {"status": "error", "code": "ERR_UNKNOWN_INSTRUCTION"}
        return self.execute(instr)

    def execute(self, instr: AITInstruction, is_interrupt: bool = False):
        status = "ok"; result = None
        
        # 0. Heat Management & Cognitive Scheduling
        effective_priority = 9 if is_interrupt else instr.priority
        obj = self.registry.get(instr.target_id)
        
        if obj and instr.action in ["load", "write", "summarize"]:
            obj.access_heat += 1.0
            if obj.access_heat > 5.0 and instr.action != "summarize":
                effective_priority = max(1, effective_priority - 3) # Throttle

        # 1. Kernel Key & ACL Check
        if instr.action in ["write", "sync", "forget"] and instr.target_id == "ctx0":
            import re
            key_match = re.search(r'key=([a-zA-Z0-9-]+)', instr.metadata or "")
            if not key_match or not self.registry.verify_key(key_match.group(1)):
                status = "error"; result = "ERR_KERNEL_KEY_REQUIRED"
                self._log_audit(instr, status, result, effective_priority)
                return {"status": status, "result": result}

        if obj:
            if not self.acl.check(self.current_agent, instr.target_id, obj.type):
                status = "error"; result = "ERR_PERMISSION_DENIED"
                self._log_audit(instr, status, result, effective_priority)
                return {"status": status, "result": result}
        elif instr.action not in ["query", "send", "gc", "ls", "ps", "syscall", "device"]:
            status = "error"; result = "ERR_UNKNOWN_CTX"
            self._log_audit(instr, status, result, effective_priority)
            return {"status": status, "result": result}

        # 2. Action Execution
        if instr.action == "load": self.store.load(instr.target_id, effective_priority)
        elif instr.action == "unload": self.store.unload(instr.target_id)
        elif instr.action == "summarize":
            result = f"{instr.target_id}:sum -> {obj.summary}"
            obj.access_heat = max(0, obj.access_heat - 3.0)
        elif instr.action == "send":
            import re
            to_match = re.search(r'to=([a-zA-Z0-9_-]+)', instr.metadata or ""); body_match = re.search(r'body="([^"]+)"', instr.metadata or "")
            if to_match and body_match:
                recipient = to_match.group(1); body = body_match.group(1); msg_id = f"msg_{len(self.audit_log)}"
                from .registry import ContextObject
                msg_obj = ContextObject(id=msg_id, type="message", title=f"Msg", content_ref=f"internal://{msg_id}", summary=body, tokens_estimate=100, data=body)
                self.registry.register(msg_obj); self.acl.grant(recipient, msg_id); result = f"Message sent to {recipient} as {msg_id}"
            else: status = "error"; result = "ERR_INVALID_IPC_FORMAT"
        elif instr.action == "branch":
            suffix = instr.metadata if instr.metadata else "a"
            branch_obj = self.registry.branch(instr.target_id, suffix)
            if branch_obj: self.store.load(branch_id, effective_priority); result = f"Branched"
            else: status = "error"; result = "ERR_BRANCH_FAILED"
        elif instr.action == "merge":
            if not obj.parent: status = "error"; result = "ERR_NOT_A_BRANCH"
            else:
                p = self.registry.get(obj.parent)
                if p: p.data = obj.data; p.state.dirty = True; result = f"Merged"; self.store.unload(obj.id)
                else: status = "error"; result = "ERR_PARENT_NOT_FOUND"
        elif instr.action == "forget":
            self.store.unload(instr.target_id)
            if instr.target_id in self.registry.registry: del self.registry.registry[instr.target_id]
            result = "Forgotten"
        elif instr.action == "write":
            if instr.metadata:
                if obj.type == "neurostate":
                    import json
                    try: u = json.loads(instr.metadata)
                    except: u = {p.split('=')[0]: p.split('=')[1] for p in instr.metadata.split() if '=' in p}
                    d = json.loads(obj.data) if obj.data else {}
                    d.update(u); obj.data = json.dumps(d); result = "NS updated"
                else:
                    if '=' in instr.metadata: obj.data = instr.metadata.split('=',1)[1]; result = "Updated"
                    else: obj.data = instr.metadata; result = "Replaced"
            obj.state.dirty = True
        elif instr.action == "sync":
            if self.store.storage:
                targets = [obj] if instr.target_id != "ctx0" else list(self.registry.registry.values())
                for t in targets:
                    if t.state.dirty and t.data: self.store.storage.write(t.content_ref, str(t.data)); t.state.dirty = False
                result = "Synced"
            else: status = "error"; result = "ERR_NO_STORAGE"
        elif instr.action == "gc":
            targets = [t for t in list(self.registry.registry.keys()) if self.registry.registry[t].type == "message" or "." in t]
            for t in targets: self.store.unload(t); del self.registry.registry[t]
            result = "GC done"
        elif instr.action == "ls": result = "\n".join([f"{o.id} [{o.type}]" for o in self.registry.registry.values()])
        elif instr.action == "ps": result = "\n".join([f"{o.id} [{o.type}]" for o in self.store.active_contexts.values()])
        elif instr.action == "syscall":
            import re, os
            f = re.search(r'func=([a-z_]+)', instr.metadata or "")
            if f and f.group(1) == "listdir" and self.acl.get_role(self.current_agent) == Role.ROOT: result = str(os.listdir('.')[:5])
            else: status = "error"; result = "DENIED"
        elif instr.action == "device":
            import re
            m = re.search(r'mount=([a-z]+)', instr.metadata or ""); p = re.search(r'path=([^ ]+)', instr.metadata or "")
            if m and p and self.store.storage: self.store.storage.mount(m.group(1), p.group(1)); result = "Mounted"
            else: status = "error"; result = "FAILED"
                
        self._log_audit(instr, status, result, effective_priority)
        return {"status": status, "result": result}

    def _log_audit(self, instr, status, result, effective_priority=None):
        p = effective_priority if effective_priority is not None else instr.priority
        c = AITCodec.encode(instr.domain, instr.target_id, instr.action, p)
        self.audit_log.append({"agent": self.current_agent, "instr": c, "action": instr.action, "target": instr.target_id, "status": status, "result": result})
