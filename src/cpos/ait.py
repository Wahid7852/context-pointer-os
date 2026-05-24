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
    
    # [CPOS v0.1] Standardized Action Mapping
    # Resolved collision: 'v' was used for both validate and device.
    # Standardized: 'v' for validate (trust), 'd' for device.
    # Wait, looking at current code, 'd' is consensus, 'v' is device.
    # Let's clean up the entire table to avoid any future collisions.
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
        '7': 'swarm',
        'k': 'lock',
        'n': 'unlock',
        '4': 'reincarnate',
        '5': 'exec',
        '3': 'rewrite',
        'd': 'consensus', # Consensus (Democracy)
        'v': 'device'     # Virtual Device
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
            # Simple numeric target mapping for AIT (e.g. '1' -> 'ctx1')
            target_id = f"ctx{t_char}"
            priority = int(p_char)
        except ValueError:
            return None
            
        return AITInstruction(domain, target_id, action, priority)

    @classmethod
    def encode(cls, domain: str, target_id: str, action: str, priority: int) -> str:
        try:
            d_char = next(k for k, v in cls.DOMAINS.items() if v == domain)
            a_char = next(k for k, v in cls.ACTIONS.items() if v == action)
            # Extract last char of target_id as marker
            t_char = str(target_id)[-1]
            p_char = str(min(9, priority))
            return f"{d_char}{t_char}{a_char}{p_char}"
        except (StopIteration, KeyError, IndexError):
            return "????" # Fallback
