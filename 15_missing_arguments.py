"""
LESSON 15 - MISSING ARGUMENTS
-----------------------------
Missing argument = a required value the user never gave ("book a table" - which restaurant? what time?).
Two defences, use BOTH:
  1) Prompt rule:  "If required information is missing, ASK the user. Never guess."
  2) Code check:   if the model calls anyway, return a `missing_arguments` error listing what is missing.

PROJECT: a table-booking chatbot that asks follow-up questions until it has everything.
Run:  python 15_missing_arguments.py           (you type the answers)
      python 15_missing_arguments.py --demo    (scripted user, no typing)
"""
import json
import sys
from datetime import date

from common import banner, run_tool_loop

BOOK_TOOL = {
    "type": "function",
    "function": {
        "name": "book_table",
        "description": "Book a restaurant table. Requires restaurant, date, time and party size.",
        "parameters": {
            "type": "object",
            "properties": {
                "restaurant": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "time": {"type": "string", "description": "24h time HH:MM"},
                "party_size": {"type": "integer", "minimum": 1},
            },
            "required": ["restaurant", "date", "time", "party_size"],
        },
    },
}


def book_table(restaurant, date, time, party_size):
    return {"status": "confirmed", "confirmation": "BK-2041", "restaurant": restaurant,
            "date": date, "time": time, "party_size": party_size}


def executor(name, raw_args, call_id):
    args = json.loads(raw_args or "{}")
    required = BOOK_TOOL["function"]["parameters"]["required"]
    missing = [f for f in required if args.get(f) in (None, "")]
    if missing:                                    # defence #2
        return json.dumps({"error": "missing_arguments", "missing": missing,
                           "instruction": "Ask the user for these values. Do NOT guess them."})
    return json.dumps(book_table(**args))


def new_chat():
    today = date.today()
    system = (f"Today is {today.isoformat()} ({today:%A}). You help book restaurant tables. "
              "If any required detail is missing, ask the user a short question. Never guess or invent values.")   # defence #1
    return [{"role": "system", "content": system}]


def turn(messages, text):
    messages.append({"role": "user", "content": text})
    print(f"\nYou: {text}")
    print("Assistant:", run_tool_loop(messages, [BOOK_TOOL], executor, verbose=True))


def main():
    banner("Table-booking assistant that asks for missing details")
    messages = new_chat()
    if "--demo" in sys.argv:
        for line in ["Book me a table tonight.", "Blue Tokai", "8 pm", "4 people"]:
            turn(messages, line)
        return
    print("Type 'quit' to stop. Start with something vague like: Book me a table tonight.")
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in {"quit", "exit"}:
            break
        if text:
            messages.append({"role": "user", "content": text})
            print("Assistant:", run_tool_loop(messages, [BOOK_TOOL], executor))


if __name__ == "__main__":
    main()
