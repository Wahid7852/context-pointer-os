# Sensor and Goal Manager Spec — Draft

This is a documentation-only specification for the first missing pieces of the Kagioneko Cognitive Agent OS:

1. software sensors
2. goal manager
3. wellbeing advisory rules
4. CPOS integration boundaries

No implementation is started by this document.

## Design principles

- Observe before acting.
- Store metadata, not raw sensitive content.
- Keep CPOS as the safety kernel.
- Keep Human Escalation as the authority for risky operations.
- Treat wellbeing support as advisory friction, not user control.
- Do not claim AGI completion.

## Sensor Layer overview

Sensors convert external state into metadata-only events.

A sensor should answer:

- What changed?
- How risky is it?
- What source-of-truth file or endpoint should be read next?
- Does this require Human Escalation?
- Is it only informational?

Sensors must not dump raw logs, secret files, raw diffs, raw stdout/stderr, `.env`, cert/key material, or token values into persistent records.

## Base sensor event schema

```json
{
  "schema": "kagioneko.sensor_event.v1",
  "event_id": "sensor_evt_...",
  "event_type": "sensor_event",
  "sensor_event_type": "git_state_changed",
  "source": "git_sensor",
  "observed_at": "2026-06-06T00:00:00+09:00",
  "subject": "repo:context-pointer-os",
  "summary": "main clean and origin synced",
  "risk": "low|medium|high|critical",
  "confidence": 0.9,
  "source_of_truth": ["NEXT_HANDOFF.md"],
  "requires_human_review": false,
  "suggested_next_action": "continue_observing",
  "metadata_only": true,
  "raw_request_stored": false,
  "raw_diff_stored": false,
  "raw_outputs_stored": false,
  "secret_values_stored": false,
  "execute_automatically": false
}
```

## Event Bus mapping

A sensor record uses `schema: kagioneko.sensor_event.v1` while following the shared
Event Bus envelope conventions: `event_type` is always `sensor_event`, `source` names
the concrete sensor such as `git_sensor`, and `sensor_event_type` carries the specific
observation such as `git_state_changed` or `git_dirty`. The Event Bus may preserve the
sensor schema as its payload schema, but it must not rename these fields or promote a
sensor observation into an action.

## Sensor types

### 1. Git sensor

Purpose: detect repo state relevant to work/resume/release.

Inputs:

- `git status --short --branch`
- `git tag --list`
- `git log --oneline -n N`
- remote URL with secret redaction

Sensor event types (`sensor_event_type`):

- `git_clean`
- `git_dirty`
- `git_ahead`
- `git_behind`
- `tag_created`
- `remote_secret_risk_detected`

Risk examples:

- clean/synced: low
- dirty with intended docs only: low/medium
- token in remote URL: high
- release tag present but release unpublished: medium

Rules:

- Never persist credential-bearing remote URLs.
- Remote URLs must be redacted before storage.
- `push`, tag creation, and release publish require explicit user confirmation.

### 2. Docker/process sensor

Purpose: observe running experiments without controlling them.

Inputs:

- container name
- image
- command
- status
- bind mounts
- ports

Events:

- `container_running`
- `container_stopped`
- `container_mounts_repo`
- `container_exposes_port`
- `cognitive_pulse_source_running`

Risk examples:

- local container with no exposed ports: low
- bind-mounted live repo with write access: medium
- exposed public port: high unless explicitly approved

Rules:

- Do not exec into containers automatically.
- Do not stop/start containers automatically.
- Do not display env values.
- VN-CPU/UNO starts as observe-only.

### 3. Time/session sensor

Purpose: support late-night and overfocus advisory friction.

Inputs:

- local time
- session duration
- user statements like “寝る”, “よふかし”, “残業”
- release/publish/tag intent during late hours

Events:

- `late_night_session`
- `long_session`
- `post_overtime_session`
- `sleep_intent_detected`
- `late_night_release_risk`

Rules:

- Be supportive, not shaming.
- Suggest pause/sleep; do not block ordinary work.
- Add extra confirmation for final release/tag/publish/destructive actions.
- Handoff memo is preferred over continuing high-stakes work late at night.

### 4. Release sensor

Purpose: track final/prerelease/draft states.

