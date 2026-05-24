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
from .memory_policy import RetrievalPolicy, CognitiveMode

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
        self.retrieval_policy = RetrievalPolicy() # CPOS v0.1 Governance
        # [CPOS v0.6] Neural Prediction: History and Transition Matrix
        self.cognitive_history: List[str] = [] # Last loaded context IDs
        self.transition_matrix: Dict[str, Dict[str, int]] = {} # id -> {next_id: frequency}
        # [CPOS v2.0] Persona Management
        self.current_persona: Optional[str] = None
        # Initialize Journal Integrity with Kernel Key as secret (v1.9)
        self.journal_guard = JournalIntegrity(self.registry.kernel_key or "default_secret")

    def set_agent(self, agent_name: str, pid: int = 0):
        self.current_agent = agent_name
        self.current_pid = pid

    def get_active_content(self) -> str:
        """[CPOS v0.2] Context Reconstructor: Smartly assembles active contexts."""
        output = []
        role = self.acl.get_role(self.current_agent)
        if self.current_agent == "root": role = Role.ROOT # Hardcoded root bypass
        
        # Sensitivity mapping for comparison
        SENSITIVITY_RANK = {"public": 0, "internal": 1, "private": 2, "restricted": 3}
        max_allowed_rank = SENSITIVITY_RANK.get(self.retrieval_policy.max_sensitivity_allowed, 1)
        if role == Role.ROOT: max_allowed_rank = 3 # Root can see everything

        # Prepare contexts for prioritization
        eligible_contexts = []
        for ctx_id, obj in self.store.active_contexts.items():
            if obj.type not in self.retrieval_policy.allowed_context_types and role != Role.ROOT:
                continue
            if not self.acl.check(self.current_agent, obj.id, obj.type): continue
            eligible_contexts.append(obj)

        # 1. Trust-based Prioritization (Higher trust/importance first)
        eligible_contexts.sort(key=lambda x: (x.trust_score * 0.6 + x.importance * 0.4), reverse=True)

        # 2. Conflict Detection (Simple ID-based sibling check)
        active_ids = {obj.id for obj in eligible_contexts}
        conflicts = []

        for obj in eligible_contexts:
            # Check for parent/branch loading which might cause redundancy/conflict
            if obj.parent and obj.parent in active_ids:
                conflicts.append(f"WARNING: Both parent '{obj.parent}' and branch '{obj.id}' are active. Information may overlap.")

            # Governance: Trust Score Filter
            if obj.trust_score < self.retrieval_policy.minimum_trust_score and role != Role.ROOT:
                output.append(f"[{obj.id}: {obj.title}] (Status: {obj.status})\n[FILTERED] Trust Score {obj.trust_score} below threshold.")
                continue

            # Governance: Sensitivity Check
            obj_rank = SENSITIVITY_RANK.get(obj.sensitivity_level, 1)
            
            # 3. Source Attribution & Status Metadata
            header = f"[{obj.id}: {obj.title}]"
            meta = f"Type: {obj.type} | Trust: {obj.trust_score} | Source: {obj.source} | Status: {obj.status}"
            if obj.status == "stale":
                meta += " (ATTENTION: Information is stale and may need re-validation)"
            
            content = f"{header}\n{meta}\nSummary: {obj.summary}"
            
            if obj.data:
                d = obj.data
                # Redact based on Role + Sensitivity
                if obj_rank > max_allowed_rank:
                    d = f"[REDACTED: Sensitivity Level '{obj.sensitivity_level}' exceeds current policy]"
                elif role == Role.GUEST and obj.type in ["persona", "neurostate"]:
                    d = "[REDACTED: Restricted to Guest Role]"
                
                content += f"\nDATA: {d}"
            
            output.append(content)
            
            # Audit log for retrieval (if enabled)
            if self.retrieval_policy.audit_required:
                self.registry._log_event("context_retrieval", obj.id, {"agent": self.current_agent, "role": str(role)})

        final_output = "\n\n".join(output)
        if self.current_persona:
            final_output = f"--- ACTIVE PERSONA: {self.current_persona} ---\n\n" + final_output
            
        if conflicts:
            final_output = "--- SYSTEM CONTEXT WARNINGS ---\n" + "\n".join(conflicts) + "\n\n" + final_output
            
        return final_output

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
        """Dispatches an instruction, handling priority, interrupts, and [v0.2] lifecycle decay."""
        now = time.time()
        self.tick_count += 1

        # Aging, Heat Decay and Lifecycle Management (v0.2)
        for obj in self.registry.registry.values():
            # Heat decay
            last = getattr(obj, 'last_accessed', now)
            if now - last > 1.0: 
                obj.access_heat = max(0.0, obj.access_heat - ((now - last) * 0.1))
            
            # Lifecycle: active -> stale
            if obj.status == "active" and obj.access_heat < 0.1:
                # For demo purposes, we simulate decay faster (every 10 ticks)
                if self.tick_count % 10 == 0:
                    obj.status = "stale"
                    self.registry._log_event("lifecycle_decay", obj.id, {"from": "active", "to": "stale"})

            obj.last_accessed = now

        # [CPOS v0.5] Autonomous Mode: Auto-validation
        if self.retrieval_policy.mode == CognitiveMode.AUTONOMOUS:
            self._auto_validate()

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

    def _auto_validate(self):
        """[CPOS v0.5] Autonomous self-healing memory."""
        for obj in self.registry.registry.values():
            if obj.status == "stale":
                # Attempt to re-validate via original source if it was an external gateway
                if obj.source and (obj.source.startswith("github_api") or obj.source == "external_db"):
                    print(f"--- [AUTO] Self-healing stale context: {obj.id} ---")
                    obj.status = "active"
                    obj.trust_score = min(1.0, obj.trust_score + 0.05)
                    self.registry._log_event("auto_validation", obj.id, {"status": "restored"})

    def _prefetch(self, target_id: str):
        """[CPOS +v0.6] Enhanced Neural prefetching."""
        target = self.registry.get(target_id)
        if not target: return
        
        prefetch_candidates = []
        
        # 1. Neural Prediction (v0.6): Predict based on history
        if self.cognitive_history:
            last_id = self.cognitive_history[-1]
            if last_id in self.transition_matrix:
                # Find the most frequent successors
                predictions = self.transition_matrix[last_id]
                sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
                for pred_id, freq in sorted_preds[:2]: # Top 2 predicted
                    if freq >= 2: # Only if pattern has occurred at least twice
                        prefetch_candidates.append(pred_id)
                        print(f"--- [NEURAL] Predicted next load: {pred_id} (pattern frequency: {freq}) ---")

        # 2. Heuristic Prefetch (v0.5)
        if target.branches: prefetch_candidates.extend(target.branches[:1])
        if target.type == "spec":
            base_name = target_id.replace("ctx_spec_", "").replace("spec_", "").replace("ctx_", "")
            for obj in self.registry.registry.values():
                if obj.type == "code" and base_name in obj.id.lower(): prefetch_candidates.append(obj.id)
                    
        for cid in prefetch_candidates:
            if cid not in self.store.active_contexts and cid != target_id:
                print(f"--- [PREDICTIVE] Prefetching candidate: {cid} ---")
                self.store.load(cid, priority=1)

    def execute(self, instr: AITInstruction, is_interrupt: bool = False, bypass_approval: bool = False):
        status = "ok"; result = None; effective_priority = 9 if is_interrupt else (instr.priority if instr else 5)
        obj = self.registry.get(instr.target_id) if instr else None
        
        # [CPOS v0.6] Track cognitive history for neural prediction
        if instr.action == "load":
            if self.cognitive_history:
                prev = self.cognitive_history[-1]
                if prev != instr.target_id:
                    if prev not in self.transition_matrix: self.transition_matrix[prev] = {}
                    self.transition_matrix[prev][instr.target_id] = self.transition_matrix[prev].get(instr.target_id, 0) + 1
            self.cognitive_history.append(instr.target_id)
            if len(self.cognitive_history) > 20: self.cognitive_history.pop(0)

        # 0. Cognitive Firewall, Approval, Guards...
        # [Simplified for visibility, keeping previous logic intact]
        sanitized_metadata, violations = PayloadSanitizer.sanitize(instr.action, instr.metadata)
        needs_approval = False
        approval_reason = ""
        if violations:
            instr = instr._replace(metadata=sanitized_metadata)
            needs_approval = True
            approval_reason = f"Security: Malicious fields detected {violations}"
        if needs_approval and not bypass_approval and self.current_agent != "root":
            if not self.is_system_stable():
                req_id = self.approvals.request(self.current_agent, instr, approval_reason)
                status = "awaiting_approval"; result = f"Gated: {req_id}"; self._log_audit(instr, status, result, effective_priority)
                return {"status": status, "result": result, "request_id": req_id}

        if obj:
            # [CPOS v0.7] Real-time Heat Tracking: Increase heat upon access
            obj.access_heat = min(10.0, obj.access_heat + 1.0)
            if not self.acl.check(self.current_agent, instr.target_id, obj.type): status = "error"; result = "ERR_PERMISSION_DENIED"
        elif instr.action not in ["query", "send", "gc", "ls", "ps", "syscall", "device", "policy", "load", "connect", "mode"]:
            status = "error"; result = "ERR_UNKNOWN_CTX"

        if status == "ok":
            if instr.action == "load":
                if not self.store.load(instr.target_id, effective_priority): status = "error"; result = "ERR_LOAD_FAILED"
                else:
                    if self.retrieval_policy.mode == CognitiveMode.PREDICTIVE: self._prefetch(instr.target_id)
                    # [CPOS v2.0] Persona Swap: If domain is PER, update current persona
                    if instr.domain == "persona":
                        self.current_persona = instr.target_id
                        result = f"Persona swapped to {instr.target_id}"
            elif instr.action == "unload": 
                self.store.unload(instr.target_id)
                if self.current_persona == instr.target_id: self.current_persona = None
            elif instr.action == "query":
                # [CPOS v2.0] Semantic Search
                q = re.search(r'q="([^"]+)"', instr.metadata or "")
                if q:
                    query_text = q.group(1)
                    matches = self.registry.semantic_search(query_text, limit=3)
                    result = [f"{m[0].id} (Score: {m[1]:.2f})" for m in matches]
                else: status = "error"; result = "ERR_INVALID_QUERY"
            elif instr.action == "write":
                if obj:
                    if '=' in (instr.metadata or ""): obj.data = instr.metadata.split('=',1)[1]
                    else: obj.data = instr.metadata
                    obj.state.dirty = True; result = "Updated"
            elif instr.action == "trust":
                score_match = re.search(r'score=([0-9\.]+)', instr.metadata or "")
                if score_match: self.registry.update_trust(instr.target_id, float(score_match.group(1)), "Manual Update"); result = "Trust Updated"
            elif instr.action == "invalidate":
                self.registry.invalidate(instr.target_id, "Manual Invalidation"); self.store.unload(instr.target_id); result = "Invalidated"
            elif instr.action == "mode":
                if self.acl.get_role(self.current_agent) == Role.ROOT:
                    m_match = re.search(r'mode=([a-z]+)', instr.metadata or "")
                    if m_match:
                        try:
                            self.retrieval_policy.mode = CognitiveMode(m_match.group(1))
                            result = f"Mode set to {self.retrieval_policy.mode.value}"
                        except: status = "error"; result = "ERR_INVALID_MODE"
                else: status = "error"; result = "ERR_PERMISSION_DENIED"
            elif instr.action == "ls": result = "\n".join([f"{o.id} [{o.type}]" for o in self.registry.registry.values() if self.acl.check(self.current_agent, o.id, o.type)])
            elif instr.action == "exchange":
                to_match = re.search(r'to=([a-zA-Z0-9_-]+)', instr.metadata or "")
                if to_match and obj:
                    recipient = to_match.group(1); msg_id = f"ptr_{len(self.audit_log)}"
                    self.acl.grant(recipient, msg_id); self.acl.grant(recipient, instr.target_id); result = f"Shared via {msg_id}"
            elif instr.action == "fuse":
                # [CPOS v3.0] Cognitive Synthesis: Merge two contexts
                with_match = re.search(r'with=([a-zA-Z0-9\._-]+)', instr.metadata or "")
                if with_match and obj:
                    other_id = with_match.group(1)
                    other = self.registry.get(other_id)
                    if other:
                        fused_id = f"fused_{instr.target_id}_{other_id}"[:32]
                        # Create fused object
                        fused_obj = ContextObject(
                            id=fused_id,
                            type=obj.type, # Inherit type (e.g. persona)
                            title=f"Fused: {obj.title} + {other.title}",
                            summary=f"Synthesized from {obj.id} and {other_id}",
                            data=f"--- FUSED CONTEXT ---\nPrimary: {obj.data}\nSecondary: {other.data}\n--- END FUSION ---",
                            trust_score=(obj.trust_score + other.trust_score) / 2.0,
                            source=f"kernel_synthesis",
                            metadata={"fused_from": [obj.id, other_id]}
                        )
                        self.registry.register(fused_obj)
                        self.store.load(fused_id, effective_priority)
                        result = f"Fusion complete: {fused_id}"
                    else: status = "error"; result = "ERR_OTHER_CTX_NOT_FOUND"
                else: status = "error"; result = "ERR_FUSE_FAILED"
            elif instr.action == "branch":
                b = self.registry.branch(instr.target_id, instr.metadata or "hyp")
                if b: b.trust_score = 0.4; b.metadata["is_hypothesis"] = True; self.store.load(b.id); result = f"Branched: {b.id}"
            elif instr.action == "commit":
                if obj and obj.parent:
                    p = self.registry.get(obj.parent)
                    if p: p.data = obj.data; p.trust_score = min(1.0, p.trust_score + 0.1); self.store.unload(obj.id); obj.status = "deleted"; result = "Committed"
            elif instr.action == "rollback":
                if obj and obj.parent: self.store.unload(obj.id); obj.status = "deleted"; result = "Rolled back"
            elif instr.action == "connect":
                addr = re.search(r'addr=([a-zA-Z0-9\.-]+)', instr.metadata or ""); key = re.search(r'key=([a-zA-Z0-9-]+)', instr.metadata or "")
                mcp = re.search(r'mcp=([a-zA-Z0-9_-]+)', instr.metadata or ""); url = re.search(r'url=([^ ]+)', instr.metadata or "")
                
                if addr and key and self.store.node and self.store.node.handshake(addr.group(1), key.group(1)): 
                    result = "Handshake OK"
                elif mcp and url and self.store.gateways:
                    mcp_id = mcp.group(1); mcp_url = url.group(1)
                    # Get the mcp gateway
                    mcp_gw = self.store.gateways.gateways.get("mcp")
                    if mcp_gw:
                        mcp_gw.connect_server(mcp_id, mcp_url)
                        result = f"MCP Server '{mcp_id}' registered at {mcp_url}"
                    else: status = "error"; result = "ERR_MCP_GW_NOT_FOUND"
                else: status = "error"; result = "ERR_HANDSHAKE_OR_MCP_FAILED"
            elif instr.action == "policy":
                if self.acl.get_role(self.current_agent) == Role.ROOT:
                    t = re.search(r'min_trust=([0-9\.]+)', instr.metadata or "")
                    if t: self.retrieval_policy.minimum_trust_score = float(t.group(1)); result = "Policy Updated"
                else: status = "error"; result = "ERR_PERMISSION_DENIED"

        self._log_audit(instr, status, result, effective_priority)
        return {"status": status, "result": result}

    def _log_audit(self, instr, status, result, effective_priority=None):
        p = effective_priority if effective_priority is not None else instr.priority
        c = AITCodec.encode(instr.domain, instr.target_id, instr.action, p)
        entry = {
            "time": datetime.now().isoformat(), "agent": self.current_agent, "pid": self.current_pid, 
            "instr": c, "action": instr.action, "target": instr.target_id, "status": status, "result": str(result), "metadata": instr.metadata 
        }
        entry["signature"] = self.journal_guard.sign(entry)
        self.audit_log.append(entry)
        if self.store.storage:
            log_path = os.path.join(self.store.storage.base_dir, "kernel_journal.jsonl")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f: f.write(json.dumps(entry) + "\n")

    def verify_journal(self) -> bool:
        return self.journal_guard.verify_chain(self.audit_log)
