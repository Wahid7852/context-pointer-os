import pytest
from cpos.ait import AITCodec, AITInstruction

def test_ait_decode():
    instr = AITCodec.decode("m4l8")
    assert instr.domain == "memory"
    assert instr.target_id == "ctx4"
    assert instr.action == "load"
    assert instr.priority == 8

def test_ait_encode():
    code = AITCodec.encode("memory", "ctx4", "load", 8)
    assert code == "m4l8"

def test_ait_complex_id_encode():
    # Should take the last char of the ID
    code = AITCodec.encode("persona", "ctx20", "write", 9)
    assert code == "p0w9"
