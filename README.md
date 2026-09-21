# Agent Trace Investigator

A 4-hour take-home investigation toolkit for discovering model, run, infrastructure, and grading anomalies in coding-agent traces.

## Design

The pipeline deliberately separates **high-recall deterministic discovery** from **expensive LLM interpretation**:

```text
HF traces
   |
   v
normalise -> per-trace features -> model/run/task aggregates
   |                  |
   |                  +--> transition / repetition / outcome analysis
   |
   +--> candidate detectors -----------------------+
                                                   |
                                                   v
                                        compact evidence packets
                                                   |
                                                   v
                                         optional OpenRouter LLM
                                                   |
                                                   v
                                    cross-trace aggregation + review
```

The goal is not to ask an LLM to read 370 long traces. Instead, cheap detectors surface hypotheses; LLMs inspect small, cited evidence packets and help distinguish plausible mechanisms from noise.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Load the supplied dataset and compute a feature table
ati extract

# Produce model/run/infrastructure summaries
ati summarize

# Generate candidate findings and evidence packets
ati discover

# Optional: have an OpenRouter model triage the candidates
cp .env.example .env
# add OPENROUTER_API_KEY
ati judge --limit 30
```

The dataset is loaded directly from Hugging Face by default:

```python
load_dataset("mfmVNfpt2q/agent-traces", split="train")
```

No raw traces are committed to the repository.

## Evidence standard

Every report finding should include:

1. **Observation** — exactly what is unusual.
2. **Quantification** — numerator/denominator and comparison group.
3. **Trace evidence** — trace ID, message/episode index, and compact excerpt.
4. **Attribution** — model, run, infrastructure, grader, task, or unknown.
5. **Alternative explanations** — what could produce the same pattern.
6. **Confidence** — high / medium / low, with the reason.

## Commands

### `ati extract`
Parses conversations and emits `outputs/features.csv` and `outputs/episodes.jsonl`.

### `ati summarize`
Prints model × run × status/reward tables, proxy error rates, task allocation, and feature summaries.

### `ati discover`
Runs deterministic candidate detectors for repeated tool calls, tool loops, test behavior, reasoning/action contradictions, proxy errors, status/reward mismatches, and model/run outliers. Emits `outputs/candidates.jsonl` and `outputs/evidence_packets.jsonl`.

### `ati judge`
Uses OpenRouter's OpenAI-compatible API to classify evidence packets. It is intentionally optional and bounded to candidate packets rather than whole traces.

## Optional Inspect AI integration

The repo includes a small adapter under `src/ati/inspect_bridge.py`. If `inspect-ai` is installed, the same evidence packets can be wrapped as Inspect AI samples/tasks for judge evaluation. The core pipeline does not depend on Inspect AI so that deterministic analysis remains usable even if an evaluator framework changes.

## Suggested 4-hour workflow

- 0:00–0:20 schema + extraction
- 0:20–1:00 feature engineering
- 1:00–1:30 infrastructure/run/grader analysis
- 1:30–2:15 model fingerprints and sequence analysis
- 2:15–3:00 deep-dive hypotheses + LLM verification
- 3:00–3:35 pipeline prototype
- 3:35–4:00 report and calibration
