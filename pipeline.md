# Discovery pipeline design

## Objective

Automatically surface unusual, reproducible and potentially consequential behaviours from long coding-agent traces without putting every trace into an LLM context window.

## Architecture

```text
                 raw traces
                     |
                     v
          schema normalisation
                     |
                     v
          episode-level records
                     |
        +------------+-------------+
        |                          |
        v                          v
 deterministic features       text statistics
        |                          |
        +------------+-------------+
                     |
                     v
             candidate detectors
                     |
                     v
             evidence packets
                     |
                     v
          LLM candidate review
                     |
                     v
           cross-trace aggregation
                     |
                     v
              human verification
```

## Candidate detectors

### Deterministic

- exact/repeated tool calls
- repeated commands after failures
- tool transition anomalies
- test strategy anomalies
- unusual edit/write behaviour
- proxy error/429 events
- status/reward inconsistencies
- trace-level robust outliers

### Statistical

- model-vs-rest feature contrasts
- model × run interaction effects
- within-task comparisons
- log-odds / TF-IDF language contrasts
- sequence n-grams
- clustering/outlier detection

### LLM-assisted

The LLM receives a compact evidence packet rather than the whole trace:

```json
{
  "candidate_id": "...",
  "metadata": {"model": "...", "run": "...", "task_id": "..."},
  "hypothesis": "...",
  "evidence": {
    "reasoning": "...",
    "content": "...",
    "tool": "...",
    "tool_args": "...",
    "tool_result": "..."
  }
}
```

The judge must separately return:

1. directly observed behaviour
2. interpretation
3. likely attribution
4. alternative explanations
5. confidence
6. a follow-up test

## False-positive control

A candidate should not become a report finding solely because an LLM calls it interesting. Promote candidates using:

- prevalence above a minimum threshold
- model/run specificity
- reproducibility across independent traces
- strength of local evidence
- counterexample search
- confound checks
- human verification for high-impact findings

For a model-specific claim, compare against both:

1. all other models, and
2. the same tasks where available.

For an infrastructure claim, compare runs and models jointly.

## Scaling

The pipeline is embarrassingly parallel at the trace and candidate level. A production version would use a columnar feature store for trace-level data and a queue for LLM candidate review. Cache evidence packets and judge outputs by content hash so repeated investigations do not incur repeated API cost.

A useful scaling hierarchy is:

```text
all traces
  ↓  cheap parsing
all episodes
  ↓  deterministic detectors
1–10% candidate episodes
  ↓  statistical aggregation
hundreds of evidence packets
  ↓  LLM review
small set of verified findings
```

The exact percentages should be measured rather than assumed on a larger corpus.
