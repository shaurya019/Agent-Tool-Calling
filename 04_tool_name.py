"""
LESSON 4 - TOOL NAME
--------------------
The name is the FIRST thing the model reads. Rules & habits:

  * Allowed: letters, digits, underscore, dash. Max 64 characters. No spaces!
  * Use  verb_noun  in snake_case:  get_weather, cancel_order, search_products
  * Be specific. `data`, `run`, `tool1`, `helper` tell the model nothing.
  * Names should be different enough from each other that they cannot be confused.

PROJECT: (a) a tiny name "linter", (b) see the API reject a bad name,
         (c) an experiment: same tools with bad names vs good names - does the model still pick right?
Run:  python 04_tool_name.py
"""
import re

from openai import BadRequestError

from common import MODEL, banner, client, peek_tool_calls

ALLOWED = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
VAGUE = {"do_it", "run", "tool", "data", "helper", "function", "execute", "process", "handle"}


def lint_tool_name(name):
    problems = []
    if not ALLOWED.match(name):
        problems.append("illegal: use 1-64 chars of letters, digits, _ or -")
    if name.lower() in VAGUE or re.fullmatch(r"(tool|fn|func)\d*_?[a-z]?\d*", name.lower()):
        problems.append("too vague: says nothing about what it does")
    if ALLOWED.match(name) and "_" not in name:
        problems.append("style: prefer verb_noun (get_weather)")
    if name != name.lower():
        problems.append("style: prefer lowercase snake_case")
    return problems or ["looks good"]


def order_tools(status_name, cancel_name):
    """Same parameters, NO descriptions - so only the names can guide the model."""
    params = {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}
    return [
        {"type": "function", "function": {"name": status_name, "parameters": params}},
        {"type": "function", "function": {"name": cancel_name, "parameters": params}},
    ]


def main():
    banner("(a) Name linter")
    for n in ["get_weather", "get weather!", "data", "tool1", "GetWeather", "cancelOrder", "search_products"]:
        print(f"  {n!r:20} -> {'; '.join(lint_tool_name(n))}")

    banner("(b) What does the API say about an illegal name?")
    bad = [{"type": "function", "function": {"name": "get weather!", "description": "x",
                                             "parameters": {"type": "object", "properties": {}}}}]
    try:
        client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": "hi"}], tools=bad)
    except BadRequestError as err:
        print("API rejected it:", err.message)

    banner("(c) Names alone: vague vs clear")
    question = [{"role": "user", "content": "Where is my order A100? I have not received it."}]
    for label, tools in [("VAGUE  (tool_a / tool_b)", order_tools("tool_a", "tool_b")),
                         ("CLEAR  (get_order_status / cancel_order)", order_tools("get_order_status", "cancel_order"))]:
        picks = []
        for _ in range(3):   # ask 3 times to see if it is consistent
            _, calls = peek_tool_calls(question, tools)
            picks.append(calls[0][0] if calls else "none")
        print(f"  {label:45} -> {picks}")
    print("\nWith vague names the model has to guess. Clear names = fewer wrong calls.")


if __name__ == "__main__":
    main()
