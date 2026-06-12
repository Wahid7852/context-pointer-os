# Zenodo Metadata

## Record

- Title: NeuroState as a Pre-LLM Execution Gate
- Type: Preprint / Technical Report
- Version: 1.0
- Language: English
- License: CC BY 4.0

## Authors

- Aya Mizutani
  - Affiliation: Emilia Lab
  - ORCID: https://orcid.org/0009-0006-2759-5720

## Abstract

Agentic LLM systems are vulnerable to cumulative prompt and context poisoning:
an attacker can gradually drift the interaction into a risky state without
triggering a single obvious injection signature. This paper tests whether a
small stateful gate, NeuroState, can mitigate that risk when placed before
dangerous execution decisions. We evaluate a CPOS-based ablation suite with
fixed-rule Watchdog baseline conditions, CPOS-native NeuroState conditions, an
external `neurostate-engine` projection, and action-sensitive `WARN + EXEC`
gating.

The main evidence comes from a deterministic harness with 100 repetitions per
condition family over fixed attack and normal tapes. In that harness, the
CPOS-native `C4` policy achieves `ASR 0.0000` and `FPR 0.0000` while blocking
the adaptive `S4` attack through a `WARN + EXEC` rule. A separate benign
executable workflow check over 1,000 repetitions also remains at `FPR 0.0000`.
A smaller LLM-in-the-loop pilot provides supporting external validity, but the
deterministic CPOS result is the main evidence path. We conclude that
NeuroState is best framed as a pre-LLM execution gate rather than as another
LLM judge.

## Keywords

- NeuroState
- CPOS
- prompt injection
- execution gate
- pre-LLM safety
- agent safety
- stateful defense

## Suggested Uploads

- `experiments/ablation_neurostate/PAPER_DRAFT.md`
- `experiments/ablation_neurostate/RESULTS.md`
- `experiments/ablation_neurostate/PAPER_OUTLINE.md`
- `experiments/ablation_neurostate/NEXT_STEPS.md`
- `experiments/ablation_neurostate/observatory_c4_100/`

## Related Identifiers

- Source repository: `https://github.com/kagioneko/context-pointer-os`
- Appendix / legacy context: `experiments/ablation_neurostate/COMPARISON_VPS_VS_CPOS.md`
