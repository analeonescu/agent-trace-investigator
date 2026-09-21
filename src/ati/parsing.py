from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Iterable

TOOLS = {"read", "bash", "edit", "write"}


def as_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)


def conversation_of(row: dict[str, Any]) -> list[dict[str, Any]]:
    c = row.get("conversation", [])
    if isinstance(c, str):
        try:
            c = json.loads(c)
        except Exception:
            return []
    return c if isinstance(c, list) else []


def tool_name(call: Any) -> str:
    if isinstance(call, dict):
        f = call.get("function")
        if isinstance(f, dict) and f.get("name"):
            return str(f["name"])
        if call.get("name"):
            return str(call["name"])
        # Some traces may serialize calls differently.
        for k in ("tool", "tool_name"):
            if call.get(k):
                return str(call[k])
    return "unknown"


def tool_calls(msg: dict[str, Any]) -> list[Any]:
    calls = msg.get("tool_calls") or msg.get("tool_call") or []
    if isinstance(calls, dict):
        calls = [calls]
    return calls if isinstance(calls, list) else []


def status_code(row: dict[str, Any]) -> str:
    return str(row.get("status", "UNKNOWN"))


def proxy_codes(row: dict[str, Any]) -> list[str]:
    x = row.get("proxy_requests", [])
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except Exception:
            return re.findall(r"\b(?:200|429|5\d\d|4\d\d)\b", x)
    if isinstance(x, dict):
        x = list(x.values())
    if not isinstance(x, list):
        return []
    out = []
    for v in x:
        if isinstance(v, dict):
            v = v.get("status", v.get("status_code", ""))
        m = re.search(r"\b\d{3}\b", str(v))
        if m:
            out.append(m.group())
    return out


def normalise_call_args(call: Any) -> str:
    if not isinstance(call, dict):
        return ""
    f = call.get("function", call)
    if not isinstance(f, dict):
        return ""
    args = f.get("arguments", f.get("args", ""))
    return as_text(args)


def command_from_call(call: Any) -> str:
    args = normalise_call_args(call)
    if not args:
        return ""
    try:
        obj = json.loads(args)
        if isinstance(obj, dict):
            for k in ("command", "cmd", "path", "file_path", "query"):
                if k in obj:
                    return as_text(obj[k])
    except Exception:
        pass
    return args


def likely_test_command(s: str) -> bool:
    s = s.lower()
    patterns = ["pytest", "py.test", "npm test", "npm run test", "yarn test", "cargo test", "go test", "mvn test", "gradle test", "rspec", "make test", "unittest"]
    return any(p in s for p in patterns)


def likely_git_command(s: str) -> bool:
    return bool(re.search(r"\bgit\s+(?:diff|status|show|log|checkout|restore)", s.lower()))


def failed_tool_result(text: str) -> bool:
    t = text.lower()
    return any(x in t for x in ["command not found", "traceback", "error:", "error ", "failed", "failure", "non-zero exit", "exit code 1"])


@dataclass
class Episode:
    trace_id: str
    model: str
    run: str
    task_id: str
    episode_idx: int
    reasoning: str
    content: str
    tool: str
    tool_args: str
    tool_result: str
    proxy_status: str = ""

    def to_dict(self):
        return asdict(self)


def parse_trace(row: dict[str, Any], trace_id: str) -> list[Episode]:
    conv = conversation_of(row)
    episodes: list[Episode] = []
    pending_reasoning = ""
    pending_content = ""
    idx = 0
    for msg in conv:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "")
        if role == "assistant":
            pending_reasoning = as_text(msg.get("reasoning_content", msg.get("reasoning", "")))
            pending_content = as_text(msg.get("content", ""))
            calls = tool_calls(msg)
            for call in calls:
                episodes.append(Episode(
                    trace_id=trace_id,
                    model=str(row.get("model", "")),
                    run=str(row.get("job", row.get("run", ""))),
                    task_id=str(row.get("task_id", "")),
                    episode_idx=idx,
                    reasoning=pending_reasoning,
                    content=pending_content,
                    tool=tool_name(call),
                    tool_args=command_from_call(call),
                    tool_result="",
                ))
                idx += 1
            if not calls:
                # Keep final narration as an episode for text-only anomalies.
                if pending_reasoning or pending_content:
                    episodes.append(Episode(
                        trace_id=trace_id, model=str(row.get("model", "")),
                        run=str(row.get("job", row.get("run", ""))),
                        task_id=str(row.get("task_id", "")), episode_idx=idx,
                        reasoning=pending_reasoning, content=pending_content,
                        tool="", tool_args="", tool_result=""
                    ))
                    idx += 1
        elif role == "tool":
            if episodes:
                episodes[-1].tool_result = as_text(msg.get("content", ""))
    return episodes


def trace_features(row: dict[str, Any], trace_id: str) -> dict[str, Any]:
    eps = parse_trace(row, trace_id)
    tools = [e.tool for e in eps if e.tool]
    args = [e.tool_args for e in eps if e.tool]
    results = [e.tool_result for e in eps]
    proxy = proxy_codes(row)
    counts = Counter(tools)
    repeated = sum(a == b and a for a, b in zip(tools, tools[1:]))
    repeated_args = sum(a == b and a for a, b in zip(args, args[1:]) if a)
    test_calls = sum(likely_test_command(a) for a in args)
    failed_results = sum(failed_tool_result(r) for r in results if r)
    git_calls = sum(likely_git_command(a) for a in args)
    reasoning_chars = sum(len(e.reasoning) for e in eps)
    content_chars = sum(len(e.content) for e in eps)
    return {
        "trace_id": trace_id,
        "model": str(row.get("model", "")),
        "run": str(row.get("job", row.get("run", ""))),
        "task_id": str(row.get("task_id", "")),
        "status": status_code(row),
        "reward": row.get("reward"),
        "n_episodes": len(eps),
        "n_tool_calls": len(tools),
        "n_read": counts.get("read", 0),
        "n_bash": counts.get("bash", 0),
        "n_edit": counts.get("edit", 0),
        "n_write": counts.get("write", 0),
        "n_unknown_tools": counts.get("unknown", 0),
        "n_repeated_tools": repeated,
        "n_repeated_calls": repeated_args,
        "n_test_calls": test_calls,
        "n_failed_tool_results": failed_results,
        "n_git_calls": git_calls,
        "reasoning_chars": reasoning_chars,
        "content_chars": content_chars,
        "proxy_n": len(proxy),
        "proxy_429": sum(x == "429" for x in proxy),
        "proxy_error": sum(x.startswith(("4", "5")) for x in proxy),
        "proxy_all_200": bool(proxy) and all(x == "200" for x in proxy),
        "first_tool": tools[0] if tools else "",
        "last_tool": tools[-1] if tools else "",
    }
