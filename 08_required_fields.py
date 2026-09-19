"""
LESSON 8 - REQUIRED FIELDS
--------------------------
`"required": [...]` lists the parameters the tool cannot work without.
  * Put a parameter in `required` only if the function truly needs it.
  * If the user did not give a required value, a good model asks a question... or a bad one guesses.
    So YOU must also check on your side (see lesson 15).
  * STRICT MODE ("strict": true): every property must be listed in `required`, and
    `additionalProperties` must be false. "Optional" is then written as a nullable type (lesson 9).

PROJECT: flight-search tool with 3 required fields. We test 3 prompts (complete / partly missing / empty)
and write `missing_required()` to detect gaps.
Run:  python 08_required_fields.py
"""
import json

from common import banner, peek_tool_calls

FLIGHT_TOOL = {
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": "Search flights. Needs origin city, destination city and travel date.",
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Departure city"},
                "destination": {"type": "string", "description": "Arrival city"},
                "date": {"type": "string", "description": "Travel date, YYYY-MM-DD"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
}

STRICT_VERSION = {
    "type": "function",
    "function": {
        "name": "search_flights",
        "description": "Search flights.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": ["origin", "destination", "date"],   # strict: ALL fields must be here
            "additionalProperties": False,                    # strict: must be false
        },
    },
}


def missing_required(schema, args):
    """Return the names of required fields that are absent or empty."""
    return [f for f in schema.get("required", []) if args.get(f) in (None, "")]


def main():
    schema = FLIGHT_TOOL["function"]["parameters"]
    system = {"role": "system", "content": "Today is 2026-09-19. Use the tool when you have everything you need; otherwise ask the user."}
    prompts = [
        "Find flights from Delhi to Goa on 2026-10-05.",
        "Find me a flight to Goa.",
        "I want to travel somewhere warm.",
    ]
    banner("Required fields in action")
    for p in prompts:
        msg, calls = peek_tool_calls([system, {"role": "user", "content": p}], [FLIGHT_TOOL])
        print(f"\nUser: {p}")
        if not calls:
            print("  model did NOT call the tool. It says:", msg.content)
        for name, raw in calls:
            args = json.loads(raw)
            print(f"  model calls {name}({args})  missing={missing_required(schema, args)}")

    banner("Strict-mode version of the same schema")
    print(json.dumps(STRICT_VERSION, indent=2))
    msg, calls = peek_tool_calls([system, {"role": "user", "content": prompts[0]}], [STRICT_VERSION])
    print("\nstrict call:", calls)


if __name__ == "__main__":
    main()
