import re
from typing import NamedTuple, Optional

class AITInstruction(NamedTuple):
    domain: str
    target_id: str
    action: str
    priority: int
    metadata: Optional[str] = None

class AITCodec:
    """The 'Machine Code' layer. 4-character fixed instruction set."""
    
    DOMAINS = {
        'm': 'memory',
        's': 'security',
        'n': 'neurostate',
        'o': 'observability',
        'r': 'reasoning',
        't': 'task',
        'p': 'persona'
    }
    
    ACTIONS = {
        'l': 'load',
        'u': 'unload',
        'm': 'summarize',
        'r': 'raw',
        'b': 'branch',
        'g': 'merge',
        '1': 'commit',
        '0': 'rollback',
        'q': 'query',
        'w': 'write',
        'f': 'forget',
        't': 'trust',
        'z': 'invalidate',
        's': 'sync',
        'p': 'send',
        'c': 'gc',
        'h': 'connect',
        'i': 'ls',
        'x': 'ps',
        'y': 'syscall',
        'a': 'policy',
        'j': 'mode',
        'e': 'exchange',
        '8': 'fuse',
        '9': 'synth',
        'v': 'device',
        'k': 'lock',
        'n': 'unlock'
    }

    @classmethod
    def decode(cls, code: str) -> Optional[AITInstruction]:
        if len(code) != 4:
            return None
        
        d_char, t_char, a_char, p_char = code[0], code[1], code[2], code[3]
        
        domain = cls.DOMAINS.get(d_char)
        action = cls.ACTIONS.get(a_char)
        
        if not domain or not action:
            return None
            
        try:
            target_id = f"ctx{t_char}"
            priority = int(p_char)
        except ValueError:
            return None
            
        return AITInstruction(domain, target_id, action, priority)

    @classmethod
    def encode(cls, domain: str, target_id: str, action: str, priority: int) -> str:
        d_char = next(k for k, v in cls.DOMAINS.items() if v == domain)
        a_char = next(k for k, v in cls.ACTIONS.items() if v == action)
        # Extract last char of target_id as marker (e.g. '4' from 'ctx4' or '0' from 'msg_0')
        t_char = target_id[-1]
        p_char = str(min(9, priority))
        return f"{d_char}{t_char}{a_char}{p_char}"
