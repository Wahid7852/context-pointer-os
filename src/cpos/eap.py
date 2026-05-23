import re
from typing import Optional, List
from .ait import AITInstruction, AITCodec

class EAPParser:
    """The 'Assembly' layer. Parses >MEM:LOAD #ctx4 !8 style strings."""
    
    # Pattern: >DOMAIN:ACTION #ctxID !PRIORITY [| metadata]
    PATTERN = r'>([A-Z]+):([A-Z]+)\s+#ctx([a-zA-Z0-9\._msg]+)\s*!(\d+)(?:\s*\|\s*(.*))?'

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
        'GC': 'gc',
        'LS': 'ls',
        'PS': 'ps',
        'SYS': 'syscall',
        'DEV': 'device',
        'POLICY': 'policy',
        'LOCK': 'lock',
        'UNLOCK': 'unlock'
    }

    @classmethod
    def parse(cls, line: str) -> Optional[AITInstruction]:
        match = re.match(cls.PATTERN, line)
        if not match:
            return None
            
        domain_raw, action_raw, ctx_id_suffix, priority_raw, metadata = match.groups()
        
        domain = cls.DOMAIN_MAP.get(domain_raw)
        action = cls.ACTION_MAP.get(action_raw)
        
        if not domain or not action:
            return None
        
        # If ctx_id_suffix starts with 'msg_', it's a message ID, don't prefix with 'ctx'
        target_id = ctx_id_suffix if ctx_id_suffix.startswith('msg_') else f"ctx{ctx_id_suffix}"
            
        return AITInstruction(
            domain=domain,
            target_id=target_id,
            action=action,
            priority=int(priority_raw),
            metadata=metadata
        )

