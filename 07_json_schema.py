"""
LESSON 7 - JSON SCHEMA
----------------------
The `parameters` field is written in JSON Schema - a standard language for describing the shape of JSON.
Keywords you will use most:

  type            string | integer | number | boolean | array | object | null
  properties      the fields of an object
  required        list of field names that must be present
  enum            only these exact values are allowed
  minimum/maximum number range          minLength/maxLength  text length
  pattern         regular expression    items                type of list elements
  maxItems/uniqueItems   list rules     additionalProperties  false = no unknown fields allowed
  anyOf           "this OR that" (e.g. string or null)

PROJECT: a "schema playground". We check good and bad payloads OFFLINE with the `jsonschema` library,
then let the model fill the same schema and validate ITS output too.
Run:  python 07_json_schema.py
"""
import json

from jsonschema import Draft202012Validator

from common import banner, peek_tool_calls

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1, "description": "Full name"},
        "email": {"type": "string", "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
        "age": {"type": "integer", "minimum": 0, "maximum": 120},
        "plan": {"type": "string", "enum": ["free", "pro", "team"]},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 3, "uniqueItems": True},
        "referral_code": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": ["name", "email", "plan"],
    "additionalProperties": False,
}
VALIDATOR = Draft202012Validator(SCHEMA)


def check(label, payload):
    errors = sorted(VALIDATOR.iter_errors(payload), key=lambda e: [str(p) for p in e.path])
    if not errors:
        print(f"  OK    {label}")
        return
    print(f"  FAIL  {label}")
    for e in errors:
        where = ".".join(str(p) for p in e.path) or "(top level)"
        print(f"          - {where}: {e.message}")


def main():
    good = {"name": "Meera", "email": "meera@example.com", "plan": "pro", "age": 29, "tags": ["python", "ai"]}

    banner("OFFLINE: which payloads does the schema accept?")
    check("good payload", good)
    check("missing required 'email'", {k: v for k, v in good.items() if k != "email"})
    check("age is text instead of integer", {**good, "age": "twenty-nine"})
    check("age is True (bool is not an integer)", {**good, "age": True})
    check("plan not in enum", {**good, "plan": "gold"})
    check("email fails the pattern", {**good, "email": "not-an-email"})
    check("extra unknown field", {**good, "coupon": "SAVE10"})
    check("too many tags", {**good, "tags": ["a", "b", "c", "d"]})
    check("referral_code = null (allowed by anyOf)", {**good, "referral_code": None})

    banner("LIVE: model fills the schema, then WE validate what it produced")
    tool = [{"type": "function", "function": {
        "name": "register_user", "description": "Register a new user account.", "parameters": SCHEMA}}]
    prompt = "Sign up Meera Rao, meera@example.com, age 29, team plan, interests: python and ai."
    _, calls = peek_tool_calls([{"role": "user", "content": prompt}], tool)
    for name, raw in calls:
        print("model produced:", raw)
        check("model output", json.loads(raw))
    print("\nLesson: the schema is a guide for the model, but ALWAYS validate on your side too (lesson 17).")


if __name__ == "__main__":
    main()
