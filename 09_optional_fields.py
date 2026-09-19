"""
LESSON 9 - OPTIONAL FIELDS
--------------------------
Optional fields = properties that are NOT in `required`. The model may skip them.
  * Say the default in the description ("Defaults to price").
  * Apply the default in YOUR code - never assume the model filled it.
  * Do not make things optional if skipping them causes wrong results.
  * In STRICT mode you cannot leave a field out; instead make its type nullable: ["integer", "null"].

PROJECT: hotel search. Watch which optional fields the model fills for different sentences,
then use `apply_defaults()` to complete the arguments safely.
Run:  python 09_optional_fields.py
"""
import json

from common import banner, peek_tool_calls

HOTEL_TOOL = {
    "type": "function",
    "function": {
        "name": "search_hotels",
        "description": "Search hotels in a city. Only 'city' is needed; the rest are optional filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "max_price": {"type": "integer", "description": "Max price per night in INR. Omit if the user gave no budget."},
                "stars": {"type": "integer", "minimum": 1, "maximum": 5, "description": "Minimum star rating. Omit if not mentioned."},
                "sort_by": {"type": "string", "enum": ["price", "rating"], "default": "price"},
            },
            "required": ["city"],
        },
    },
}

STRICT_HOTEL = {
    "type": "function",
    "function": {
        "name": "search_hotels",
        "description": "Search hotels in a city. Use null for filters the user did not mention.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "max_price": {"type": ["integer", "null"]},
                "stars": {"type": ["integer", "null"]},
                "sort_by": {"type": ["string", "null"], "enum": ["price", "rating", None]},
            },
            "required": ["city", "max_price", "stars", "sort_by"],
            "additionalProperties": False,
        },
    },
}


def apply_defaults(schema, args):
    """Fill missing optional fields using the "default" values declared in the schema."""
    filled = dict(args)
    for field, spec in schema["properties"].items():
        if field not in filled and "default" in spec:
            filled[field] = spec["default"]
    return filled


def main():
    schema = HOTEL_TOOL["function"]["parameters"]
    prompts = [
        "Hotels in Goa please.",
        "4-star hotels in Goa under 8000 rupees, sorted by rating.",
    ]
    banner("Optional fields: only filled when the user says something about them")
    for p in prompts:
        _, calls = peek_tool_calls([{"role": "user", "content": p}], [HOTEL_TOOL])
        print(f"\nUser: {p}")
        for _, raw in calls:
            args = json.loads(raw)
            print("  model args      :", args)
            print("  after defaults  :", apply_defaults(schema, args))

    banner("STRICT mode: optional becomes 'nullable' and the model must send every field")
    try:
        _, calls = peek_tool_calls([{"role": "user", "content": prompts[0]}], [STRICT_HOTEL])
        print("strict call:", calls)
    except Exception as err:   # e.g. a model that does not support strict
        print("Strict call failed on this model:", err)


if __name__ == "__main__":
    main()
