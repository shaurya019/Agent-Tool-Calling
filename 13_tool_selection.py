"""
LESSON 13 - TOOL SELECTION
--------------------------
How does the model choose a tool? From names + descriptions + the conversation.
You can also STEER it with `tool_choice`:

  "auto"                    model decides (default)   - may answer directly or call tools
  "none"                    never call tools
  "required"                must call some tool
  {"type":"function","function":{"name":"X"}}   must call tool X

PROJECT: (a) see all four modes on one question, (b) a tiny "selection test-suite" that scores accuracy.
Use the test-suite every time you change a description - it is how professionals catch regressions.
Run:  python 13_tool_selection.py
"""
from common import banner, peek_tool_calls
from demo_tools import ALL_TOOLS

CHOICES = {
    '"auto"': {"tool_choice": "auto"},
    '"none"': {"tool_choice": "none"},
    '"required"': {"tool_choice": "required"},
    "force get_weather": {"tool_choice": {"type": "function", "function": {"name": "get_weather"}}},
}

SUITE = [
    ("What's 12 * 15?", "calculate"),
    ("Is it raining in London?", "get_weather"),
    ("Where is order A100?", "get_order_status"),
    ("Tell me a fun fact about owls.", None),
    ("If it is 34C in Delhi, what is that in Fahrenheit?", "calculate"),
]


def main():
    question = [{"role": "user", "content": "What's 12 * 15?"}]
    banner("(a) tool_choice modes for the question: 'What's 12 * 15?'")
    for label, kwargs in CHOICES.items():
        msg, calls = peek_tool_calls(question, ALL_TOOLS, **kwargs)
        print(f"  {label:20} -> calls={calls}  text={msg.content!r}")
    print("\nNotice: forcing get_weather makes the model invent a city. Force only when you are sure.")

    banner("(b) Selection test-suite")
    correct = 0
    for prompt, expected in SUITE:
        _, calls = peek_tool_calls([{"role": "user", "content": prompt}], ALL_TOOLS)
        got = calls[0][0] if calls else None
        ok = got == expected
        correct += ok
        print(f"  {'PASS' if ok else 'FAIL'}  {prompt:55} expected={expected}  got={got}")
    print(f"\nAccuracy: {correct}/{len(SUITE)}")


if __name__ == "__main__":
    main()
