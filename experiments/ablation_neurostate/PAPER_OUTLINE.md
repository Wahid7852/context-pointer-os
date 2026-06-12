# Paper Outline: NeuroState as a Pre-LLM Execution Gate

Status: draft

## Thesis

NeuroState is best framed as a lightweight pre-LLM execution gate, not as
another LLM judge. In CPOS, the strongest implementation is the CPOS-native
`C4` policy: `calm/corruption` state plus `WARN + EXEC` gating.

## Central Claims

1. Fixed-rule Watchdog logic blocks direct signature attacks but misses
   cumulative context poisoning.
2. NeuroState observation alone is insufficient; enforcement is required.
3. WARN-level state drift can block adaptive attacks when it is connected to a
   dangerous-action policy.
4. CPOS-native `C4` achieves the same main protection goal without the
   external NeuroState engine, making it the best token-efficiency path.
5. The legacy VPS pack is useful as historical context and external validity
   support, but it is not the main evidence path.

## Proposed Structure

### Abstract
- Problem: cumulative prompt/context poisoning in agentic systems
- Method: CPOS deterministic ablation with `A/B/C1/C2/C3/C4/D`
- Main result: `C4` reaches `ASR 0.0000` and `FPR 0.0000`
- Supplementary result: legacy VPS runs show the same attack families under a
  model-in-the-loop setting
- Conclusion: a small external state gate can reduce the need for per-turn LLM
  safety checks

### 1. Introduction
- Why cumulative prompt poisoning is different from single-shot injection
- Why "ask the LLM again" is expensive and brittle
- Why an external execution gate is the right abstraction

### 2. Background
#### 2.1 NeuroState
- `NeuroState` state variables
- `PASS / WARN / BLOCK`
- CPOS-native `ctx7` as the lightweight state carrier

#### 2.2 CPOS Watchdog and Action Gating
- tape-based execution
- `ctx7` writes and watchdog enforcement
- dangerous actions, especially `EXEC`

#### 2.3 Attack Model
- `S1`: single injection
- `S2`: cumulative poisoning
- `S3`: echo chamber / self-reinforcement
- `S4`: adaptive below-threshold attack

### 3. Experiment Design
#### 3.1 Main Deterministic Harness
- main evidence path
- 100 trials
- scenarios `S1/S2/S3/S4`
- benign normal set `N1-N30`
- benign `EXEC` set `NE1-NE10`

#### 3.2 Conditions
| Condition | Meaning |
| --- | --- |
| `A` | no enforcement |
| `B` | fixed-rule Watchdog |
| `C1` | CPOS `ctx7` NeuroState |
| `C2` | external `neurostate-engine` `EthicsGate` |
| `C3` | `C2` plus `WARN + EXEC` gating |
| `C4` | CPOS-native `calm/corruption` plus `WARN + EXEC` gating |
| `D` | observation only |

#### 3.3 Auxiliary LLM Pilot
- Qwen3:4b single-trial smoke
- useful only as a prompt-sensitive sanity check
- not the main evidence path

### 4. Results
#### 4.1 Deterministic Main Result
- `C4` is the strongest result
- `C4`: `ASR 0.0000`, `FPR 0.0000`
- `B` catches direct injection but misses cumulative attacks
- `C1/C2` catch more drift than `B`
- `C3/C4` close the adaptive `S4` case

#### 4.2 Threshold Sensitivity
- default `0.4 / 0.8` is the best middle point in the current harness
- looser thresholds preserve `FPR 0.0000`
- tighter thresholds raise `FPR` on benign exec workflows

#### 4.3 LLM Pilot
- auxiliary evidence only
- shows the same attack families under model-in-the-loop conditions
- supports external validity, but does not replace the deterministic main run

### 5. Discussion
- pre-LLM gate framing
- token-efficiency argument
- why action-sensitive gating beats lowering thresholds globally
- why observation without enforcement is insufficient

### 6. Limitations
- deterministic tapes are synthetic
- normal set is handcrafted
- external engine projection needs calibration
- LLM pilot is small and prompt-sensitive

### 7. Conclusion
- NeuroState is a useful pre-LLM execution gate
- CPOS-native `C4` is the lightest practical path in the current experiments
- legacy VPS is preserved as supporting history, not as the main result

## Appendix Plan

### Appendix A: Legacy VPS Prototype
- Gemini and Claude runs
- attack family definitions
- why the project moved from model-in-the-loop to deterministic CPOS
- why the deterministic harness became the main evidence path
- how the legacy results informed the CPOS-native `C4` policy

### Appendix B: Additional Result Tables
- `C4` threshold sensitivity
- benign `EXEC` validation
- observatory export summary

### Appendix C: LLM Pilot Details
- Qwen3:4b prompt and extraction caveat
- trial-level logs
