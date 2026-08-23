# Event Bus and World Model Spec — Draft

This is a documentation-only specification for connecting sensors, goals, memory, observability, and CPOS review gates in the Kagioneko Cognitive Agent OS.

No implementation is started by this document.

## Purpose

The Event Bus and World Model connect these pieces:

```text
Sensor Layer
  -> Event Bus
  -> World Model
  -> Goal Manager
  -> CPOS Safety Kernel / Human Escalation
  -> Observatory + tape-memory pointers
```

The goal is to give the system a current, metadata-only map of reality without storing raw secrets, raw diffs, raw outputs, or private runtime bodies.

## Core rule

Events are evidence pointers, not raw evidence dumps.

Store:

- IDs
- timestamps
- short summaries
- hashes/sizes/counts
- risk levels
- state labels
- source-of-truth paths/URLs
- review/action hints

Do not store:

- API keys, tokens, passwords, Vault values, SSH keys, cert/key material
- `.env` values
- raw stdout/stderr
- raw diffs or patch bodies
- raw request bodies
- raw checkpoint/handoff bodies
- private runtime logs

## Event Bus overview

The Event Bus is the shared shape for cross-repo cognitive events.

It should support:

- sensor events
- goal updates
- memory pointers
- state deltas
- action proposals
- review decisions
- execution results
- reflection notes
- sleep/consolidation events

CPOS Task Tape can serve as the first persistence substrate. Observatory can later consume selected events for replayable timelines. tape-memory can store only short pointers to the latest relevant event/doc, not raw event history.

## Base event schema

```json
{
  "schema": "kagioneko.cognitive_event.v1",
  "event_id": "evt_...",
  "event_type": "sensor_event|goal_update|memory_pointer|state_delta|action_proposal|review_decision|execution_result|reflection_note|sleep_consolidation",
  "sensor_event_type": "git_state_changed|null",
  "source": "git_sensor|docker_sensor|goal_manager|cpos|observatory|tape_memory|user|vn_cpu|zenn|notion",
  "observed_at": "2026-06-06T00:00:00+09:00",
  "subject": "cpos_v0_1_1_rc1",
  "summary": "v0.1.1-rc1 prerelease published; final release paused",
  "risk": "low|medium|high|critical",
  "confidence": 0.9,
  "source_of_truth": ["NEXT_HANDOFF.md"],
  "related_goal_ids": ["cpos_v0_1_1_final"],
  "requires_human_review": false,
  "metadata_only": true,
  "raw_request_stored": false,
  "raw_diff_stored": false,
  "raw_outputs_stored": false,
  "secret_values_stored": false,
  "execute_automatically": false
}
```

## Event types

### `sensor_event`

Created by software sensors. For these records, `event_type` remains `sensor_event`; the concrete observation is stored in `sensor_event_type` (for example, `git_dirty`). Sensor sources use concrete names such as `git_sensor`, matching the Sensor spec.

Examples:

- git clean/synced
- Docker container running
- late-night session
- Zenn draft exists
- Notion page created
- token-bearing remote URL detected

Rules:

- values must be redacted before persistence
- raw command output is not stored

### `goal_update`

Created when a goal changes state.

Examples:

- `cpos_v0_1_1_final`: paused -> ready_for_review
- `zenn_cpos_for_agents`: draft -> ready_for_review
- `neko_late_night_pause`: observing -> done

Rules:

- goal updates do not grant execution authority by themselves
- updates that grant new authority require Human Escalation

### `memory_pointer`

Created when a memory pointer is updated or declared stale.

Examples:

- `cpos_resume_latest` now points to `NEXT_HANDOFF.md`
- `zenn_cpos_for_agents_draft` points to the Zenn draft path
- stale tape detected after new release state

Rules:

- pointer only, no raw memory bodies
- tape-memory remains cache, not source of truth

### `state_delta`

Created by state systems such as NeuroState or session/wellbeing sensors.

Examples:

- late-night caution increased
- post-overtime context detected
- long-session break suggested
- VN-CPU organism heartbeat observed

Rules:

- state deltas are signals, not commands
- strong state updates are review-gated
- no shame/self-judgment wording

### `action_proposal`

Created when the system suggests an action.

Examples:

- draft release notes
- run tests
- create Zenn draft
- ask user whether to publish final release

Rules:

- proposal is not execution
- high-risk proposal enters CPOS/Human Escalation
- destructive, publish, release, tag, port, user management, and `authorized_keys` actions require explicit confirmation

### `review_decision`

Created by CPOS review gates or Human Escalation.

Examples:

- contract approved only
- release publish rejected
- sandbox run approved with supplied diff

Rules:

- approval meaning must be scoped
- contract approval does not imply command execution
- final release approval must be explicit

### `execution_result`

Created after a sandboxed or external execution result summary.

Examples:

- tests passed count
- prepublish ok
- release_check ok
- external agent redacted result

Rules:

- no raw stdout/stderr
- store status, exit code, failure kind, duration, hash/size only

### `reflection_note`

Created after a session or design insight.

Examples:

- origin story note
- architecture decision
- “AGI claim avoided” positioning

Rules:

