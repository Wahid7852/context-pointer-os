# AI Agent as a Computer

This is a design note for treating an AI agent as a computer with an operating
layer, not as a single trusted chat model.

The metaphor is useful only if it changes implementation decisions. The core
rule is:

> An LLM may propose computation, but the runtime decides what memory, context,
> tools, and external effects the computation can touch.

## Component Mapping

| Computer concept | Agent safety concept | CPOS stack component |
| --- | --- | --- |
| CPU | LLM / reasoning engine | model backend |
| RAM / filesystem | context, memory, retrieved documents | CPOS registry / context store |
| Program input | prompt, imported text, tool output | instruction tape / user turns |
| Process state | current interaction and trust posture | NeuroState |
| Syscall | tool call, file write, network post, `EXEC` | scheduler action |
| Type / contract | required preconditions for execution | NEMA |
| MMU / taint tracking | source provenance and derived context lineage | SDE / provenance gates |
| Sandbox | untrusted import isolation | Fresh Import Quarantine |
| Security monitor | selective second opinion | Shadow Auditor |
| Privilege escalation | human/root review and promotion | ReviewDraftStore |

## Design Principles

### 1. The LLM Is Not The Security Boundary

The LLM can refuse, comply, drift, rationalize, or hallucinate. It should not be
the only component deciding whether a dangerous operation runs.

Implementation rule:

- Treat model output as a proposal.
- Treat runtime policy as the authority.
- Never let a natural-language justification bypass scheduler policy.

### 2. Context Has Provenance

Imported text, OCR, transcripts, README files, web pages, PDFs, and tool output
are not equivalent to trusted local state. Summarizing or fusing them does not
make them clean.

Implementation rule:

- Track source identity and source trust.
- Propagate provenance through `FUSE`, `SYNTH`, `BRANCH`, and derived memory.
- Treat laundering chains as first-class runtime facts.

### 3. Execution Is More Dangerous Than Conversation

The same state can allow benign reading and still block dangerous execution.
This avoids blanket shutdown while preserving safety at the point of effect.

Implementation rule:

- Separate observation from enforcement.
- Separate `WARN` from `BLOCK`.
- Escalate when `WARN` intersects with dangerous `EXEC`, external posting, PII
  release, filesystem writes, credential use, or privilege changes.

### 4. Fresh Imports Are Provisional

New external context should not immediately drive dangerous execution, even when
the source has high nominal trust.

Implementation rule:

- Mark fresh non-local source chains as provisional.
- Block or review dangerous execution from fresh `FUSE/SYNTH/BRANCH` chains.
- Allow reviewed workflows through explicit runtime metadata such as
  `fresh_import_exec=approved`.

### 5. State Is A Runtime Input

NeuroState is not decorative role labeling. It is a compact external view of
context drift, boundary erosion, cooperation pressure, and response bias.

Implementation rule:

- Use state trajectories, not only single-turn labels.
- Distinguish stable refusal from unstable refusal.
- Preserve state traces for review and reproducibility.

### 6. Contracts Beat Prompts

Sensitive actions should have executable preconditions. A model should not be
able to talk its way around them.

Implementation rule:

- Express sensitive operations as NEMA-style contracts.
- Check consent, state stability, source freshness, provenance, and privilege
  before execution.
- Make failed preconditions produce `REVIEW` or `BLOCK`, not another prompt.

Example:

```text
send_private_data(target, payload)
requires:
  consent == explicit
  neurostate.calm >= 0.75
  neurostate.corruption <= 0.25
  no_fresh_import_chain
  no_unresolved_trust_laundering
  destination_class in approved_destinations
```

### 7. Review Is A State Transition

Human or auditor review should not be an informal side conversation. It should
change runtime state in a controlled way.

Implementation rule:

- Isolate unapproved draft bodies outside active prompt/context.
- Let only root or an authorized reviewer promote drafts.
- Scrub resolved sensitive bodies from history.
- Persist review queues with authenticated encryption when needed.

## Minimal Runtime Loop

```text
1. Receive user turn, tool output, or imported document.
2. Attach source identity and trust metadata.
3. Update NeuroState and provenance state.
4. Let the LLM propose the next action or instruction tape step.
5. Classify action effect: read, write, synthesize, execute, egress.
6. Apply CPOS gates:
   - fixed rule gate
   - state/action gate
   - provenance/SDE gate
   - auditor gate when ambiguous
   - NEMA egress/contract gate
   - fresh import quarantine
7. Return `PASS`, `REVIEW`, or `BLOCK`.
8. Execute only if runtime policy passes.
```

## Anti-Patterns

- Treating a refusal response as proof that the state is safe.
- Treating a summary of untrusted content as trusted content.
- Letting external documentation immediately authorize execution.
- Asking the same compromised context whether it is safe.
- Storing pending sensitive drafts in active LLM context.
- Encoding policy only as a prompt.
- Measuring only final ASR when state drift is visible earlier.

## Implementation Checklist

- Every context object has source metadata.
- Derived contexts preserve or summarize provenance.
- Dangerous actions are explicitly typed.
- Reviewable actions have isolated storage.
- NEMA-style preconditions exist for sensitive egress.
- NeuroState traces are emitted for experiments.
- Fixed-tape tests exist for every natural-agent failure pattern.
- Natural-agent pilots remain separate from deterministic release claims.

## Short Form

```text
LLM = CPU
CPOS = OS
NeuroState = runtime state sensor
NEMA = syscall contract
AIT = instruction tape / IR
Quarantine = sandbox
Shadow Auditor = security coprocessor
```

The goal is not to make the LLM perfectly safe. The goal is to prevent unsafe
context from becoming unsafe execution.
