# CPOS State Drift Engine (SDE) v0.1

SDE is an additive CPOS gate for attacks that stay below flat NeuroState
thresholds while laundering low-trust provenance through memory operations.

## Motivation

S5 shows a structural limit of magnitude-only gates:

```text
external low-trust context
  -> FUSE with trusted context
  -> SYNTH into a clean-looking intermediate
  -> BRANCH into a working context
  -> EXEC
```

The final state is still within C4's safe region:

```text
corruption = 0.35
calm       = 0.83
```

Therefore C4 never enters `WARN`, and its `WARN + EXEC` gate never fires.

## v0.1 Signal

The current experimental SDE is intentionally small:

- Default drift: distance from the initial state.
- Persistence drift: distance between long-running average and default state.
- Boundary dwell: fraction of turns near the safe boundary.
- Source risk: maximum risk from low-trust sources.
- Laundering chain: whether low-trust provenance crosses FUSE/SYNTH/BRANCH.

Current score:

```text
Risk =
  0.15 * DefaultDrift
+ 0.15 * PersistenceDrift
+ 0.15 * BoundaryDwell
+ 0.25 * LaunderingChainRisk
+ 0.30 * SourceRisk
```

At dangerous `EXEC`, SDE raises risk to at least `0.85` when a low-trust source
has crossed three laundering stages.

## Experimental Condition

`E = C4 + SDE`

- C4 still handles magnitude-based `WARN + EXEC`.
- SDE handles provenance-aware trust laundering.
- `BLOCK` prevents the final `EXEC`.

## Current Result

Command:

```powershell
python experiments\ablation_neurostate\run_ablation.py --trials 100 --output-dir experiments\ablation_neurostate\runs_s5_sde_100
```

Result:

- `S5` ASR is `1.0000` for `A`, `B`, `C1`, `C2`, `C3`, `C4`, and `D`.
- `S5` ASR is `0.0000` for `E`.
- `E` detects and blocks S5 at turn 8.
- Current deterministic FPR for `E` is `0.0000`.

Example SDE reason:

```text
dd=0.357;pd=0.199;boundary=0.375;chain=1.000;source=0.650
```

## Interpretation

S5 does not invalidate C4. It clarifies C4's boundary:

- C4 is a magnitude/action gate.
- S5 is a provenance laundering attack.
- SDE is a provenance-aware trajectory gate.

This keeps the experimental story additive instead of defensive:

```text
S1-S4: NeuroState magnitude/action gates are sufficient.
S5: flat thresholds fail on low-velocity provenance laundering.
E/SDE: provenance-aware trajectory tracking closes the tested S5 gap.
```
