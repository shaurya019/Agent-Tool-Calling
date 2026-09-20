"""
LESSON 22 - TOOL CANCELLATION
-----------------------------
Cancellation = the user (or your app) says "stop!" while tools are still running.
Important rules:
  1) Python cannot force-stop a thread, so long tools should CHECK a cancel flag now and then (cooperative).
  2) Tools that have not started yet can simply be cancelled (future.cancel()).
  3) The conversation must stay VALID: every tool_call_id still needs a `tool` message.
     So send {"status": "cancelled"} results - do not just drop them.
  4) Tell the model what was cancelled, so it can explain and offer next steps.
  (Related: for streaming replies, close the stream. For asyncio code, handle asyncio.CancelledError.)

PROJECT: report builder. Two long reports are requested; a timer plays the "user" who presses cancel
after 2 seconds. You can also press Ctrl+C yourself.
Run:  python 22_tool_cancellation.py
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from common import MODEL, banner, client

cancel_event = threading.Event()

REPORT_TOOL = {
    "type": "function",
    "function": {
        "name": "build_report",
        "description": "Build a long report. Takes several seconds.",
        "parameters": {
            "type": "object",
            "properties": {"name": {"type": "string", "enum": ["sales", "inventory"]}},
            "required": ["name"],
        },
    },
}


def build_report(name, steps=10):
    for i in range(steps):
        if cancel_event.is_set():                       # check the flag every step
            return {"status": "cancelled", "report": name, "progress": f"{i}/{steps} steps done"}
        time.sleep(0.5)
    return {"status": "done", "report": name}


def run_calls_with_cancel(calls):
    """Run tool calls one by one in a worker thread; returns {call_id: result_string} even if cancelled."""
    pool = ThreadPoolExecutor(max_workers=1)             # 1 worker -> the 2nd report waits in the queue
    futures = {c.id: pool.submit(build_report, **json.loads(c.function.arguments)) for c in calls}
    try:
        for f in futures.values():
            f.result()
    except KeyboardInterrupt:                            # user pressed Ctrl+C
        print("\n  Ctrl+C received -> cancelling")
        cancel_event.set()

    results = {}
    if cancel_event.is_set():
        for f in futures.values():
            f.cancel()                                   # queued jobs are removed; running job stops by itself
    for cid, f in futures.items():
        if f.cancelled():
            results[cid] = json.dumps({"status": "cancelled", "progress": "never started"})
        else:
            results[cid] = json.dumps(f.result())
    pool.shutdown(wait=True)
    return results


def main():
    banner("Ask for two reports, then cancel after 2 seconds")
    messages = [{"role": "user", "content": "Build the sales report and the inventory report."}]
    msg = client.chat.completions.create(model=MODEL, messages=messages, tools=[REPORT_TOOL]).choices[0].message
    if not msg.tool_calls:
        print("Model did not call tools:", msg.content)
        return
    print(f"model requested {len(msg.tool_calls)} report(s)")

    threading.Timer(2.0, cancel_event.set).start()       # simulated user clicking "Cancel"
    results = run_calls_with_cancel(msg.tool_calls)
    cancel_event.clear()

    messages.append(msg)
    for call in msg.tool_calls:                          # EVERY id gets an answer, even if cancelled
        print(f"  id={call.id} -> {results[call.id]}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": results[call.id]})

    final = client.chat.completions.create(model=MODEL, messages=messages, tools=[REPORT_TOOL])
    print("\nAssistant:", final.choices[0].message.content)


if __name__ == "__main__":
    main()
