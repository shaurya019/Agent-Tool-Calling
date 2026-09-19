"""
LESSON 12 - MULTIPLE TOOL CALLS
-------------------------------
Two different situations:

  A) PARALLEL  - one model reply contains SEVERAL tool_calls ("weather in 3 cities").
                 They are independent, so you can run them at the same time (threads) = faster.
  B) SEQUENTIAL - call #2 needs the result of call #1, so the model must go round the loop twice.

You can turn off parallel calls with  parallel_tool_calls=False.

PROJECT: "City weather board" - time the parallel version vs. sequential, then a dependent chain.
Run:  python 12_multiple_tool_calls.py
"""
import time
from concurrent.futures import ThreadPoolExecutor

from common import MODEL, banner, client, make_executor, run_tool_loop
from demo_tools import ALL_TOOLS, WEATHER_TOOL, calculate, get_weather


def slow_weather(**kwargs):
    time.sleep(1)                      # pretend the weather service takes 1 second
    return get_weather(**kwargs)


EXECUTOR = make_executor({"get_weather": slow_weather})


def run_parallel(calls):
    """Run every tool call at the same time. Returns {call_id: result_string}."""
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = {c.id: pool.submit(EXECUTOR, c.function.name, c.function.arguments, c.id) for c in calls}
        return {cid: fut.result() for cid, fut in futures.items()}


def part_a():
    banner("A) Parallel: 3 independent calls in ONE model reply")
    messages = [{"role": "user", "content": "Give me the weather in Delhi, Mumbai and Tokyo."}]
    msg = client.chat.completions.create(model=MODEL, messages=messages, tools=[WEATHER_TOOL]).choices[0].message
    if not msg.tool_calls:
        print("No tool calls this time.")
        return
    print(f"model asked for {len(msg.tool_calls)} calls in one reply")
    messages.append(msg)
    start = time.time()
    results = run_parallel(msg.tool_calls)
    print(f"ran in {time.time() - start:.1f}s   (one after another would be ~{len(msg.tool_calls)}s)")
    for call in msg.tool_calls:
        messages.append({"role": "tool", "tool_call_id": call.id, "content": results[call.id]})
    final = client.chat.completions.create(model=MODEL, messages=messages, tools=[WEATHER_TOOL])
    print("Assistant:", final.choices[0].message.content)


def part_b():
    banner("B) Sequential: the 2nd call needs the 1st result")
    messages = [{"role": "user", "content":
                 "Get Delhi's temperature in celsius, then use the calculator to convert it to fahrenheit "
                 "(multiply by 9, divide by 5, add 32)."}]
    print("Assistant:", run_tool_loop(messages, ALL_TOOLS, make_executor({"get_weather": get_weather, "calculate": calculate})))


def part_c():
    banner("C) parallel_tool_calls=False  (forces one call per round)")
    messages = [{"role": "user", "content": "Weather in Delhi and Paris?"}]
    print("Assistant:", run_tool_loop(messages, [WEATHER_TOOL], make_executor({"get_weather": get_weather}),
                                      parallel_tool_calls=False))
    print("Notice the extra rounds compared with parallel mode.")


def main():
    part_a()
    part_b()
    part_c()


if __name__ == "__main__":
    main()
