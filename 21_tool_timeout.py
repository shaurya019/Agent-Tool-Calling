"""
LESSON 21 - TOOL TIMEOUT
------------------------
A slow tool can freeze your whole app. A timeout says: "wait at most N seconds, then give up".
When it fires, send a clear `timeout` result so the model can tell the user honestly.

Two kinds of timeout in Python:
  SOFT  - run in a thread, stop WAITING after N seconds. The work keeps running in the background
          (Python cannot kill threads). Fine for read-only lookups.
  HARD  - run in a separate process and kill it after N seconds. Use for risky or heavy work.

Also remember the model call has its own timeout:  client.with_options(timeout=30).

PROJECT: a slow report tool protected by soft and hard timeouts.
Run:  python 21_tool_timeout.py
"""
import json
import multiprocessing as mp
import queue
import threading
import time

from common import banner, run_tool_loop

REPORT_TOOL = {
    "type": "function",
    "function": {
        "name": "slow_report",
        "description": "Generate a summary report about a topic. Can be slow.",
        "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]},
    },
}


def slow_report(topic):
    time.sleep(6)                        # pretend the report takes 6 seconds
    return {"topic": topic, "report": "All good."}


def timeout_result(seconds):
    return {"error": "timeout", "message": f"The tool did not finish within {seconds} seconds.",
            "hint": "Tell the user it is taking too long and offer to try again later."}


def run_soft_timeout(fn, args, timeout):
    box = {}

    def target():
        try:
            box["value"] = fn(**args)
        except Exception as exc:
            box["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=target, daemon=True)     # daemon: does not block program exit
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return timeout_result(timeout)                        # thread is still running in the background
    return {"error": box["error"]} if "error" in box else box["value"]


def _worker(fn, args, q):
    try:
        q.put(("ok", fn(**args)))
    except Exception as exc:
        q.put(("error", f"{type(exc).__name__}: {exc}"))


def run_hard_timeout(fn, args, timeout):
    q = mp.Queue()
    proc = mp.Process(target=_worker, args=(fn, args, q))
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()                                       # really stop it
        proc.join()
        return timeout_result(timeout)
    try:
        status, payload = q.get(timeout=1)
    except queue.Empty:
        return {"error": "tool_crashed", "message": "The tool process ended without a result."}
    return payload if status == "ok" else {"error": payload}


def hard_executor(name, raw_args, call_id):
    if name != "slow_report":
        return json.dumps({"error": "unknown_tool"})
    return json.dumps(run_hard_timeout(slow_report, json.loads(raw_args), timeout=2))


def main():
    banner("1) SOFT timeout (thread): give up waiting after 2s")
    start = time.time()
    print(run_soft_timeout(slow_report, {"topic": "sales"}, timeout=2), f"| waited {time.time() - start:.1f}s")

    banner("2) HARD timeout (process): give up AND kill the work after 2s")
    start = time.time()
    print(run_hard_timeout(slow_report, {"topic": "sales"}, timeout=2), f"| waited {time.time() - start:.1f}s")

    banner("3) Live: the model gets a timeout result and explains it")
    messages = [{"role": "user", "content": "Generate the sales report for me."}]
    print("Assistant:", run_tool_loop(messages, [REPORT_TOOL], hard_executor))


if __name__ == "__main__":       # this guard is REQUIRED when using multiprocessing
    main()
