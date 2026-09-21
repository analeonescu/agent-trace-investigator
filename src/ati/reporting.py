from __future__ import annotations
from pathlib import Path
import pandas as pd


def summarize(outdir="outputs"):
    df = pd.read_csv(Path(outdir) / "features.csv")
    pd.set_option("display.max_rows", 100)
    print("\n=== MODEL × STATUS ===")
    print(pd.crosstab(df.model, df.status))
    print("\n=== MODEL × REWARD ===")
    print(pd.crosstab(df.model, df.reward))
    print("\n=== RUN × STATUS ===")
    print(pd.crosstab(df.run, df.status))
    print("\n=== MODEL × RUN (trace count) ===")
    print(pd.crosstab(df.model, df.run))
    print("\n=== PROXY ERRORS BY MODEL ===")
    print(df.groupby("model")["proxy_429"].agg(["sum", "mean", "count"]))
    print("\n=== FEATURE MEDIANS BY MODEL ===")
    cols = ["n_tool_calls", "n_repeated_calls", "n_test_calls", "n_failed_tool_results", "reasoning_chars", "content_chars"]
    print(df.groupby("model")[cols].median().round(1))
    print("\n=== STATUS/REWARD CROSS-TAB ===")
    print(pd.crosstab(df.status, df.reward))
