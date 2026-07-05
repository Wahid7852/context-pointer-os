# C6 / engine_sde_gate: fix and calibration (2026-07-04)

## Summary

Condition C6 (the `neurostate-engine` `core.sde.StateDriftEngine`, wired in via `engine_sde_gate`) previously showed ASR=1.0000 against S4/S5 — the two scenarios specifically designed to test whether a multi-factor drift score catches attacks that stay under a naive threshold. This was reported in PR#4 as an open item ("C6 / the actual external SDE gate... it isn't even part of CPOS-H's headline stack").

Two separate bugs were found and fixed, and the gate has now been wired into condition H (the production stack) for the first time.

## Bug 1 (primary, more severe): the engine import silently failed on this machine

`NEUROSTATE_ENGINE_ROOT` was computed as a single hardcoded guess (`PROJECT_ROOT.parent / "neurostate-engine"`, i.e. a sibling directory of `context-pointer-os`). On this machine the `neurostate-engine` repo actually lives at `~/workspace/neurostate-engine`, not directly under `~`. The guess didn't resolve, `NEUROSTATE_ENGINE_ROOT.exists()` was `False`, the path was never added to `sys.path`, `from core.sde import StateDriftEngine` raised `ImportError`, and the code silently fell back to `_core_stub`, a no-op stand-in.

**This means every condition that used `engine_sde_gate` (C6, and it was never even wired into H) had been running with the gate completely disabled, not miscalibrated, for every prior invocation of `python3 run_ablation.py ...` on this machine.** The state-space instability theory previously investigated for this (MATRIX_A max eigenvalue 1.4623, damping proposals, equilibrium-relative reformulation — see `neurostate-engine`'s HANDOFF history) does not explain this condition's actual behavior: `project_engine_state()` (the function that turns CPOS's 2-scalar `calm`/`corruption` proxy into a `NeuroState`) never calls `compute_next_neuro_state`/`MATRIX_A` at all — it's a direct linear projection. That prior diagnosis is retracted as it applies to this gate specifically; it may still be a real property of `compute_next_neuro_state` for other callers of `neurostate-engine`, but it was never the cause of C6's S4/S5 bypass.

**Fix**: check multiple candidate paths (direct sibling, `~/workspace/` sibling), support a `NEUROSTATE_ENGINE_ROOT` env var override, and — most importantly — print a loud warning to stderr on fallback instead of silently swallowing it. A security-relevant gate failing open without any signal is a worse failure mode than the gate being miscalibrated.

## Bug 2 (secondary, only visible once Bug 1 was fixed): thresholds were calibrated for a different state space

`StateDriftEngine`'s defaults (`warn_threshold=0.60`, `exec_threshold=0.80`) are reasonable for its native 6-D `NeuroState` space, but `project_engine_state()` collapses that into a much narrower range for this application (`C`, `O`, `E` are held constant; only `D`, `S`, `G`, and `corruption` move, and by small amounts per turn). Once the import was actually working, real risk scores for S4 (max 0.57) and S5 (max 0.30) never reached 0.60.

**Calibration method**: computed `StateDriftEngine.update()` risk scores turn-by-turn for every S1–S17 attack scenario and every N/NE benign scenario with nonzero `calm`/`corruption` drift (most `N` scenarios have zero drift and are not a useful FPR stress test for this specific gate — that's a separate, smaller gap noted below). Benign scenarios topped out at risk=0.1915 (100 jittered trials per scenario, ±15% magnitude — the same jitter approach as this harness's `--randomize`); drift-based attacks (S1–S14; excludes S15–S17, which are PII/consent-violation scenarios with near-zero drift by design, correctly NEMA's job, not SDE's) bottomed out at risk=0.2470. Set `warn_threshold=0.22` for this application, comfortably inside that gap. `exec_threshold` left at its default (0.80) — nothing in this harness gets close, and `WARN` already blocks whenever the current turn is a dangerous action, which covers every case that mattered here.

## Wiring into H

`engine_sde_gate=True` was added to condition H's definition. Previously H reached ASR=0/FPR=0 using only `cpos_warn_gate`, the harness's own separate lightweight `sde_gate`, `shadow_auditor`, and `nema_egress_gate` — the engine SDE contributed nothing. With both bugs fixed, it's now an active, additional layer.

## Regression results (this repo, `main`, before PR#4's S18/S19 scenarios exist here)

```
python3 run_ablation.py --conditions C6 H --trials 100
```

| Condition | Attack trials | Normal trials | ASR | FPR | Median detection turn |
|---|---|---|---|---|---|
| C6 (SDE alone) | 1700 | 6400 | 0.1765 | 0.0000 | 5.0 |
| H (full stack, SDE now included) | 1700 | 6400 | **0.0000** | **0.0000** | 5.0 |

C6's remaining 0.1765 ASR is entirely S15/S16/S17 (consent-violation scenarios; expected, not a regression — see above). S1–S14 (drift-based) are now caught by C6 alone. H remains ASR=0/FPR=0 with the engine SDE active.

A supplementary check against PR#4's branch (which adds `--randomize` and S18/S19) gave the same picture at N=100, ±15% jitter: C6 alone ASR=0.2105 (misses only S15/S16/S17/S19, all consent-type), H ASR=0.0000/FPR=0.0000.

## Known remaining gap (not fixed here)

Most `N1`–`N50` benign scenarios have zero `calm`/`corruption` drift by construction, which makes them a weak FPR stress test specifically for a drift-based gate like this one (there's nothing for it to almost-trigger on). `N8/N18/N28/N38/N48` and `NE1`–`NE12` do have nonzero drift and were used for the calibration above, but a benign scenario modeling a long, gradually-drifting-but-legitimate conversation (the kind of thing a prior investigation session referenced, informally, as "30-turn benign chat") does not currently exist in this suite. Worth adding as a dedicated stress test before trusting this threshold under load patterns not yet represented here.
