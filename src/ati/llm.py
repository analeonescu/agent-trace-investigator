from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SYSTEM = """You are a forensic analyst of coding-agent traces. Evaluate one candidate at a time. Do not invent evidence. Distinguish: (1) directly observed behavior, (2) interpretation, and (3) hypotheses about cause. Consider model, run, task, infrastructure and grader explanations. A finding should be unusual, reproducible, or consequential, not merely surprising. Return JSON with keys: verdict, observation, likely_attribution, alternative_explanations, confidence, followup_test."""


def judge(outdir="outputs", limit=20, model=None):
    from openai import OpenAI
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENROUTER_API_KEY before running ati judge")
    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = model or os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    client = OpenAI(base_url=base_url, api_key=api_key)
    packets = []
    with (Path(outdir) / "evidence_packets.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): packets.append(json.loads(line))
    packets = packets[:limit]
    results = []
    for p in packets:
        prompt = json.dumps(p, ensure_ascii=False, indent=2)
        r = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        content = r.choices[0].message.content or "{}"
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw": content}
        results.append({"candidate_id": p["candidate_id"], "model": model, "judgement": parsed})
    path = Path(outdir) / "llm_judgements.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in results: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(results)
