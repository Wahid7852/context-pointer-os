import pytest
from cpos.ait import AITCodec, AITInstruction

def test_ait_decode():
    # m1l5: memory, ctx1, load, priority 5
    instr = AITCodec.decode("m1l5")
    assert instr.domain == "memory"
    assert instr.target_id == "ctx1"
    assert instr.action == "load"
    assert instr.priority == 5

def test_ait_encode():
    code = AITCodec.encode("memory", "ctx1", "load", 5)
    assert code == "m1l5"

def test_ait_collision_check():
    # Ensure validate (v) and device (d) are distinct
    # Wait, my new mapping uses 't' for trust/validate and 'v' for device
    # Let's verify the actual map
    assert AITCodec.ACTIONS['t'] == 'trust'
    assert AITCodec.ACTIONS['v'] == 'device'
    assert 'd' in AITCodec.ACTIONS # consensus
    
def test_ait_invalid_code():
    assert AITCodec.decode("invalid") is None
    assert AITCodec.decode("zzzz") is None
