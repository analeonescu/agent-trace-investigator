# Discovery pipeline

## Architecture

```text
raw traces
  -> normalise
  -> cheap per-trace / per-episode features
  -> candidate detectors
       | repeated actions
       | tool loops
       | test anomalies
       | reasoning/action contradictions
       | proxy errors
       | status/reward inconsistencies
       | model/run outliers
  -> compact evidence packets
  -> optional LLM investigator
  -> cross-trace aggregation
  -> human verification
```

## Why this design

Long traces should not be repeatedly sent to an LLM. Deterministic parsing can process every message cheaply. LLM calls should be reserved for ambiguous candidate episodes and given only the local evidence needed to assess them.

A candidate is stronger when it is:

- frequent enough to estimate a rate;
- concentrated in one model or run;
- supported by multiple independent traces;
- temporally linked to an observable outcome;
- absent or substantially rarer in an appropriate comparison group.

## False-positive control

1. **Require a comparison group.** A repeated read is not interesting if every model does it at the same rate.
2. **Separate observation from explanation.** The detector says what happened; the LLM may propose why.
3. **Search for counterexamples.** Every promising finding gets a denominator and examples where the behavior does not occur.
4. **Condition on task/run.** Aggregate rates can be confounded by task difficulty or run configuration.
5. **Use two-stage review.** High-recall cheap detectors followed by lower-recall semantic review.
6. **Keep uncertainty explicit.** Unknown attribution is preferable to overclaiming model causality.

## Scale

For a much larger corpus, persist episode-level records in Parquet/Arrow and compute aggregates incrementally. Candidate detectors can run independently and emit a common candidate schema. LLM judging can be batched, cached by evidence hash, and rate-limited. The raw trace never needs to enter the judge context once a compact evidence packet has been constructed.

## OpenRouter

OpenRouter exposes an OpenAI-compatible API, so the prototype uses the standard OpenAI Python client with `base_url=https://openrouter.ai/api/v1`. This makes the judge model configurable without changing the pipeline. See the OpenRouter documentation for the current API surface. citeturn0search0turn0search2

## Inspect AI

Inspect AI is optional. The forensic pipeline remains framework-independent; an adapter is provided so candidate packets can be turned into evaluator samples if desired.
