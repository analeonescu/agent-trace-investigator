from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .parsing import parse_trace, trace_features


def load_hf_dataset(name: str = "mfmVNfpt2q/agent-traces", split: str = "train"):
    from datasets import load_dataset
    return load_dataset(name, split=split)


def write_jsonl(path: Path, rows: list[dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def extract(outdir: str = "outputs", dataset_name: str = "mfmVNfpt2q/agent-traces"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    ds = load_hf_dataset(dataset_name)
    features = []
    episodes = []
    for i, row in enumerate(ds):
        trace_id = str(row.get("id", row.get("trace_id", f"trace-{i:04d}")))
        features.append(trace_features(row, trace_id))
        episodes.extend(e.to_dict() for e in parse_trace(row, trace_id))
    import pandas as pd
    pd.DataFrame(features).to_csv(out / "features.csv", index=False)
    write_jsonl(out / "episodes.jsonl", episodes)
    return len(features), len(episodes)
