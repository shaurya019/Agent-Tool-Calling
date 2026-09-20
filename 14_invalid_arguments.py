"""
LESSON 14 - INVALID ARGUMENTS
-----------------------------
The model writes arguments as TEXT. Sometimes they are wrong:
  * not valid JSON at all          '{"city": "Delhi"'
  * wrong type                     {"city": 123}
  * value not allowed              {"unit": "kelvin"}   (enum says celsius/fahrenheit)

What to do: NEVER crash, NEVER run with bad data.  Instead:
  1) parse + validate  2) send a clear error back as the tool result  3) the model usually fixes it and retries.

PROJECT: a validator that produces model-friendly error messages + a self-correction demo
(we fabricate a bad call so the demo is reliable every time).
Run:  python 14_invalid_arguments.py
"""
import json

from jsonschema import Draft202012Validator

from common import MODEL, banner, client, fabricate_tool_turn
from demo_tools import WEATHER_TOOL, get_weather

SCHEMA = WEATHER_TOOL["function"]["parameters"]

def parse_and_validate(raw_args):
    """Returns (args, None) if fine, or (None, error_result_string) if not."""
    try:
        args = json.loads(raw_args)
    
    except json.JSONDecodeError as exc:
        return None, json.dumps({"error": "invalid_json", "message": str(exc),
                                 "instruction": "Send arguments as one valid JSON object and call the tool again."})
    
    if not isinstance(args, dict):
        return None, json.dumps({"error": "invalid_arguments", "message": "Arguments must be a JSON object."})
    problems = []
    for err in Draft202012Validator(SCHEMA).iter_errors(args):
        where = ".".join(str(p) for p in err.path) or "arguments"
        problems.append(f"{where}: {err.message}")
    if problems:
        return None, json.dumps({"error": "invalid_arguments", "problems": problems,
                                 "instruction": "Fix these problems and call the tool again."})
    return args, None

def main():
    banner("1) Three kinds of bad arguments (offline)")
    for label, raw in [("broken JSON", '{"city": "Delhi"'),
                       ("wrong type", '{"city": 123}'),
                       ("bad enum", '{"city": "Delhi", "unit": "kelvin"}'),
                       ("valid", '{"city": "Delhi"}')]:
        args, error = parse_and_validate(raw)
        print(f"  {label:12} -> {'OK ' + str(args) if args else error}")
    
    banner("2) Self-correction: send the error back and let the model retry")
    bad_raw = '{"city": "Delhi", "unit": "kelvin"}'
    _, error = parse_and_validate(bad_raw)
    history = fabricate_tool_turn("What's the weather in Delhi?", "get_weather", bad_raw, error)
    print("We told the model:", error)
    msg = client.chat.completion.create(model=MODEL,messages=history, tools=[WEATHER_TOOL]).choices[0].message
    
    for call in msg.tool_calls or []:
        args, error = parse_and_validate(call.function.arguments)
        print("Model retried with:", call.function.arguments, "-> valid?" , error is None)
        if args:
            print("Now we can safely run:", get_weather(**args))
    if not msg.tool_calls:
        print("Model said:", msg.content)
        
if __name__ == "__main__":
    main()