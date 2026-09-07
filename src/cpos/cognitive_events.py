"""[CPOS Phase 1] Sensor event envelope and Task Tape adapter.

Implements only the part of `docs/EVENT_BUS_AND_WORLD_MODEL_SPEC.md` and
`docs/SENSOR_AND_GOAL_MANAGER_SPEC.md` that the Git sensor needs: the
`kagioneko.sensor_event.v1` record shape, its safety invariants, and the
adapter that writes conforming records onto the CPOS Task Tape.

Out of scope here: the Goal Manager, the World Model, and the other
`kagioneko.cognitive_event.v1` event types. This module exists so the
Event Bus boundary is a named seam rather than an implicit one, not to
start those components.

The contract is closed. A record carrying a field that is not in
`FIELD_TYPES` is refused, so the metadata-only boundary holds for any
producer, not only for the Git sensor.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

SENSOR_EVENT_SCHEMA = "kagioneko.sensor_event.v1"

# Task Tape event name for a recorded sensor observation, from the
# "Suggested CPOS event names" list in the Event Bus spec.
TAPE_SENSOR_EVENT = "cognitive_sensor_event_recorded"

RISK_LEVELS = ("low", "medium", "high", "critical")

# Every field the Event Bus spec pins to a fixed value for a metadata-only
# sensor record. These are invariants of the Phase 1 sensor layer, not
# per-event choices, so the builder sets them and the validator enforces them.
SAFETY_INVARIANTS = {
    "metadata_only": True,
    "raw_request_stored": False,
    "raw_diff_stored": False,
    "raw_outputs_stored": False,
    "secret_values_stored": False,
    "execute_automatically": False,
}

# The complete, frozen top-level field set with its required type. Anything
# absent from this mapping is rejected: an unknown field would otherwise ride
# through the adapter into persistent storage and defeat the boundary.
FIELD_TYPES: Dict[str, Any] = {
    "schema": str,
    "event_id": str,
    "event_type": str,
    "sensor_event_type": str,
    "source": str,
    "observed_at": str,
    "subject": str,
    "summary": str,
    "risk": str,
    "confidence": float,
    "source_of_truth": list,
    "requires_human_review": bool,
    "suggested_next_action": str,
    # Contract-level provenance: dotted paths naming fields whose value is
    # written by an untrusted producer (a repository, a remote peer). A
    # consumer must not render these as trusted prose.
    "untrusted_fields": list,
    "metadata_only": bool,
    "raw_request_stored": bool,
    "raw_diff_stored": bool,
    "raw_outputs_stored": bool,
    "secret_values_stored": bool,
    "execute_automatically": bool,
    # Additive extension: the state labels and counts the Event Bus spec tells
    # sensors to store, which the published envelope has no slot for.
    "observation": dict,
}

REQUIRED_FIELDS = tuple(f for f in FIELD_TYPES if f != "observation")

# Events are evidence pointers, not evidence dumps. A field name carrying any
# of these substrings is a raw-output log leaking onto the tape.
DENIED_KEY_PARTS = (
    "raw", "stdout", "stderr", "diff", "patch", "body", "content",
    "secret", "token", "password", "credential", "key", "env",
)

# An observation value is a state label, a count, or a timestamp. Nesting or an
# unbounded string is a blob in disguise.
OBSERVATION_VALUE_TYPES = (str, int, float, bool, type(None))
MAX_OBSERVATION_VALUE_LEN = 256


class SensorEventContractError(ValueError):
    """A record does not conform to `kagioneko.sensor_event.v1`."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _denied(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in DENIED_KEY_PARTS)


