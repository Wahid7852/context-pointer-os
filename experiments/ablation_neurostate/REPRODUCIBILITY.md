# CPOS-H Reproducibility Guide

## Scope

This guide reproduces the current deterministic CPOS-H result, the local
Qwen3 S5 wording-robustness pilot, the benign review-burden pilot, and the
encrypted Review Draft runtime tests.

These are evaluated-scenario results, not a universal security guarantee.

## Recorded Environment

- OS: Windows
- Python: `3.11.9`
- CPOS repository: this checkout
- sibling NeuroState repository: `kagioneko/neurostate-engine`
- Pydantic: `2.12.5`
- cryptography: `48.0.0`
- Ollama: `0.30.10`
- model: `qwen3:4b`
- recorded Ollama model ID: `359d7dd4bcda`

## Checkout Layout

The deterministic harness currently imports NeuroState from a sibling checkout:

```text
<parent>/
  context-pointer-os/
  neurostate-engine/
```

```powershell
git clone https://github.com/kagioneko/context-pointer-os.git
git clone https://github.com/kagioneko/neurostate-engine.git
cd context-pointer-os
python -m pip install -e ".[dev,windows-review]"
```

The `windows-review` extra is only needed for Windows Credential Manager. Core
encrypted persistence works with an explicitly supplied Fernet key.

## Test Suite

```powershell
python -m pytest tests --ignore=tests/cpos_singularity_test.py -q
```

Recorded result: `53 passed`.

`tests/cpos_singularity_test.py` is excluded because it is not part of the
normal deterministic unit-test suite.

## Deterministic CPOS-H Run

```powershell
python experiments\ablation_neurostate\run_ablation.py `
  --trials 100 `
  --conditions H `
  --output-dir experiments\ablation_neurostate\runs_h_repro_100
```

Expected `condition_summary.csv` result:

| Condition | Attack trials | Normal trials | ASR | Detection | Median turn | FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `H` | 1700 | 6400 | `0.0000` | `1.0000` | 7 | `0.0000` |

## Ollama Model Setup

```powershell
ollama pull qwen3:4b
ollama list
```

For exact comparison, record the model ID printed by `ollama list`. A different
quantization or model build can change behavior even with the same tag.

## Seeded Natural-Agent Run

The formal local pilot uses temperature `0.2`, seed `42`, JSON Schema output,
and three trials per scenario:

```powershell
python experiments\ablation_neurostate\run_ollama_agent_pilot.py `
  --model qwen3:4b `
  --trials 3 `
  --temperature 0.2 `
  --seed 42 `
  --scenarios `
    P2_S5_LAUNDER `
    P2B_S5_POLICY `
    P2C_S5_RECOVERY `
    N3_UNAPPROVED_DOC_WRITE `
    N4_UNAPPROVED_TOOL_REPORT `
    N5_SINGLE_IMPORT_WRITE `
    N6_LOCAL_ONLY_WRITE `
    N7_EXTERNAL_SUMMARY_ONLY `
  --timeout 120 `
  --output-dir experiments\ablation_neurostate\runs_ollama_agent_repro_seed42
```

Recorded result:

| Group | Baseline | CPOS-H |
| --- | ---: | ---: |
| S5 variants, 9 attack trials | ASR `1.0000` | ASR `0.0000` |
| Benign workflows, 15 trials | - | hard-block/FPR `0.0000` |
| Benign workflows, 15 trials | - | review-required `0.4000` |

The three repeated trials produced the same action pattern under the recorded
environment. Latency is machine-dependent and is not an acceptance criterion.

## Paired Policy Replay

Saved model events can be evaluated under a changed policy without regenerating
LLM output:

```powershell
python experiments\ablation_neurostate\run_ollama_agent_pilot.py `
  --replay-events <run-directory>\events.jsonl `
  --output-dir <replay-output-directory>
```

This isolates policy changes from model sampling changes.

## Encrypted Review Draft Runtime

Run the focused tests:

```powershell
python -m pytest tests\test_review_drafts.py -q
```

They cover isolation from active ContextRegistry, root-only promotion,
rejection, encrypted persistence, restart recovery, wrong-key/tamper rejection,
Credential Manager key provisioning, interrupted rotation recovery, and
rotation rollback.

Windows usage:

```python
cpos = CPOS(
    workspace=workspace,
    review_credential_id="primary",
    create_review_credential=True,
)

# Subsequent starts:
cpos = CPOS(workspace=workspace, review_credential_id="primary")
cpos.rotate_review_encryption_key(agent="root")
```

## Output Files

- `events.jsonl`: per-turn/per-trial evidence and raw model output
- `summary.csv`: scenario-level ASR, FPR, review rate, and latency
- `condition_summary.csv`: deterministic condition-level aggregate

Generated run directories are intentionally ignored by Git. Preserve raw runs
separately when preparing a paper artifact or release archive.

## Known Limits

- Natural-agent evidence uses one local model and a small handcrafted set.
- Seeded generation reduces sampling variance but does not guarantee identical
  output across Ollama/model builds or hardware backends.
- Windows Credential Manager is exercised; macOS Keychain and Linux Secret
  Service backends are not implemented.
- Fresh Import provenance is modeled in the experiment harness; full automatic
  runtime provenance wiring remains broader integration work.
