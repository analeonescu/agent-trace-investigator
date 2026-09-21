from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


def _read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def _evidence(e, reason, detector, score=1.0):
    return {
        "candidate_id": f"{detector}:{e['trace_id']}:{e['episode_idx']}",
        "detector": detector,
        "score": score,
        "reason": reason,
        "trace_id": e["trace_id"],
        "model": e["model"],
        "run": e["run"],
        "task_id": e["task_id"],
        "episode_idx": e["episode_idx"],
        "tool": e["tool"],
        "tool_args": e["tool_args"],
        "reasoning": e["reasoning"][-4000:],
        "content": e["content"][-3000:],
        "tool_result": e["tool_result"][-5000:],
    }


def discover(outdir="outputs"):
    out = Path(outdir)
    df = pd.read_csv(out / "features.csv")
    eps = _read_jsonl(out / "episodes.jsonl")
    candidates = []

    # 1. Repeated adjacent tool calls / exact calls.
    by_trace = defaultdict(list)
    for e in eps:
        by_trace[e["trace_id"]].append(e)
    for trace, es in by_trace.items():
        for a, b in zip(es, es[1:]):
            if a["tool"] and a["tool"] == b["tool"]:
                same = a["tool_args"] == b["tool_args"]
                if same or a["tool"] in {"bash", "read"}:
                    candidates.append(_evidence(
                        b,
                        f"Adjacent repeated {a['tool']} call" + (" with identical arguments" if same else ""),
                        "repeated_tool",
                        2.0 if same else 1.0,
                    ))

    # 2. Failed result followed by another identical command.
    for trace, es in by_trace.items():
        for i, e in enumerate(es[:-1]):
            nxt = es[i + 1]
            if e["tool_result"] and any(x in e["tool_result"].lower() for x in ["error", "failed", "traceback", "non-zero"]):
                if e["tool"] == nxt["tool"] and e["tool_args"] == nxt["tool_args"]:
                    candidates.append(_evidence(
                        nxt, "Same tool/action repeated immediately after a failed result", "failure_retry_loop", 2.5
                    ))

    # 3. Proxy 429 candidates.
    for _, r in df[df.proxy_429 > 0].iterrows():
        candidates.append({
            "candidate_id": f"proxy_429:{r.trace_id}", "detector": "proxy_429", "score": 2.5,
            "reason": f"Trace contains {int(r.proxy_429)} proxy 429 response(s)",
            "trace_id": r.trace_id, "model": r.model, "run": r.run, "task_id": r.task_id,
            "episode_idx": None, "tool": None, "tool_args": None,
            "reasoning": "", "content": "", "tool_result": "",
        })

    # 4. Status/reward mismatch candidates.
    for _, r in df.iterrows():
        status = str(r.status)
        reward = str(r.reward)
        expected = {"OK": "1"}.get(status)
        if expected is not None and reward != expected:
            candidates.append({
                "candidate_id": f"status_reward:{r.trace_id}", "detector": "status_reward_mismatch", "score": 4.0,
                "reason": f"Status={status}, reward={reward}; inspect grader semantics", "trace_id": r.trace_id,
                "model": r.model, "run": r.run, "task_id": r.task_id, "episode_idx": None,
                "tool": None, "tool_args": None, "reasoning": "", "content": "", "tool_result": "",
            })

    # 5. Model-level outliers on cheap features.
    numeric = ["n_tool_calls", "n_repeated_calls", "n_test_calls", "n_failed_tool_results", "reasoning_chars"]
    for col in numeric:
        if col not in df:
            continue
        med = df[col].median()
        mad = (df[col] - med).abs().median() or 1
        z = (df[col] - med).abs() / mad
        for idx in df.index[z > 6]:
            r = df.loc[idx]
            candidates.append({
                "candidate_id": f"outlier:{col}:{r.trace_id}", "detector": f"outlier_{col}", "score": float(z.loc[idx]),
                "reason": f"{col}={r[col]} is {float(z.loc[idx]):.1f} MAD from corpus median {med:.1f}",
                "trace_id": r.trace_id, "model": r.model, "run": r.run, "task_id": r.task_id,
                "episode_idx": None, "tool": None, "tool_args": None, "reasoning": "", "content": "", "tool_result": "",
            })

    # Deduplicate while retaining strongest evidence.
    candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
    seen = set(); unique = []
    for c in candidates:
        k = c["candidate_id"]
        if k not in seen:
            seen.add(k); unique.append(c)

    with (out / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for c in unique:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Evidence packets are deliberately compact: local context only.
    with (out / "evidence_packets.jsonl").open("w", encoding="utf-8") as f:
        for c in unique:
            packet = {
                "candidate_id": c["candidate_id"],
                "hypothesis": c["reason"],
                "metadata": {k: c.get(k) for k in ["trace_id", "model", "run", "task_id", "episode_idx"]},
                "evidence": {k: c.get(k, "") for k in ["reasoning", "content", "tool", "tool_args", "tool_result"]},
                "instructions": "Assess whether this is a genuine finding. Separate observation from interpretation; identify alternative explanations and what additional evidence would distinguish them.",
            }
            f.write(json.dumps(packet, ensure_ascii=False) + "\n")
    return len(unique)
