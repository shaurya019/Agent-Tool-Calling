"""
LESSON 5 - TOOL DESCRIPTION
---------------------------
The description is your chance to TELL the model when to use the tool.
A great description answers:  What does it do?  When should I use it?  When should I NOT use it?
What does it return?

PROJECT: a mini "tool-selection test". Same 3 tools, two versions of descriptions (vague vs good).
We run 4 test questions and score how often the model picks the right tool.
Run:  python 05_tool_description.py
"""
from common import banner, peek_tool_calls

VAGUE = {
    "find_product": "Looks things up.",
    "track_order": "Looks things up.",
    "read_return_policy": "Looks things up.",
}
GOOD = {
    "find_product": "Search the store catalog for products to buy (e.g. 'blue running shoes'). "
                    "Use when the customer is browsing or asking what we sell. "
                    "Do NOT use for existing orders or policy questions.",
    "track_order": "Get the shipping status of an EXISTING order using its order id like 'A100'. "
                   "Use for 'where is my package?'. Requires an order id.",
    "read_return_policy": "Look up store policy about returns, refunds and exchanges. "
                          "Use for rules and deadlines (e.g. 'can I return after 30 days?'). Not for a specific order.",
}
PARAM = {"find_product": "query", "track_order": "order_id", "read_return_policy": "topic"}

TESTS = [
    ("Do you have blue running shoes under 3000 rupees?", "find_product"),
    ("Where is my package A100?", "track_order"),
    ("Can I return shoes after 30 days?", "read_return_policy"),
    ("Hello, how are you?", None),          # expected: NO tool
]


def build_tools(descriptions):
    return [{
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": {PARAM[name]: {"type": "string"}}, "required": [PARAM[name]]},
        },
    } for name, desc in descriptions.items()]


def score(label, descriptions):
    tools = build_tools(descriptions)
    correct = 0
    print(f"\n{label}")
    for prompt, expected in TESTS:
        _, calls = peek_tool_calls([{"role": "user", "content": prompt}], tools)
        chosen = calls[0][0] if calls else None
        ok = chosen == expected
        correct += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {prompt[:50]:50} expected={expected}  got={chosen}")
    print(f"  score: {correct}/{len(TESTS)}")


def main():
    banner("Vague descriptions vs good descriptions")
    score("VAGUE descriptions ('Looks things up.')", VAGUE)
    score("GOOD descriptions (what / when / when-not)", GOOD)


if __name__ == "__main__":
    main()
