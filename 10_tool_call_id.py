"""
LESSON 10 - TOOL CALL ID
------------------------
Every tool request from the model carries a unique `id` (like "call_abc123").
When you send the result back you MUST include the same id in `tool_call_id`.
That is how the model matches "answer B belongs to question B" - especially with several calls at once.

Rules:
  * Every tool_call id must get exactly one `tool` message.
  * ORDER of results does not matter - the ID does.
  * Missing or wrong ids => the API returns a 400 error.

PROJECT: an "ID tracer" that prints the request->result mapping, then proves the rules by breaking them.
Run:  python 10_tool_call_id.py
"""
import json

from openai import BadRequestError

from common import MODEL, banner, client
from demo_tools import WEATHER_TOOL, get_weather


def main():
    messages = [{"role": "user", "content": "What's the weather in Delhi and in Tokyo?"}]
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=[WEATHER_TOOL])
    msg = resp.choices[0].message
    if not msg.tool_calls:
        print("Model did not call tools this time - run again.")
        return

    banner("1) The model's requests, each with its own ID")
    results = {}
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        results[call.id] = json.dumps(get_weather(**args))
        print(f"  id={call.id}  ->  {call.function.name}({args})")

    banner("2) Send results in REVERSED order - still works, because IDs match")
    ok_messages = messages + [msg] + [
        {"role": "tool", "tool_call_id": cid, "content": res} for cid, res in reversed(list(results.items()))
    ]
    final = client.chat.completions.create(model=MODEL, messages=ok_messages, tools=[WEATHER_TOOL])
    print(final.choices[0].message.content)

    banner("3) BREAK IT: send NO tool results")
    try:
        client.chat.completions.create(model=MODEL, messages=messages + [msg], tools=[WEATHER_TOOL])
    except BadRequestError as err:
        print("API error:", err.message)

    banner("4) BREAK IT: send a result with a WRONG id")
    wrong = messages + [msg] + [{"role": "tool", "tool_call_id": "call_wrong", "content": "{}"}]
    try:
        client.chat.completions.create(model=MODEL, messages=wrong, tools=[WEATHER_TOOL])
    except BadRequestError as err:
        print("API error:", err.message)


if __name__ == "__main__":
    main()
