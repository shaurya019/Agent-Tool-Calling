"""
LESSON 23 - TOOL RESULT SIZE LIMITS
-----------------------------------
Everything you return goes into the model's context window (limited!) and you pay for the tokens.
A tool that returns 5,000 log lines can overflow the context, cost a lot, and hide the answer.

Strategies:
  1) TRUNCATE  - cut the result to a maximum size (cut whole items, and SAY it was cut)
  2) PAGINATE  - give tools offset/limit so the model can ask for the next page
  3) SUMMARISE - give counts/aggregates via a separate tool (count_logs) instead of raw rows
  4) FILTER    - let the model search with filters instead of dumping everything
  Rough rule of thumb: 1 token ~ 4 characters of English.

PROJECT: a log-search assistant over 5,000 fake log lines.
Run:  python 23_tool_result_size_limits.py
"""
import json
import random

from common import banner, run_tool_loop

MAX_CHARS = 4000      # about 1,000 tokens

_rng = random.Random(42)
LOGS = [{"id": i, "level": _rng.choice(["INFO", "INFO", "INFO", "WARN", "ERROR"]),
         "service": _rng.choice(["api", "db", "auth"]), "message": f"request {i} took {_rng.randint(5, 900)}ms"}
        for i in range(5000)]


def count_logs(level):
    return {"level": level, "count": sum(1 for log in LOGS if log["level"] == level)}


def search_logs(level, offset=0, limit=10):
    limit = min(limit, 50)
    matches = [log for log in LOGS if log["level"] == level]
    page = matches[offset:offset + limit]
    more = offset + limit < len(matches)
    return {"total_matches": len(matches), "offset": offset, "returned": len(page),
            "next_offset": offset + limit if more else None, "logs": page}


def limit_result(data, max_chars=MAX_CHARS, hint="Use offset/limit or filters to see more."):
    """Safety net for ANY tool: never send more than max_chars, and say when something was cut."""
    text = json.dumps(data)
    if len(text) <= max_chars:
        return text
    if isinstance(data, list):                         # cut whole items, not half a JSON object
        kept, size = [], 0
        for item in data:
            item_size = len(json.dumps(item)) + 1
            if size + item_size > max_chars - 300:
                break
            kept.append(item)
            size += item_size
        return json.dumps({"truncated": True, "shown": len(kept), "total": len(data), "items": kept, "hint": hint})
    return json.dumps({"truncated": True, "original_chars": len(text), "preview": text[:max_chars - 300], "hint": hint})


TOOLS = [
    {"type": "function", "function": {
        "name": "count_logs", "description": "Count log lines of a given level. Use for 'how many' questions.",
        "parameters": {"type": "object", "properties": {"level": {"type": "string", "enum": ["INFO", "WARN", "ERROR"]}},
                       "required": ["level"]}}},
    {"type": "function", "function": {
        "name": "search_logs", "description": "Return log lines of a level, one page at a time (max 50 per page). "
                                              "Use next_offset from the result to get the next page.",
        "parameters": {"type": "object", "properties": {
            "level": {"type": "string", "enum": ["INFO", "WARN", "ERROR"]},
            "offset": {"type": "integer", "minimum": 0, "description": "Start position, default 0"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Page size, default 10"}},
            "required": ["level"]}}},
]
REGISTRY = {"count_logs": count_logs, "search_logs": search_logs}


def executor(name, raw_args, call_id):
    try:
        return limit_result(REGISTRY[name](**json.loads(raw_args)))    # the safety net wraps EVERY tool
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def main():
    banner("1) The problem: dump everything")
    everything = json.dumps(LOGS)
    print(f"{len(everything):,} characters ~ {len(everything) // 4:,} tokens. Too big!")

    banner("2) The safety net: limit_result()")
    limited = limit_result(LOGS)
    print(f"{len(limited):,} characters ~ {len(limited) // 4:,} tokens. Starts with: {limited[:120]}...")

    banner("3) Live: count + paginate instead of dumping")
    messages = [{"role": "user", "content": "How many ERROR logs are there? Show me the first 3 of them."}]
    print("Assistant:", run_tool_loop(messages, TOOLS, executor))


if __name__ == "__main__":
    main()
