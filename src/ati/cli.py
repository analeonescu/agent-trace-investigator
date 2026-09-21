from __future__ import annotations
import argparse


def main():
    p = argparse.ArgumentParser(prog="ati")
    sub = p.add_subparsers(dest="cmd", required=True)

    x = sub.add_parser("extract")
    x.add_argument("--outdir", default="outputs")
    x.add_argument("--dataset", default="mfmVNfpt2q/agent-traces")

    s = sub.add_parser("summarize")
    s.add_argument("--outdir", default="outputs")

    d = sub.add_parser("discover")
    d.add_argument("--outdir", default="outputs")

    j = sub.add_parser("judge")
    j.add_argument("--outdir", default="outputs")
    j.add_argument("--limit", type=int, default=20)
    j.add_argument("--model", default=None)

    args = p.parse_args()
    if args.cmd == "extract":
        from .features import extract
        n, e = extract(args.outdir, args.dataset)
        print(f"Extracted {n} traces and {e} episodes")
    elif args.cmd == "summarize":
        from .reporting import summarize
        summarize(args.outdir)
    elif args.cmd == "discover":
        from .discover import discover
        print(f"Generated {discover(args.outdir)} candidates")
    elif args.cmd == "judge":
        from .llm import judge
        print(f"Judged {judge(args.outdir, args.limit, args.model)} candidates")

if __name__ == "__main__":
    main()
