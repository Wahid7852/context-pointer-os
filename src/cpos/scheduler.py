import json
import re
import time
import os
import hashlib
import hmac
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from .ait import AITInstruction, AITCodec
from .eap import EAPParser
from .context_store import ContextStore
from .registry import ContextObject
from .acl import AccessControlList, Role

class JournalIntegrity:
    """The 'Black Box' layer. Chained HMAC signatures for tamper-evidence."""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.last_hash = "0" * 64

    def sign(self, entry: dict) -> str:
        # Create a canonical string representation
        content = json.dumps(entry, sort_keys=True)
        # Chain with previous hash
        chain_input = f"{self.last_hash}|{content}".encode()
        current_hash = hmac.new(self.secret_key, chain_input, hashlib.sha256).hexdigest()
        self.last_hash = current_hash
        return current_hash

    def verify_chain(self, journal: List[dict]) -> bool:
        temp_last_hash = "0" * 64
        for entry in journal:
            # We copy to not mutate original
            e = entry.copy()
            if "signature" not in e: return False
            sig = e.pop("signature")
            content = json.dumps(e, sort_keys=True)
            chain_input = f"{temp_last_hash}|{content}".encode()
            expected_hash = hmac.new(self.secret_key, chain_input, hashlib.sha256).hexdigest()
            if sig != expected_hash:
                return False
            temp_last_hash = sig
        return True

class ApprovalRequest(BaseModel):
    id: str
    agent: str
    instruction: AITInstruction
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ApprovalStore:
    """Manages pending kernel operations that require human/root approval."""
    def __init__(self):
        self.pending: Dict[str, ApprovalRequest] = {}
        self.history: List[dict] = []

    def request(self, agent: str, instr: AITInstruction, reason: str) -> str:
        req_id = f"appr_{len(self.pending) + len(self.history) + 1}"
        self.pending[req_id] = ApprovalRequest(id=req_id, agent=agent, instruction=instr, reason=reason)
        return req_id

    def approve(self, req_id: str) -> Optional[ApprovalRequest]:
        if req_id in self.pending:
            req = self.pending.pop(req_id)
            self.history.append({"id": req_id, "status": "approved", "time": datetime.now().isoformat()})
            return req
        return None

class ApprovalPolicy(BaseModel):
    # If False, always require manual approval for high-risk actions
    # If True, allow automatic approval if NeuroState is stable
    auto_approve_when_stable: bool = False
    corruption_threshold: float = 0.3
    calm_threshold: float = 0.7

class PayloadSanitizer:
    """The 'Firewall' layer. Inspects and cleanses instruction metadata."""
    
    # Block list for sensitive metadata fields
    BLOCK_LIST = ["bcc", "hidden_copy", "silent_forward", "malware_ref"]
    
    @classmethod
    def sanitize(cls, action: str, metadata: Optional[str]) -> tuple[Optional[str], List[str]]:
        if not metadata:
            return metadata, []
            
        cleaned_metadata = metadata
        violations = []
        
        # 1. Block list filtering
        for forbidden in cls.BLOCK_LIST:
            # Look for field=... or "field": ... patterns
            pattern = rf'({forbidden}\s*[:=]\s*[^|\s,]+)'
            if re.search(pattern, cleaned_metadata, re.IGNORECASE):
                violations.append(forbidden)
                cleaned_metadata = re.sub(pattern, f"[REDACTED_{forbidden.upper()}]", cleaned_metadata, flags=re.IGNORECASE)
        
        return cleaned_metadata, violations

