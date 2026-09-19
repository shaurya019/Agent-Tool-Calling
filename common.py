import json
import os 
import sys

try:  # load OPENAI_API_KEY from a .env file if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.getenv("OPENAI_API_KEY"):
    sys.exit(
        "OPENAI_API_KEY not found.\n"
        "Copy .env.example to .env and paste your key there (or export it in your terminal)."
    )

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI() 

def banner(text: str) -> None:
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)
    
    
def make_executor(registry: dict):
    """
    Turn {"tool_name": python_function} into an executor.
    An executor has the shape:  executor(name, raw_args_json, call_id) -> str
    (Tool results sent back to the model must be strings.)
    Later lessons write their own smarter executors.
    """
    def execute(name: str, raw_args: str, call_id: str) -> str:
        fn = registry.get(name)
        if fn is None:
            return json.dumps({"error": f"Unknown tool '{name}'"})
        try:
            args = json.loads(raw_args or "{}")
            return json.dumps(fn(**args), default=str)
        except Exception as exc:  # lesson 18 shows a much better way
            return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
    return execute

def run_tool_loop(messages, tools, executor, max_rounds=6, verbose=True, **kwargs):
    """
    The heart of tool calling:
      ask model -> if it wants tools, run them, send results -> ask again -> ... -> final text.
    `messages` is modified in place (so a chat can continue afterwards).
    Extra keyword args (tool_choice=..., parallel_tool_calls=...) go to the API call.
    """
    
    for round_no in range(1,max_rounds+1):
        res = client.chat.completions.create(model=MODEL, messages=messages, tools=tools, **kwargs)
        msg = res.choices[0].message
        messages.append(msg)
        
        if not msg.tool_calls:                    # no tools requested -> this is the final answer
            return msg.content
        
        for call in msg.tool_calls:
            if verbose:
                print(f"  [round {round_no}] model asks: {call.function.name}({call.function.arguments})  id={call.id}")
            result = executor(call.function.name, call.function.arguments, call.id)
            if verbose:
                print(f"  [round {round_no}] result   : {result[:200]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "(stopped: too many tool rounds)"
            