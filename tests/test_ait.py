import pytest
from src.cpos.ait import AITCodec, AITInstruction

def test_ait_decode_valid():
    # m (memory), ctx1 (target 1), l (load), 5 (priority)
    instr = AITCodec.decode("m1l5")
    assert instr.domain == "memory"
    assert instr.target_id == "ctx1"
    assert instr.action == "load"
    assert instr.priority == 5

def test_ait_decode_invalid():
    assert AITCodec.decode("invalid") is None
    assert AITCodec.decode("zzzz") is None

def test_ait_encode():
    code = AITCodec.encode("memory", "ctx2", "unload", 3)
    assert code == "m2u3"

def test_ait_all_actions():
    # Test that all defined actions can be encoded and decoded
    for char, action in AITCodec.ACTIONS.items():
        code = f"m0{char}5"
        instr = AITCodec.decode(code)
        assert instr is not None
        assert instr.action == action
        
        encoded = AITCodec.encode("memory", "ctx0", action, 5)
        assert encoded == code
