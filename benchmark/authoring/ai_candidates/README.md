# AI-drafted benchmark candidates (DEC-041)

This folder holds **AI-drafted candidate** items only. They never enter the locked Gold/test set directly, and `tools/benchmark.py` never loads this folder as authoring input.

## Required fields on every item

The usual item fields, plus:

```yaml
origin: AI_DRAFT
model: <exact model id>
prompt_version: <id of the prompt file used>
timestamp: <ISO-8601 UTC>
evidence_source_ids: [EVD-…]      # or literature cand_ids; empty only for abstain items
status: UNVERIFIED                # → REVIEWED → EVIDENCE_CHECKED → REWRITTEN → ADJUDICATED → BENCHMARK_CANDIDATE
```

## Promotion path

```text
AI draft → human review → source/evidence verification → human rewrite where needed
→ answer adjudication → duplicate/leakage audit → BENCHMARK_CANDIDATE → (moved to ../) → freeze
```

An item may be moved up into `benchmark/authoring/` only with:
- `status: BENCHMARK_CANDIDATE`;
- `human_reviewer: <name>`;
- `rewrite_note: <what was changed, or "none needed">`.

The validator rejects an `AI_DRAFT` item in `authoring/` that lacks these.

## Analysis

Human-authored and AI-drafted pools stay distinguishable by their `origin` field, so results can be reported per origin. This tests whether the origin of an item affects its difficulty or model performance. It matters because the system under test is itself an LLM.
