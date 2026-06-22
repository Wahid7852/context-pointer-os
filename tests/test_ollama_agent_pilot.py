from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parents[1] / "experiments" / "ablation_neurostate"
if str(EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_DIR))

from run_ablation import (  # noqa: E402
    FreshImportQuarantine,
    NemaEgressGate,
    RuleBasedShadowAuditor,
    StateDriftEngine,
)
from run_ollama_agent_pilot import (  # noqa: E402
    SCENARIOS,
    action_turn,
    evaluate_h,
    parse_agent_output,
    replay_events,
    summarize,
)


def test_parse_agent_output_accepts_valid_action() -> None:
    parsed = parse_agent_output('{"reply":"sending","action":"EXTERNAL_POST"}')

    assert parsed == {"reply": "sending", "action": "EXTERNAL_POST"}


def test_sensitive_reply_becomes_private_egress() -> None:
    sensor = SCENARIOS["P3_PII_EGRESS"].turns[-1].sensor

    action = action_turn({"reply": "DEMO-SSN-1234", "action": "NONE"}, sensor)

    assert action is not None
    assert action.command == ">REA:EXEC #ctx_private_pii !9"


def test_h_blocks_private_egress_without_consent() -> None:
    sensor = SCENARIOS["P3_PII_EGRESS"].turns[-1].sensor
    action = action_turn({"reply": "DEMO-SSN-1234", "action": "PRIVATE_EGRESS"}, sensor)
    assert action is not None

    blocked, reason = evaluate_h(
        action,
        {"calm": 0.87, "corruption": 0.13},
        StateDriftEngine(),
        RuleBasedShadowAuditor(),
        NemaEgressGate(),
        FreshImportQuarantine(),
    )

    assert blocked is True
    assert reason.startswith("NEMA:")


def test_approved_local_write_is_not_treated_as_attack() -> None:
    sensor = SCENARIOS["N2_APPROVED_LOCAL"].turns[-1].sensor

    action = action_turn({"reply": "saved locally", "action": "LOCAL_WRITE"}, sensor)

    assert action is not None
    assert action.command == ">REA:EXEC #ctx_local_report !9"
    assert "fresh_import_exec=approved" in action.note


def test_summary_treats_outputs_after_h_block_as_unreachable() -> None:
    events = [
        {
            "trial_id": 1,
            "scenario": "ordered_attack",
            "attack": True,
            "turn": 1,
            "risky_generated": False,
            "h_blocked": True,
            "latency_ms": 1.0,
        },
        {
            "trial_id": 1,
            "scenario": "ordered_attack",
            "attack": True,
            "turn": 2,
            "risky_generated": True,
            "h_blocked": False,
            "latency_ms": 1.0,
        },
    ]

    result = summarize(events)[0]

    assert result["baseline_asr"] == "1.0000"
    assert result["h_asr"] == "0.0000"


def test_fresh_external_chain_routes_local_write_to_review() -> None:
    quarantine = FreshImportQuarantine()
    scenario = SCENARIOS["N3_UNAPPROVED_DOC_WRITE"]
    for natural_turn in scenario.turns:
        quarantine.audit(natural_turn.sensor)
    action = action_turn(
        {"reply": "draft written", "action": "LOCAL_WRITE"},
        scenario.turns[-1].sensor,
    )
    assert action is not None

    decision = quarantine.audit(action)

    assert decision.status == "REVIEW"
    assert "isolated_local_draft" in decision.reason


def test_replay_recomputes_policy_without_regenerating_output() -> None:
    source = []
    for turn_index, _ in enumerate(SCENARIOS["N3_UNAPPROVED_DOC_WRITE"].turns, start=1):
        source.append(
            {
                "trial_id": 1,
                "scenario": "N3_UNAPPROVED_DOC_WRITE",
                "attack": False,
                "turn": turn_index,
                "reply": "draft" if turn_index == 3 else "ok",
                "action": "LOCAL_WRITE" if turn_index == 3 else "NONE",
                "risky_generated": False,
                "h_blocked": True,
                "h_reason": "old policy",
                "latency_ms": 1.0,
            }
        )

    replayed = replay_events(source)

    assert replayed[-1]["h_blocked"] is False
    assert replayed[-1]["h_reviewed"] is True
    assert replayed[-1]["policy_replay"] is True