Inputs:

- local tags
- GitHub release state
- release notes/draft files
- prepublish/release_check status

Events:

- `rc_published`
- `release_draft_exists`
- `final_release_candidate_ready`
- `release_checks_stale`
- `final_release_confirmation_required`

Rules:

- Final release must not happen without explicit user confirmation.
- RC/prerelease does not imply final release.
- If tests or release docs changed, readiness checks are stale.

### 5. Filesystem/doc sensor

Purpose: know which docs/artifacts changed or became stale.

Inputs:

- tracked file changes
- untracked doc files
- ignored runtime artifact presence
- handoff/backlog freshness

Events:

- `handoff_updated`
- `backlog_created`
- `runtime_artifact_detected`
- `doc_link_missing`
- `summary_stale`

Rules:

- Do not read or print certs, keys, `.env`, token files, raw JSONL histories, or private logs.
- Use `docs/LOCAL_RUNTIME_FILE_INVENTORY.md` for local artifact policy.

### 6. Test/prepublish sensor

Purpose: summarize validation status.

Inputs:

- pytest result summary
- `cpos.prepublish_check --json`
- `cpos.release_check --json`
- secret scan count

Events:

- `tests_passed`
- `tests_failed`
- `prepublish_ok`
- `prepublish_failed`
- `release_check_ok`
- `release_check_failed`

Rules:

- Store counts/statuses only.
- Do not persist raw stdout/stderr logs.
- Failures become action proposals, not automatic fixes.

### 7. Zenn/Notion sensor

Purpose: track public narrative state.

Inputs:

- article path
- frontmatter `published`
- Notion page URL
- draft/published status

Events:

- `zenn_draft_created`
- `zenn_published`
- `notion_page_created`
- `public_copy_needs_review`

Rules:

- Do not publish articles without explicit user confirmation.
- Do not store Notion API keys or page contents with secrets.
- Store URLs and status only.

### 8. Android Emilia bridge sensor

Purpose: treat Android Emilia as a future body/environment sensor source without granting CPOS phone-control authority.

Inputs, only after explicit review:

- bridge/reference presence
- coarse app-local sensor summaries
- coarse NeuroState summaries
- diary availability metadata

Events:

- `android_emilia_bridge_detected`
- `android_emilia_status_observed`
- `android_emilia_sensor_summary_available`
- `android_emilia_privacy_review_required`

Rules:

- Start observe-only and metadata-only.
- Do not persist raw microphone/camera/location/diary content in CPOS by default.
- Do not trigger upload/publish/video pipelines automatically.
- Store receiver secrets in Vault/runtime environment only, never docs/code.
- Public publish/upload actions require Human Escalation and explicit confirmation.

### 9. User intent sensor

Purpose: interpret user shorthand and high-stakes requests.

Examples:

- `ぷす`, `ぷ`, `ふす`, `ぷぅ`: likely push intent for current safe commit, but not final release/tag/publish unless explicitly scoped.
- `寝る`: create/update handoff, suggest rest.
- `よろ`: continue recommended next safe step, but high-stakes operations still need clarity.
- `正式リリース`: final release intent; require checks and explicit confirmation.

Rules:

- Shorthand can authorize routine push only when context is clear.
- Do not treat vague shorthand as approval for final release, destructive action, port opening, user management, or `authorized_keys` changes.

## Goal Manager overview

The Goal Manager tracks what the system is trying to help with.

Goals are not self-preservation drives. They are user-aligned work items with safety constraints.

## Goal schema

```json
{
  "schema": "kagioneko.goal.v1",
  "goal_id": "cpos_v0_1_1_final",
  "title": "Decide final v0.1.1 release",
  "scope": "project|wellbeing|release|article|system",
  "state": "paused",
  "priority": "low|medium|high|critical",
  "created_at": "2026-06-06T00:00:00+09:00",
  "updated_at": "2026-06-06T00:00:00+09:00",
  "revisit_after": "2026-06-??",
  "success_criteria": ["tests pass", "prepublish ok", "user approves final release"],
  "safety_constraints": ["no final tag without explicit confirmation"],
  "source_of_truth": ["NEXT_HANDOFF.md", "GITHUB_RELEASE_DRAFT_v0.1.1.md"],
  "requires_human_confirmation": true,
  "metadata_only": true
}
```

