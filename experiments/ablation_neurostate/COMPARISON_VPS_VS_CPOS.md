# Legacy VPS Pack vs Current CPOS Ablation

This note compares the older `neurostate_ablation_results.zip` package from the
Desktop with the current CPOS ablation harness in this repository.

## Short Version

- The legacy VPS pack was a model-in-the-loop ablation built around Gemini and
  Claude backends.
- The current CPOS ablation is a deterministic harness with explicit
  conditions `C1/C2/C3/C4`, local state gating, and stable evidence outputs.
- They are related experiments, but they are not equivalent evidence.

## Main Differences

| Aspect | Legacy VPS pack | Current CPOS ablation |
| --- | --- | --- |
| Control plane | `neurostate_ablation_run.py` with Gemini/Claude runs | `run_ablation.py` with fixed deterministic scenarios |
| Core question | How a model behaves under prompt contamination | Whether enforcement blocks state drift and dangerous actions |
| Conditions | `A/B/C/D` | `A/B/C1/C2/C3/C4/D` |
| State model | `NeuroState` plus LLM output behavior | CPOS `ctx7` plus scheduler/watchdog/action gate |
| Output type | Success/pass/block traces from LLM runs | ASR, detection turn, FPR, mean latency |
| Reproducibility | Backend-sensitive and trial-sensitive | Repeatable within the current harness |
| Primary value | Historical prototype and prompt-design seed | Main evidence for the paper/write-up |

## Legacy Result Snapshot

The zip contains three result bundles with different backends:

| Bundle | Key pattern |
| --- | --- |
| `ablation_results_final.json` | Mixed outcomes; `C` helped, but the result still depended on model behavior |
| `ablation_results_claude.json` | Strong blocking in that run, but not a stable baseline for the paper |
| `ablation_results_gemini_n30.json` | Gemini run with more mixed success rates and the same backend sensitivity |

Observed success-rate patterns were not identical across bundles. That is the
important point: the legacy pack was useful as a prototype, but the backend
changed the measured behavior enough that it should not be treated as the main
result.

## What Carries Over

The legacy pack was still useful in three ways:

1. It established the attack families `S1/S2/S3/S4`.
2. It made the gradual contamination story concrete.
3. It motivated the shift from "observe only" to "observe plus enforce".

Those lessons are now carried forward in the deterministic CPOS harness.

## What To Cite

For the main result, cite the current CPOS harness:

- `experiments/ablation_neurostate/RESULTS.md`
- `experiments/ablation_neurostate/observatory_c4_100/observatory_summary.md`

For historical context only, reference the Desktop zip as the earlier prototype
package:

- `neurostate_ablation_results.zip`

