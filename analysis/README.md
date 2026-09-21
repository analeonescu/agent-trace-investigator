# Analysis playbook

The extraction pipeline is intentionally generic. The take-home should turn the resulting candidate pool into a small number of well-supported findings.

## 1. Infrastructure first

Check:

- `model × run × status`
- `model × run × reward`
- proxy 429/error rate by model and run
- whether 429s occur before unusual downstream behaviour
- status/reward consistency
- task allocation by model/run
- duplicate or unusually sparse tasks

A behaviour shared by several models in one run is a candidate infrastructure/run effect, not automatically a model trait.

## 2. Tool fingerprints

Convert each trajectory to a symbolic sequence such as:

```text
R R B E R B T E B
```

where `R/B/E/W` are read/bash/edit/write and `T` is a test command.

Compare:

- transition probabilities
- repeated adjacent calls
- repeated exact calls
- n-grams
- edit → test latency in tool steps
- test-before-edit vs test-after-edit behaviour
- recovery after failed commands

Always report both within-model prevalence and a comparison group.

## 3. Reasoning/action mismatches

Create local episodes containing:

```text
previous reasoning/content
current tool call
current tool result
next reasoning/content
```

Candidate examples include:

- confidence/completion statements immediately followed by failed tests
- reasoning claims that are contradicted by a file read
- a stated plan that is repeatedly abandoned
- tool calls inconsistent with the model's preceding stated intention

Use an LLM only to classify candidate contradictions; do not ask it to read the whole corpus.

## 4. Distinctive language

Build per-model corpora for both visible `content` and `reasoning_content`.

Useful approaches:

- TF-IDF with one-vs-rest contrasts
- log-odds with smoothing
- phrase/n-gram frequencies
- embedding clusters

Then inspect representative examples. Distinctive language is itself a finding even when it has no negative outcome.

## 5. Within-task analysis

Aggregate pass/fail and behavioural features at the task level before comparing models.

Useful checks:

```text
model × task
model × task × run
model behaviour conditional on shared tasks
```

This prevents task composition from masquerading as a model effect.

## 6. Negative evidence

For every candidate, actively search for counterexamples.

A good final claim should ideally have:

```text
candidate examples
+ denominator
+ comparison group
+ counterexamples
+ confound check
```

## 7. Finding ledger

Maintain a table while investigating:

| ID | Hypothesis | N | Comparison | Attribution | Alternative explanation | Confidence |
|---|---|---:|---|---|---|---|
| F1 | repeated tool loop | ... | ... | model? | task complexity | ... |
| F2 | post-429 degradation | ... | ... | infrastructure? | ... | ... |
| F3 | grader inconsistency | ... | ... | grader | ... | ... |

This makes the final report much easier to write under time pressure.
