# Agent Trace Investigator

A forensic, scalable workflow for investigating coding-agent traces for **model behavior**, **infrastructure/evaluation failures**, and **grader anomalies** over 370 anonymised SWE-style coding-agent traces.

## Why this approach

The central design choice is to **separate high-recall discovery from expensive interpretation**:

```text
370 raw traces
      |
      v
normalise + episode extraction
      |
      +-----------------------------+
      |                             |
      v                             v
cheap behavioural features     text/sequence signals
      |                             |
      +-------------+---------------+
                    v
          candidate generation
                    |
                    v
          compact evidence packets
                    |
                    v
       optional OpenRouter / Inspect AI
                    |
                    v
       cross-trace aggregation + review
```

The pipeline never needs to put an entire long trace into one model context. LLM calls are reserved for **candidate verification and interpretation**, after deterministic/statistical detectors have reduced the search space.

## Quickstart

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Optional Inspect AI support:

```bash
pip install -e '.[inspect]'
```

### 2. Extract the supplied dataset

```bash
ati extract
```

By default this loads:

```python
load_dataset("mfmVNfpt2q/agent-traces", split="train")
```

and writes:

```text
outputs/
├── features.csv
└── episodes.jsonl
```

Raw traces are **not committed** to the repository.

### 3. Inspect the corpus

```bash
ati summarize
```

This reports model/run/status/reward tables, proxy errors, task allocation and behavioural feature summaries.

### 4. Generate candidates

```bash
ati discover
```

This currently searches for:

- repeated and looping tool calls
- retries after failed tool results
- proxy 429/error traces
- status/reward inconsistencies
- unusual per-trace behaviour
- tool/test behaviour

Outputs:

```text
outputs/candidates.jsonl
outputs/evidence_packets.jsonl
```

### 5. Optional LLM-assisted verification

```bash
cp .env.example .env
# add OPENROUTER_API_KEY
ati judge --limit 30
```

The default OpenRouter model can be overridden with:

```bash
export OPENROUTER_MODEL=google/gemini-2.5-flash
```

or:

```bash
ati judge --limit 30 --model <provider/model>
```

The supplied API key should **never** be committed. `.env` is gitignored.

## Repository layout

```text
src/ati/
├── parsing.py          # trace → episodes + low-level feature extraction
├── features.py         # dataset loading + feature-table generation
├── discover.py         # candidate detectors + evidence packets
├── reporting.py        # corpus/model/run summaries
├── llm.py              # bounded OpenRouter verification
├── inspect_bridge.py   # optional Inspect AI integration point
└── cli.py              # `ati` command line interface

analysis/
└── README.md           # recommended forensic analyses

tests/
└── test_parsing.py

findings.md             # report template / evidence standard
pipeline.md             # Part 2 architecture
```

## Evidence standard

A report finding should contain:

1. **Observation** — exactly what happened.
2. **Quantification** — numerator, denominator and comparison group.
3. **Trace evidence** — trace ID + episode/message location + excerpt.
4. **Attribution** — model, run, task, infrastructure, grader, or unknown.
5. **Alternative explanations** — plausible confounders.
6. **Confidence** — calibrated to the evidence.

A useful finding looks like:

> Model X repeats identical `bash` commands after failed results in 14/52 traces (27%), versus 3/61 (5%) for the comparison models. The effect remains after conditioning on tasks represented in both groups. The trace-level examples show the same command being retried without an intervening environment change. This supports a model-specific retry pattern, although task difficulty and tool semantics remain possible confounders.

Avoid:

> Model X is bad at tool use.

The repository is deliberately designed to make the first version easy to replace with stronger detectors as hypotheses emerge.

See [`analysis/README.md`](analysis/README.md) for concrete analyses to add during the take-home.

## Running tests

```bash
pytest -q
```