def build_sensor_event(
    *,
    sensor_event_type: str,
    source: str,
    subject: str,
    summary: str,
    risk: str = "low",
    confidence: float = 1.0,
    source_of_truth: Optional[List[str]] = None,
    requires_human_review: bool = False,
    suggested_next_action: str = "continue_observing",
    untrusted_fields: Optional[List[str]] = None,
    observed_at: Optional[str] = None,
    observation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one validated `kagioneko.sensor_event.v1` record."""
    event = {
        "schema": SENSOR_EVENT_SCHEMA,
        "event_id": f"sensor_evt_{uuid.uuid4().hex[:16]}",
        # Constant per the Event Bus spec: the concrete observation goes in
        # `sensor_event_type`, never in `event_type`.
        "event_type": "sensor_event",
        "sensor_event_type": sensor_event_type,
        "source": source,
        "observed_at": observed_at or _now_iso(),
        "subject": subject,
        "summary": summary,
        "risk": risk,
        "confidence": confidence,
        "source_of_truth": list(source_of_truth or []),
        "requires_human_review": requires_human_review,
        "suggested_next_action": suggested_next_action,
        "untrusted_fields": list(untrusted_fields or []),
        **SAFETY_INVARIANTS,
    }
    if observation is not None:
        event["observation"] = dict(observation)
    validate_sensor_event(event)
    return event


def _validate_types(event: Dict[str, Any]) -> None:
    unknown = sorted(set(event) - set(FIELD_TYPES))
    if unknown:
        raise SensorEventContractError(
            f"unknown top-level fields are not part of the contract: {unknown}"
        )
    missing = [f for f in REQUIRED_FIELDS if f not in event]
    if missing:
        raise SensorEventContractError(f"missing required fields: {missing}")
    for field, expected in FIELD_TYPES.items():
        if field not in event:
            continue
        value = event[field]
        if expected is bool:
            if not isinstance(value, bool):
                raise SensorEventContractError(f"{field} must be a bool, got {value!r}")
        elif expected is float:
            # bool is a subclass of int, so it has to be excluded explicitly.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SensorEventContractError(f"{field} must be a number, got {value!r}")
        elif not isinstance(value, expected):
            raise SensorEventContractError(
                f"{field} must be {expected.__name__}, got {type(value).__name__}"
            )


def _validate_observation(event: Dict[str, Any]) -> None:
    for key, value in (event.get("observation") or {}).items():
        if not isinstance(key, str):
            raise SensorEventContractError(f"observation key must be a string: {key!r}")
        if _denied(key):
            raise SensorEventContractError(
                f"observation key {key!r} looks like raw evidence, not metadata"
            )
        if not isinstance(value, OBSERVATION_VALUE_TYPES):
            raise SensorEventContractError(
                f"observation value for {key!r} must be a scalar, "
                f"got {type(value).__name__}"
            )
        if isinstance(value, str) and len(value) > MAX_OBSERVATION_VALUE_LEN:
            raise SensorEventContractError(
                f"observation value for {key!r} exceeds "
                f"{MAX_OBSERVATION_VALUE_LEN} characters"
            )


def validate_sensor_event(event: Dict[str, Any]) -> None:
    """Reject anything that is not a conforming metadata-only sensor record."""
    if not isinstance(event, dict):
        raise SensorEventContractError("event must be a mapping")
    _validate_types(event)

    if event["schema"] != SENSOR_EVENT_SCHEMA:
        raise SensorEventContractError(f"unexpected schema: {event['schema']!r}")
    if event["event_type"] != "sensor_event":
        raise SensorEventContractError(
            f"event_type must be 'sensor_event', got {event['event_type']!r}"
        )
    if not event["sensor_event_type"]:
        raise SensorEventContractError("sensor_event_type must be concrete")
    if not event["source"]:
        raise SensorEventContractError("source must name a concrete sensor")
    if event["risk"] not in RISK_LEVELS:
        raise SensorEventContractError(f"unknown risk level: {event['risk']!r}")
    if not 0.0 <= float(event["confidence"]) <= 1.0:
        raise SensorEventContractError("confidence must be within 0.0..1.0")

    for field, expected in SAFETY_INVARIANTS.items():
        if event[field] is not expected:
            raise SensorEventContractError(
                f"safety field {field} must be {expected}, got {event[field]!r}"
            )

    for entry in event["source_of_truth"]:
        if not isinstance(entry, str):
            raise SensorEventContractError("source_of_truth entries must be strings")

    for path in event["untrusted_fields"]:
        if not isinstance(path, str):
            raise SensorEventContractError("untrusted_fields entries must be strings")
        if _resolve_path(event, path) is _MISSING:
            raise SensorEventContractError(
                f"untrusted_fields names a field that is not present: {path!r}"
            )

    _validate_observation(event)


_MISSING = object()


def _resolve_path(event: Dict[str, Any], path: str) -> Any:
    current: Any = event
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            return _MISSING
        current = current[segment]
    return current


def task_tape_sink(registry, pointer_id_for: Any = None):
    """Adapter: publish conforming sensor events onto the CPOS Task Tape.

    Phase 1 substrate is `registry.audit_log` via `registry._log_event`, which
    the Event Bus spec permits as a first persistence substrate. The record
    written is the sensor envelope itself, so swapping the substrate later does
    not change the contract. Validation runs here as well as in the builder,
    because the adapter is the boundary any producer crosses: a record built by
    hand or by another sensor is refused rather than persisted.
    """
    def _sink(event: Dict[str, Any]) -> None:
        validate_sensor_event(event)
        pointer_id = (
            pointer_id_for(event) if callable(pointer_id_for)
            else (pointer_id_for or event["source"])
        )
        registry._log_event(TAPE_SENSOR_EVENT, pointer_id, event)
    return _sink
