"""
LESSON 11 - TOOL RESULT
-----------------------
A tool result is your answer to the model's request. It is a message with:

    {"role": "tool", "tool_call_id": "<same id>", "content": "<a STRING>"}

  * content must be TEXT. Python dicts must be turned into a string (json.dumps).
  * The model has never seen your data before - the result is its ONLY knowledge of what happened.
  * Always answer, even on failure (send an error result, never send nothing).
  * A consistent "envelope" makes results easy for the model (and for you) to understand.

PROJECT: result "envelope" helpers  tool_ok() / tool_error()  and a demo that shows what happens
if you forget json.dumps.
Run:  python 11_tool_result.py
"""
import json

from openai import BadRequestError

from common import MODEL, banner, client
from demo_tools import WEATHER_TOOL, get_weather


def tool_ok(data):
    return json.dumps({"ok": True, "data": data})


def tool_error(code, message, hint=None):
    return json.dumps({"ok": False, "error": {"code": code, "message": message, "hint": hint}})


def main():
    messages = [{"role": "user", "content": "What's the weather in Paris?"}]
    resp = client.chat.completions.create(model=MODEL, messages=messages, tools=[WEATHER_TOOL])
    msg = resp.choices[0].message
    if not msg.tool_calls:
        print("Model did not call the tool - run again.")
        return
    call = msg.tool_calls[0]
    data = get_weather(**json.loads(call.function.arguments))

    banner("MISTAKE: content is a Python dict, not a string")
    try:
        client.chat.completions.create(
            model=MODEL, tools=[WEATHER_TOOL],
            messages=messages + [msg, {"role": "tool", "tool_call_id": call.id, "content": data}])
    except BadRequestError as err:
        print("API error:", err.message)
    except Exception as err:
        print("Error:", type(err).__name__, err)

    banner("CORRECT: success envelope")
    good = messages + [msg, {"role": "tool", "tool_call_id": call.id, "content": tool_ok(data)}]
    print("tool message content:", good[-1]["content"])
    print("Assistant:", client.chat.completions.create(model=MODEL, messages=good, tools=[WEATHER_TOOL]).choices[0].message.content)

    banner("CORRECT: error envelope (the model explains the failure kindly)")
    err_msg = tool_error("city_not_found", "No weather data for 'Paris'.", "Ask the user for a nearby big city.")
    bad = messages + [msg, {"role": "tool", "tool_call_id": call.id, "content": err_msg}]
    print("tool message content:", bad[-1]["content"])
    print("Assistant:", client.chat.completions.create(model=MODEL, messages=bad, tools=[WEATHER_TOOL]).choices[0].message.content)


if __name__ == "__main__":
    main()
