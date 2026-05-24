import re
from typing import Optional, List
from .ait import AITInstruction, AITCodec

class EAPParser:
    """The 'Assembly' layer. Parses >MEM:LOAD #ctx4 !8 or >MEM:LOAD #ptr_0 !5 style strings."""
    
    # Pattern: >DOMAIN:ACTION #ID !PRIORITY [| metadata]
    # Modified to allow distributed pointer URI characters (:, /, -, .)
    PATTERN = r'>([A-Z]+):([A-Z]+)\s+#([a-zA-Z0-9\._msg:/\-\.]+)\s*!(\d+)(?:\s*\|\s*(.*))?'

    DOMAIN_MAP = {
        'MEM': 'memory',
        'SEC': 'security',
        'NEU': 'neurostate',
        'OBS': 'observability',
        'REA': 'reasoning',
        'TSK': 'task',
        'PER': 'persona'
    }

    ACTION_MAP = {
        'LOAD': 'load',
        'UNLOAD': 'unload',
        'SUM': 'summarize',
        'RAW': 'raw',
        'BRANCH': 'branch',
        'FORK': 'branch',
        'MERGE': 'merge',
        'COMMIT': 'commit',
        'ROLLBACK': 'rollback',
        'QUERY': 'query',
        'UPDATE': 'write',
        'TRUST': 'trust',
        'INVALIDATE': 'invalidate',
        'FORGET': 'forget',
        'SYNC': 'sync',
        'SEND': 'send',
        'EXCHANGE': 'exchange',
        'FUSE': 'fuse',
        'SYNTH': 'synth',
        'SWARM': 'swarm',
        'CONSENSUS': 'consensus',
        'REINCARNATE': 'reincarnate',
        'EXEC': 'exec',
        'GC': 'gc',
        'LS': 'ls',
        'PS': 'ps',
        'SYS': 'syscall',
        'DEV': 'device',
        'CONNECT': 'connect',
        'POLICY': 'policy',
        'MODE': 'mode',
        'LOCK': 'lock',
        'UNLOCK': 'unlock'
    }

    @classmethod
    def parse(cls, line: str) -> Optional[AITInstruction]:
        match = re.match(cls.PATTERN, line)
        if not match:
            return None
            
        domain_raw, action_raw, id_raw, priority_raw, metadata = match.groups()
        
        domain = cls.DOMAIN_MAP.get(domain_raw)
        action = cls.ACTION_MAP.get(action_raw)
        
        if not domain or not action:
            return None
        
        # [CPOS v0.4] Distributed Pointer Parsing
        # Format: ptr://node_addr/type/id
        if id_raw.startswith("ptr://"):
            try:
                # Remove ptr:// and split
                parts = id_raw[6:].split("/")
                if len(parts) == 3:
                    node_addr, ctx_type, remote_id = parts
                    # We store the full remote path as target_id for the scheduler/store to handle
                    target_id = id_raw
                else:
                    target_id = id_raw # Fallback
            except:
                target_id = id_raw
        else:
            # Smart prefixing: If it doesn't look like a special ID (ptr_, msg_, ptr://) 
            # and doesn't already have 'ctx', add 'ctx' for convenience.
            target_id = id_raw
            if not (id_raw.startswith('msg_') or id_raw.startswith('ptr_') or 
                    id_raw.startswith('ptr://') or id_raw.startswith('ctx')):
                # Check if it looks like a purely numeric ID (legacy support)
                if id_raw.isdigit():
                    target_id = f"ctx{id_raw}"
                # Otherwise, assume it's a full ID as provided (v2.0)
                else:
                    target_id = id_raw
            
        return AITInstruction(
            domain=domain,
            target_id=target_id,
            action=action,
            priority=int(priority_raw),
            metadata=metadata
        )