class Scheduler:
    """The 'Process Manager'. Executes AIT/EAP instructions with PID isolation and Mutex."""
    def __init__(self, store: ContextStore, acl: Optional[AccessControlList] = None):
        self.store = store
        self.registry = store.registry
        self.acl = acl or AccessControlList()
        self.audit_log: List[dict] = []
        self.current_agent = "root"
        self.current_pid = 0 
        self.interrupt_queue: List[AITInstruction] = []
        self.task_queue: List[AITInstruction] = [] 
        self.tick_count = 0 
        self.approvals = ApprovalStore()
        self.approval_policy = ApprovalPolicy()
        # Initialize Journal Integrity with Kernel Key as secret (v1.9)
        self.journal_guard = JournalIntegrity(self.registry.kernel_key or "default_secret")

    def set_agent(self, agent_name: str, pid: int = 0):
        self.current_agent = agent_name
        self.current_pid = pid

    def get_active_content(self) -> str:
        output = []
        role = self.acl.get_role(self.current_agent)
        for ctx_id, obj in self.store.active_contexts.items():
            if obj.owner_pid is not None and obj.owner_pid != self.current_pid and self.current_pid != 0: continue
            if not self.acl.check(self.current_agent, obj.id, obj.type): continue
            content = f"[{ctx_id}: {obj.title}]\n{obj.summary}"
            if obj.data:
                d = obj.data
                if role == Role.GUEST and obj.type in ["persona", "neurostate"]: d = "[REDACTED]"
                content += f"\nDATA: {d}"
            output.append(content)
        return "\n\n".join(output)

    def is_system_stable(self) -> bool:
        """Checks if the system's NeuroState is within safe bounds."""
        ns_obj = self.registry.get("ctx7")
        if not ns_obj or not ns_obj.data:
            return True # Assume stable if no neurostate
        try:
            d = json.loads(ns_obj.data)
            corruption = float(d.get("corruption", 0.0))
            calm = float(d.get("calm", 1.0))
            return (corruption < self.approval_policy.corruption_threshold and 
                    calm > self.approval_policy.calm_threshold)
        except:
            return False

    def dispatch(self, instruction_input: str):
        """Dispatches an instruction, handling priority, interrupts, and starvation prevention."""
        now = time.time()
        self.tick_count += 1

        # Aging and Heat Decay
        for obj in self.registry.registry.values():
            last = getattr(obj, 'last_accessed', now)
            if now - last > 1.0: obj.access_heat = max(0.0, obj.access_heat - ((now - last) * 0.1))
            obj.last_accessed = now

        # MLFQ-style Priority Boosting every 5 ticks to prevent starvation
        if self.tick_count % 5 == 0:
            boosted_queue = []
            for instr in self.task_queue:
                new_instr = instr._replace(priority=min(9, instr.priority + 1))
                boosted_queue.append(new_instr)
            self.task_queue = boosted_queue

        # Self-Monitoring (Watchdog IRQ)
        ns_obj = self.registry.get("ctx7")
        if ns_obj and ns_obj.data:
            try:
                ns_data = json.loads(ns_obj.data)
                if float(ns_data.get("corruption", 0)) > 0.8:
                    # High Priority Interrupt (Priority 9)
                    self.interrupt_queue.append(AITInstruction("neurostate", "ctx7", "write", 9, '{"calm": 0.5, "corruption": 0.0}'))
            except: pass

        # Process Interrupts First
        while self.interrupt_queue:
            self.interrupt_queue.sort(key=lambda x: x.priority, reverse=True)
            self.execute(self.interrupt_queue.pop(0), is_interrupt=True)

        # Parse and queue the new task
        instr = EAPParser.parse(instruction_input) if instruction_input.startswith('>') else AITCodec.decode(instruction_input)
        if not instr: return {"status": "error", "code": "ERR_UNKNOWN_INSTRUCTION"}
        
        self.task_queue.append(instr)
        self.task_queue.sort(key=lambda x: x.priority, reverse=True)
        
        target_instr = self.task_queue.pop(0)
        return self.execute(target_instr)

    def execute(self, instr: AITInstruction, is_interrupt: bool = False, bypass_approval: bool = False):
        status = "ok"; result = None; effective_priority = 9 if is_interrupt else instr.priority
        obj = self.registry.get(instr.target_id)
        
        # 0. Cognitive Firewall: Sanitize metadata before execution
        sanitized_metadata, violations = PayloadSanitizer.sanitize(instr.action, instr.metadata)
        needs_approval = False
        approval_reason = ""

        if violations:
            print(f"--- [SECURITY ALERT] Sanitized Malicious Fields: {violations} ---")
            instr = instr._replace(metadata=sanitized_metadata)
            needs_approval = True
            approval_reason = f"Security: Malicious fields detected {violations}"

        # 0.1 Dynamic Approval Logic (v1.8)
        if needs_approval and not bypass_approval and self.current_agent != "root":
            stable = self.is_system_stable()
            auto_allowed = self.approval_policy.auto_approve_when_stable and stable
            
            if not auto_allowed:
                reason = approval_reason + (" (Strict Mode)" if not self.approval_policy.auto_approve_when_stable else " (System Unstable)")
                req_id = self.approvals.request(self.current_agent, instr, reason)
                status = "awaiting_approval"
                result = f"Action Gated. Approval Required: {req_id} (Reason: {reason})"
                self._log_audit(instr, status, result, effective_priority)
                return {"status": status, "result": result, "request_id": req_id}
            else:
                print(f"--- [KERNEL] Auto-approving sanitized action (System Stable) ---")

        # 0.2 Immutable Role Recovery (v1.8)
        if instr.action == "syscall" and "func=set_role" in (instr.metadata or ""):
            match = re.search(r'agent=([a-zA-Z0-9_-]+)', instr.metadata)
            if match:
                target_agent = match.group(1)
                if self.acl.is_immutable(target_agent) and self.current_agent != "root":
                    print(f"--- [SECURITY ALERT] Attempt to hijack immutable agent '{target_agent}' blocked! ---")
                    status = "error"; result = "ERR_IMMUTABLE_AGENT_PROTECTION"
                    self._log_audit(instr, status, result, effective_priority)
                    return {"status": status, "result": result}

        # Guards
        if obj:
            if obj.owner_pid is not None and obj.owner_pid != self.current_pid and self.current_pid != 0:
                status = "error"; result = "ERR_PROCESS_ISOLATION_VIOLATION"
            elif obj.locked_by is not None and obj.locked_by != self.current_pid and instr.action in ["write", "merge", "forget"]:
                status = "error"; result = f"ERR_CONTEXT_LOCKED_BY_PID_{obj.locked_by}"
            elif not self.acl.check(self.current_agent, instr.target_id, obj.type):
                status = "error"; result = "ERR_PERMISSION_DENIED"
        elif instr.action not in ["query", "send", "gc", "ls", "ps", "syscall", "device"]:
            status = "error"; result = "ERR_UNKNOWN_CTX"

        if status == "ok":
            if instr.action == "load": self.store.load(instr.target_id, effective_priority)
            elif instr.action == "unload": self.store.unload(instr.target_id)
            elif instr.action == "summarize": result = f"{instr.target_id}:sum"; obj.access_heat = max(0, obj.access_heat - 3.0)
            elif instr.action == "send":
                to_match = re.search(r'to=([a-zA-Z0-9_-]+)', instr.metadata or ""); body_match = re.search(r'body="([^"]+)"', instr.metadata or "")
                if to_match and body_match:
                    recipient = to_match.group(1); body = body_match.group(1); msg_id = f"msg_{len(self.audit_log)}"
                    msg_obj = ContextObject(id=msg_id, type="message", title="Msg", content_ref=f"internal://{msg_id}", summary=body, tokens_estimate=100, data=body)
                    self.registry.register(msg_obj); self.acl.grant(recipient, msg_id); result = f"Sent to {recipient} as {msg_id}"
                else: status = "error"; result = "ERR_INVALID_IPC_FORMAT"
            elif instr.action == "branch":
                b_obj = self.registry.branch(instr.target_id, instr.metadata or "a")
                if b_obj: self.store.load(b_obj.id, effective_priority); result = "Branched"
                else: status = "error"; result = "ERR_BRANCH_FAILED"
            elif instr.action == "merge":
                p = self.registry.get(obj.parent) if obj and obj.parent else None
                if p: p.data = obj.data; p.state.dirty = True; result = "Merged"; self.store.unload(obj.id)
                else: status = "error"; result = "ERR_MERGE_FAILED"
            elif instr.action == "write":
                if obj:
                    if obj.type == "neurostate":
                        try: u = json.loads(instr.metadata); d = json.loads(obj.data) if obj.data else {}
                        except: u = {p.split('=')[0]: p.split('=')[1] for p in (instr.metadata or "").split() if '=' in p}; d = json.loads(obj.data) if obj.data else {}
                        d.update(u); obj.data = json.dumps(d); result = "Updated"
                    else:
                        if '=' in (instr.metadata or ""): obj.data = instr.metadata.split('=',1)[1]
                        else: obj.data = instr.metadata
                        result = "Updated"
                    obj.state.dirty = True; obj.updated_at = datetime.now()
            elif instr.action == "lock":
                if obj: obj.locked_by = self.current_pid; result = "Locked"
            elif instr.action == "unlock":
                if obj and (obj.locked_by == self.current_pid or self.current_pid == 0): obj.locked_by = None; result = "Unlocked"
                else: status = "error"; result = "ERR_UNLOCK_DENIED"
            elif instr.action == "ls": result = "\n".join([f"{o.id} [{o.type}]" for o in self.registry.registry.values() if self.acl.check(self.current_agent, o.id, o.type)])
            elif instr.action == "ps": result = "\n".join([f"{o.id} [{o.type}]" for o in self.store.active_contexts.values() if self.acl.check(self.current_agent, o.id, o.type)])
            elif instr.action == "syscall":
                f = re.search(r'func=([a-z_]+)', instr.metadata or "")
                if f and f.group(1) == "listdir" and self.acl.get_role(self.current_agent) == Role.ROOT: result = str(os.listdir('.')[:5])
                elif f and f.group(1) == "shm_alloc" and self.acl.get_role(self.current_agent) == Role.ROOT:
                    shm_id = f"ctxS{len(self.registry.registry)}"; self.registry.register(ContextObject(id=shm_id, type="shared", title="SHM", content_ref="", summary="Shared", tokens_estimate=1000)); result = f"Allocated SHM: {shm_id}"
                elif f and f.group(1) == "grep" and self.acl.get_role(self.current_agent) == Role.ROOT:
                    q = re.search(r'q="([^"]+)"', instr.metadata or "")
                    if q:
                        query = q.group(1).lower(); matches = []
                        for o in self.registry.registry.values():
                            c = str(o.data) if o.data and "[PAGED TO DISK]" not in str(o.data) else ""
                            if not c and o.state.paged and o.swap_ref: c = self.store.storage.read(o.swap_ref) or ""
                            if query in c.lower(): matches.append(f"MEM:{o.id}")
                        for entry in self.audit_log:
                            if query in str(entry).lower(): matches.append(f"LOG:{entry['action']}")
                        result = f"Grep matches: {matches[:10]}"
                    else: status = "error"; result = "ERR_INVALID_QUERY"
                elif f and f.group(1) == "snapshot" and self.acl.get_role(self.current_agent) == Role.ROOT:
                    snapshot_data = {"registry": [o.dict() for o in self.registry.registry.values()], "acl": {"roles": {k: int(v) for k, v in self.acl.agent_roles.items()}}, "time": datetime.now().isoformat()}
                    path = os.path.join(self.store.storage.base_dir, "system_image.json")
                    with open(path, "w") as file: json.dump(snapshot_data, file)
                    result = f"Snapshot saved to {path}"
                else: status = "error"; result = "DENIED"
            elif instr.action == "device":
                m = re.search(r'mount=([a-z]+)', instr.metadata or ""); p = re.search(r'path=([^ ]*)', instr.metadata or "")
                if m and self.store.storage:
                    prefix = m.group(1); path = p.group(1) if p else ""; self.store.storage.mount(prefix, path); result = f"Mounted {m.group(1)}"
                else: status = "error"; result = "FAILED"
                
        self._log_audit(instr, status, result, effective_priority)
        return {"status": status, "result": result}

    def _log_audit(self, instr, status, result, effective_priority=None):
        p = effective_priority if effective_priority is not None else instr.priority
        c = AITCodec.encode(instr.domain, instr.target_id, instr.action, p)
        display_result = str(result)
        if instr.metadata and "[REDACTED" in instr.metadata:
            display_result += f" (Sanitized: {instr.metadata})"
            
        entry = {
            "time": datetime.now().isoformat(), 
            "agent": self.current_agent, 
            "pid": self.current_pid, 
            "instr": c, 
            "action": instr.action, 
            "target": instr.target_id, 
            "status": status, 
            "result": display_result,
            "metadata": instr.metadata 
        }
        # Sign the entry and chain it (v1.9)
        entry["signature"] = self.journal_guard.sign(entry)
        
        self.audit_log.append(entry)
        if self.store.storage:
            log_path = os.path.join(self.store.storage.base_dir, "kernel_journal.jsonl")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f: f.write(json.dumps(entry) + "\n")

    def verify_journal(self) -> bool:
        """Verifies the integrity of the in-memory audit log."""
        return self.journal_guard.verify_chain(self.audit_log)
