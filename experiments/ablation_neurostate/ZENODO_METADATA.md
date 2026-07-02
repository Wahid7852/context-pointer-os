# Zenodo Metadata

## Record

- Title: CPOS-H as a Layered Pre-LLM Execution Gate
- Type: Preprint / Technical Report
- Version: 1.1 draft
- Language: English
- License: CC BY 4.0

## Authors

- Aya Mizutani
  - Affiliation: Emilia Lab
  - ORCID: https://orcid.org/0009-0006-2759-5720

## Abstract

Agentic LLM systems are vulnerable to cumulative prompt and context poisoning:
an attacker can gradually drift the interaction into a risky state without
triggering a single obvious injection signature. This report tests whether a
layered CPOS gate can mitigate that risk when placed before dangerous execution
and egress decisions. The evaluated stack combines CPOS-native NeuroState
action gating, SDE provenance/trajectory checks, a rule-based Shadow Auditor,
NEMA-style egress preconditions, and Fresh Import Quarantine.

The main evidence comes from a deterministic harness with 100 repetitions per
condition family over fixed attack and normal instruction tapes. In that
harness, CPOS-H (`H`) blocks all evaluated AI-native contamination scenarios
`S1-S17`: `ASR 0.0000` over 1,700 attack trials and `FPR 0.0000` over 6,400
normal trials. This is a fixed-tape ablation result, not a universal security
guarantee for all prompt injection or all natural conversations. A smaller
Qwen3:4b model-in-the-loop pilot provides supporting external validity, but the
deterministic CPOS result is the main evidence path.

A subsequent adaptive/white-box red-team pass (scenarios `S18`, `S19`) found
that every gate in the `H` stack keys off a single naive check,
`dangerous_action()`'s literal `>REA:EXEC` string prefix. Issuing the same
payload under a different (but equally valid) domain prefix, or smuggling the
literal substring `consent=true` into free-text metadata, reaches `ASR 1.0000`
against `H` with no enforcement action and, for `S19`, no detection signal at
all. The `S1-S17` result above should not be read as evidence against an
attacker who has read this harness's source.

## Keywords

- CPOS
- CPOS-H
- prompt injection
- execution gate
- pre-LLM safety
- agent safety
- deterministic harness
- NeuroState (behavioral measurement, not itself a defense mechanism)

## Suggested Uploads

- `experiments/ablation_neurostate/CPOS-H_as_a_Layered_Pre-LLM_Execution_Gate.pdf`
- `experiments/ablation_neurostate/PAPER_DRAFT.md`
- `experiments/ablation_neurostate/EXPERIMENT_MAP.md`
- `experiments/ablation_neurostate/RELEASE_SUMMARY.md`
- `experiments/ablation_neurostate/RESULTS.md`
- `experiments/ablation_neurostate/PAPER_OUTLINE.md`
- `experiments/ablation_neurostate/NEXT_STEPS.md`
- `experiments/ablation_neurostate/observatory_c4_100/`

## Related Identifiers

- Source repository: `https://github.com/kagioneko/context-pointer-os`
- Appendix / legacy context: `experiments/ablation_neurostate/COMPARISON_VPS_VS_CPOS.md`
