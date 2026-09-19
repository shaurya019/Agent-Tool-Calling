"""
LESSON 6 - PARAMETERS
---------------------
Parameters are the "blanks in the form" the model must fill when it calls your tool.
Each parameter has a TYPE and (very important) a DESCRIPTION.

Common types:   string | integer | number (decimals) | boolean | array (list) | object (nested)
Helpers:        enum (only these values) | minimum/maximum | items (what is inside a list)

PROJECT: "Calendar assistant". One sentence of normal English -> the model fills a rich form
(text, number, list, choice, nested object). Watch how it converts "next Friday 3pm" to ISO format.
Run:  python 06_parameters.py
"""
from datetime import date

from common import banner, make_executor, run_tool_loop

CALENDAR_TOOL = {
    "type": "function",
    "function": {
        "name": "create_calendar_event",
        "description": "Create a calendar event. Use when the user wants to schedule a meeting or reminder.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short event title, e.g. 'Design review'"},
                "start": {"type": "string", "description": "Start time in ISO 8601, e.g. 2026-09-25T15:00:00"},
                "duration_minutes": {"type": "integer", "description": "Length in minutes", "minimum": 5, "maximum": 480},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "First names of people invited"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                "location": {
                    "type": "object",
                    "description": "Where the event happens",
                    "properties": {"room": {"type": "string"}, "building": {"type": "string"}},
                    "required": ["room"],
                },
            },
            "required": ["title", "start"],
        },
    },
}


def create_calendar_event(title, start, duration_minutes=30, attendees=None, priority="normal", location=None):
    event = {"title": title, "start": start, "duration_minutes": duration_minutes,
             "attendees": attendees or [], "priority": priority, "location": location}
    print("  >>> (pretend) saved to calendar:", event)
    return {"status": "created", "event": event}


def main():
    today = date.today()
    banner("Natural language -> filled-in parameters")
    messages = [
        {"role": "system", "content": f"Today is {today.isoformat()} ({today:%A}). Use tools to schedule events."},
        {"role": "user", "content": "Set up a 45 minute design review next Friday at 3pm with Asha and Ravi, "
                                    "high priority, in Room 4 of the Main building."},
    ]
    answer = run_tool_loop(messages, [CALENDAR_TOOL], make_executor({"create_calendar_event": create_calendar_event}))
    print("\nAssistant:", answer)
    print("\nLook at the model's arguments above: title (string), duration (integer), attendees (array),")
    print("priority (enum), location (nested object). That is all 'parameters' are.")


if __name__ == "__main__":
    main()
