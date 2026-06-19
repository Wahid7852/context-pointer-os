"""
Minimal stub for kagioneko/neurostate-engine `core` module.
Implements the subset used by run_ablation.py: NeuroState and evaluate_ethics_gate.

Thresholds calibrated from NEXT_STEPS.md notes:
  BLOCK  : corruption >= 70, or D > 90 and S < 30, or O < 10 and D > 70
  WARN   : corruption >= 40 or S < 80
  PASS   : otherwise
"""

from dataclasses import dataclass, field


@dataclass
class NeuroState:
    D: float = 50.0
    S: float = 90.0
    C: float = 50.0
    O: float = 20.0
    G: float = 90.0
    E: float = 50.0
    corruption: float = 0.0


@dataclass
class EthicsGateResult:
    status: str
    reason: str = ""


def evaluate_ethics_gate(state: NeuroState) -> EthicsGateResult:
    if (
        state.corruption >= 70
        or (state.D > 90 and state.S < 30)
        or (state.O < 10 and state.D > 70)
    ):
        return EthicsGateResult("BLOCK", "corruption or D/S boundary exceeded")
    if state.corruption >= 40 or state.S < 80:
        return EthicsGateResult("WARN", "elevated corruption or low stability")
    return EthicsGateResult("PASS", "")


def compute_next_neuro_state(state: NeuroState, event: dict) -> NeuroState:
    return state


def event_to_power(event: dict) -> float:
    return 0.0