- reflective summaries are allowed
- avoid storing private sensitive text verbatim

### `sleep_consolidation`

Created at session pause/sleep.

Examples:

- handoff updated
- goals paused
- final release deferred
- next docs to read listed

Rules:

- prefer handoff docs as source of truth
- do not push/publish/release from sleep flow unless explicitly requested

## World Model overview

The World Model is the current state map.

It is not a raw database of everything. It is a compact, queryable set of facts derived from events and source-of-truth docs.

## World fact schema

```json
{
  "schema": "kagioneko.world_fact.v1",
  "fact_id": "cpos.release.v0_1_1_rc1",
  "subject": "context_pointer_os",
  "predicate": "has_prerelease",
  "object": "v0.1.1-rc1",
  "state": "published_prerelease",
  "confidence": 1.0,
  "updated_at": "2026-06-06T00:00:00+09:00",
  "source_event_ids": ["evt_..."],
  "source_of_truth": ["docs/RELEASE_STATUS.md"],
  "stale_after": null,
  "metadata_only": true
}
```

## World fact categories

### Repo state

Facts:

- repo path
- branch
- clean/dirty
- ahead/behind
- latest pushed commit
- known untracked artifacts

Example:

```text
repo:cpos_defensive_agent state=clean branch=main remote_synced=true
```

### Release state

Facts:

- latest stable release
- prerelease state
- draft/final distinction
- final release paused/active
- validation status

Example:

```text
release:cpos_v0_1_1_rc1 state=published_prerelease final_v0_1_1=paused
```

### Docker/process state

Facts:

- container name
- image
- status
- command
- bind mounts
- port exposure summary

Example:

```text
docker:vn_cpu_v04_lean state=running role=cognitive_pulse_source permission=observe_only
```

### Draft/article state

Facts:

- article path
- published flag
- next action

Example:

```text
zenn:cpos_for_agents state=draft published=false next=polish_before_publish
```

### Goal state

Facts:

- goal state
- revisit timing
- blockers
- explicit confirmation requirements

Example:

```text
goal:cpos_v0_1_1_final state=paused requires_explicit_confirmation=true
```

### Known risk state

Facts:

- credential incident
- local runtime artifacts
- active containers
- late-night caution

Example:

```text
risk:credential_incident state=local_remote_fixed revoke_rotate_recommended=true
```

### Memory pointer state

Facts:

- latest handoff doc
- summary doc
- tape-memory pointer freshness

Example:

```text
memory:cpos_resume_latest source=NEXT_HANDOFF.md freshness=current
```

## Staleness rules

A world fact is stale when:

- source-of-truth file changed
- commit/tag/release state changed
- tests/prepublish/release_check reran
- goal state changed
- user changed priority
- time-based revisit has passed

Stale handling:

1. Mark fact as stale.
2. Create a sensor event or goal update.
3. Do not silently delete history.
4. Refresh from source of truth.
5. Update tape-memory pointer only after review if needed.

## Relationship to CPOS Task Tape

CPOS Task Tape can store:

- cognitive events
- review decisions
- action proposals
- sleep consolidation records

Task Tape should not become raw log storage.

Suggested CPOS event names:

- `cognitive_sensor_event_recorded`
- `cognitive_goal_update_recorded`
- `cognitive_world_fact_refreshed`
- `cognitive_sleep_consolidation_recorded`

## Relationship to Observatory

Observatory can consume selected events for timeline/replay.

Good Observatory events:

- sensor event summaries
- state deltas
- goal transitions
- review decisions
- execution summaries

Avoid:

- raw stdout/stderr
- raw diffs
- secret-bearing payloads
- full private logs

## Relationship to tape-memory

tape-memory should store only short resume pointers such as:

- latest handoff path
- current release state in compressed form
- next action pointer
- stale/current marker

It should not store the full World Model.

## Query patterns

The World Model should answer questions like:

- What is the current CPOS release state?
- What is paused?
- What needs explicit confirmation?
- What repo is dirty?
- What containers are running?
- What article drafts exist?
- Which facts are stale?
- What should be read first next session?

## Conflict handling

If facts conflict:

1. Prefer source-of-truth docs and live checks over stale memory.
2. Mark the lower-confidence fact stale.
3. Create a `reflection_note` or `goal_update` if the conflict affects next actions.
4. Escalate if the conflict affects release/publish/destructive operations.

## Minimal future implementation sketch

Possible files later:

```text
cpos/cognitive_events.py
cpos/world_model.py
cpos/sensors/git_sensor.py
cpos/goals.py
```

Possible commands later:

```bash
PYTHONPATH=. .venv/bin/python -m cpos.world_model snapshot --json
PYTHONPATH=. .venv/bin/python -m cpos.cognitive_events record --json-file event.json
```

But implementation should wait for review. This document is only the spec draft.

## Open questions

- Should the World Model be rebuilt from Task Tape each time or stored as a snapshot?
- Should world facts have TTLs?
- How should Notion/Zenn public state be represented?
- Should VN-CPU/UNO heartbeat become `sensor_event` or `state_delta`?
- Which facts belong on the dashboard?
- Should Goal Manager own revisit reminders, or should that be a separate scheduler?