## Goal states

| State | Meaning |
|---|---|
| `active` | Work can continue now. |
| `paused` | Intentionally resting; do not push toward action unless user resumes. |
| `blocked` | Needs missing input or external change. |
| `observing` | Watch/monitor only. |
| `ready_for_review` | Candidate exists; ask user before action. |
| `done` | No current work needed. |
| `archived` | Historical. |

## Example goals

### CPOS final v0.1.1

```json
{
  "goal_id": "cpos_v0_1_1_final",
  "title": "Move from v0.1.1-rc1 to final v0.1.1",
  "scope": "release",
  "state": "paused",
  "priority": "medium",
  "success_criteria": ["no RC issues", "335+ tests pass", "prepublish ok", "release_check ok", "explicit user confirmation"],
  "requires_human_confirmation": true
}
```

### CPOS for Agents Zenn article

```json
{
  "goal_id": "zenn_cpos_for_agents",
  "title": "Polish/publish CPOS for Agents draft",
  "scope": "article",
  "state": "ready_for_review",
  "success_criteria": ["published=false draft reviewed", "user approves publish", "no secrets"],
  "requires_human_confirmation": true
}
```

### Wellbeing late-night pause

```json
{
  "goal_id": "neko_late_night_pause",
  "title": "Reduce late-night high-stakes decisions",
  "scope": "wellbeing",
  "state": "observing",
  "success_criteria": ["handoff written", "final release decisions deferred", "user rests"],
  "requires_human_confirmation": false
}
```

## Wellbeing advisory rules

These rules are advisory friction, not control.

### Late-night caution

Trigger examples:

- user says they are sleepy, post-overtime, or late-night
- local time is late and the requested action is high-stakes
- repeated “next?” loops after release/publish work

Suggested response:

- summarize state
- offer handoff memo
- recommend rest
- defer final release/tag/publish if possible

### Long-session break

Trigger examples:

- long continuous work session
- multiple commits/pushes/releases in one session

Suggested response:

- suggest water/break/food/stretch
- keep tone light
- do not shame

### Release/tag/publish extra confirmation

Trigger examples:

- final release
- tag creation
- GitHub Release publish
- Zenn publish
- Notion public copy

Rule:

- Require explicit confirmation with concrete action name.
- Shorthand is not enough for final release unless context is already explicit and recent.

## CPOS integration

### Storage target

Sensor and goal events can be represented as CPOS Task Tape events in future implementation.

Possible review types:

- `sensor_event_review`
- `goal_update_review`
- `wellbeing_advisory`
- `release_goal_review`

### Human Escalation triggers

Escalate when:

- risk is high/critical
- action touches secrets, production, ports, systemd, users, `authorized_keys`, final release, publish, tag, push in ambiguous context
- sensor detects credential exposure risk
- goal update would grant new execution authority

### Non-escalating informational events

No escalation needed for:

- clean git status observation
- draft doc created
- tests passed summary
- local read-only repo inventory
- sleep suggestion

## Implementation boundaries

Not implemented by this spec:

- background daemon
- automatic sensors
- automatic notifications
- automatic cleanup
- automatic release/tag/publish
- direct VN-CPU control
- physical sensors

All future implementation should start read-only and metadata-only.

## Minimal future implementation sketch

Phase 1 files might be:

```text
cpos/sensors/base.py
cpos/sensors/git_sensor.py
cpos/sensors/docker_sensor.py
cpos/goals.py
```

Phase 1 commands might be:

```bash
PYTHONPATH=. .venv/bin/python -m cpos.sensors.git_sensor --json
PYTHONPATH=. .venv/bin/python -m cpos.goals list --json
```

But implementation should wait until the design is reviewed.

## Open questions

- Should goals live in Task Tape, a separate JSON file, or both?
- How should stale tape-memory pointers be detected?
- Should wellbeing advisory rules be user-configurable in a local policy file?
- How should sensor events be deduplicated?
- Which events should appear on the dashboard?
- Should VN-CPU/UNO status be imported via Docker sensor, Observatory, or External Agent Adapter?
