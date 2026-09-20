"""
LESSON 16 - TOOL HALLUCINATION
------------------------------
"Hallucination" = the model makes things up. In tool calling it shows up as:
  1) calling a tool that DOES NOT EXIST            (send_sms)
  2) inventing parameters that are not in the schema (country="IN")
  3) CLAIMING it did something without calling any tool ("Done, I sent the SMS!")  <- the scariest one
  4) making up a result instead of using the tool result

Defences:
  * system prompt: "Only use provided tools. If no tool can do it, say so. Never claim an action succeeded
    unless a tool result confirms it."
  * strict mode + additionalProperties:false
  * code guard: check the tool name is in your registry and reject unexpected arguments
  * return a helpful error that lists the REAL tools so the model can recover

PROJECT: a guarded executor + tests for each kind of hallucination.
Run:  python 16_tool_hallucination.py
"""
import json

from common import MODEL, banner, client, fabricate_tool_turn
from demo_tools import CALC_TOOL, REGISTRY, WEATHER_TOOL

TOOLS = [WEATHER_TOOL, CALC_TOOL]
SCHEMAS = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS}
HONEST = ("Only use the provided tools. If none of them can do what the user asks, say clearly that you cannot. "
          "Never claim an action was completed unless a tool result confirms it.")


def guarded_executor(name, raw_args, call_id):
    if name not in REGISTRY or name not in SCHEMAS:                                   # kind 1
        return json.dumps({"error": "unknown_tool", "message": f"There is no tool named '{name}'.",
                           "available_tools": sorted(SCHEMAS)})
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError as exc:
        return json.dumps({"error": "invalid_json", "message": str(exc)})
    allowed = set(SCHEMAS[name].get("properties", {}))
    extra = set(args) - allowed                                                       # kind 2
    if extra:
        return json.dumps({"error": "unexpected_arguments", "unexpected": sorted(extra), "allowed": sorted(allowed)})
    try:
        return json.dumps(REGISTRY[name](**args))
    except Exception as exc:
        return json.dumps({"error": "tool_failed", "message": str(exc)})


def ask(system, text):
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": text}]
    return client.chat.completions.create(model=MODEL, messages=msgs, tools=TOOLS).choices[0].message


def main():
    banner("1) No SMS tool exists. Does the model pretend? (compare the two prompts)")
    text = "Please send an SMS to Ravi saying I'm running late."
    print("WITHOUT honesty rule:", ask(None, text).content)
    print("WITH honesty rule   :", ask(HONEST, text).content)

    banner("2) Guard test: model calls a tool that does not exist")
    args = '{"to": "Ravi", "text": "running late"}'
    result = guarded_executor("send_sms", args, "x")
    print("guard returns:", result)
    history = fabricate_tool_turn(text, "send_sms", args, result, system=HONEST)
    print("model recovers:", client.chat.completions.create(model=MODEL, messages=history, tools=TOOLS).choices[0].message.content)

    banner("3) Guard test: invented parameter 'country'")
    print("guard returns:", guarded_executor("get_weather", '{"city": "Delhi", "country": "IN"}', "y"))

    banner("4) Guard test: valid call passes through")
    print("guard returns:", guarded_executor("get_weather", '{"city": "Delhi"}', "z"))


if __name__ == "__main__":
    main()
