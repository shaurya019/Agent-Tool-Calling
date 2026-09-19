"""
LESSON 3 - TOOL SCHEMA
----------------------
A tool schema is the "instruction card" you give the model about ONE tool.
It has 4 parts:

    {
      "type": "function",                  # always "function" for your own tools
      "function": {
        "name": "...",                     # lesson 4
        "description": "...",              # lesson 5
        "parameters": { JSON Schema },     # lessons 6-9
        "strict": True                     # optional: make the model follow the schema exactly
      }
    }

PROJECT: an auto-schema-maker. Write a normal Python function with type hints and a docstring,
and `tool_from_function()` builds the schema for you (this is what many frameworks do inside).
Run:  python 03_tool_schema.py
"""
import inspect
import json
from typing import Literal, get_args, get_origin, get_type_hints

from common import banner, make_executor, run_tool_loop

PY_TO_JSON = {str: "string", int: "integer", float: "number", bool: "boolean", dict: "object"}


def json_type(hint):
    """Python type hint -> JSON Schema piece."""
    if get_origin(hint) is Literal:
        return {"type": "string", "enum": list(get_args(hint))}
    if get_origin(hint) is list:
        inner = get_args(hint)[0] if get_args(hint) else str
        return {"type": "array", "items": json_type(inner)}
    return {"type": PY_TO_JSON.get(hint, "string")}


def parse_args_section(doc):
    """Read lines like '    city: City name' under 'Args:' in a docstring."""
    out = {}
    if "Args:" in doc:
        for line in doc.split("Args:")[1].splitlines():
            if ":" in line:
                name, text = line.strip().split(":", 1)
                out[name.strip()] = text.strip()
    return out


def tool_from_function(fn):
    hints = get_type_hints(fn)
    doc = inspect.getdoc(fn) or ""
    param_docs = parse_args_section(doc)
    properties, required = {}, []
    for name, param in inspect.signature(fn).parameters.items():
        prop = json_type(hints.get(name, str))
        if name in param_docs:
            prop["description"] = param_docs[name]
        properties[name] = prop
        if param.default is inspect.Parameter.empty:      # no default value -> required
            required.append(name)
    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": doc.split("\n\n")[0].strip(),
            "parameters": {"type": "object", "properties": properties,
                           "required": required, "additionalProperties": False},
        },
    }


# ---- our own function: just normal Python! ----
def convert_currency(amount: float, from_currency: str, to_currency: Literal["INR", "USD", "EUR"] = "INR") -> dict:
    """Convert money between currencies using fixed demo rates.

    Args:
        amount: How much money to convert
        from_currency: 3-letter code of the money you have, e.g. USD
        to_currency: 3-letter code you want
    """
    to_inr = {"USD": 83.0, "EUR": 90.0, "INR": 1.0}
    value = amount * to_inr[from_currency.upper()] / to_inr[to_currency]
    return {"amount": amount, "from": from_currency.upper(), "to": to_currency, "converted": round(value, 2)}


def main():
    schema = tool_from_function(convert_currency)
    banner("Generated schema (this is exactly what the model receives)")
    print(json.dumps(schema, indent=2))

    banner("Live test")
    messages = [{"role": "user", "content": "How many euros is 5000 rupees? Use the tool."}]
    answer = run_tool_loop(messages, [schema], make_executor({"convert_currency": convert_currency}))
    print("\nFinal answer:", answer)


if __name__ == "__main__":
    main()
