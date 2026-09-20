"""
LESSON 20 - TOOL RETRIES
------------------------
Some failures are temporary (network blip, "please try again"). Retrying helps - if done carefully:

  * Retry ONLY transient errors. Never retry "not found" or "invalid input".
  * Wait between tries, longer each time  (exponential backoff: 0.5s, 1s, 2s ...)
    plus a bit of randomness (jitter) so many clients do not retry at the same instant.
  * Set a maximum number of attempts.
  * Retrying a tool that CHANGES things (payments!) needs an idempotency key, or you may charge twice.
  * The OpenAI API call itself can also fail (rate limit, network). The SDK retries a few times for you
    (OpenAI(max_retries=5)), and you can wrap your own retry as shown below.

PROJECT: a @retry decorator, a flaky weather service, an idempotent payment, and a live run.
Run:  python 20_tool_retries.py
"""
import functools
import random
import time

from openai import APIConnectionError, APITimeoutError, RateLimitError

from common import MODEL, banner, client, make_executor, run_tool_loop
from demo_tools import WEATHER_TOOL, get_weather

class TransientError(Exception):
    """Temporary problem - worth retrying."""
    
# ---- a flaky service: fails twice, then works ----
_calls = {"n": 0}

def retry(times=3, base_delay=0.5, retry_on=(TransientError,)):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_on as exc:
                    if attempt == times:
                        print(f"    attempt {attempt}/{times} failed ({exc}) -> giving up")
                        raise
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.2)
                    print(f"    attempt {attempt}/{times} failed ({exc}) -> waiting {delay:.2f}s")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=3)
def flaky_weather(city, unit="celsius"):
    _calls["n"] += 1
    if _calls["n"] <= 2:
        raise TransientError("503 service unavailable")
    return get_weather(city, unit)

# ---- idempotency: same key = same payment, even if we retry ----
_processed = {}

def charge_card(amount,idempotency_key):
    if idempotency_key in _processed:
        return {**_processed[idempotency_key], "note": "duplicate ignored (idempotent)"}
    _processed[idempotency_key] = {"charged":amount,"payment_id": f"pay_{len(_processed) + 1}"}
    return _processed[idempotency_key]

def call_model_with_retry(messages,tools,attempts=4):
    """Retry the OpenAI call itself on temporary API problems."""
    
    for x in range(1,attempts+1):
        try:
            return client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
            if x == attempts:
                raise
            wait = 2 ** x + random.random()
            print(f"  API problem ({type(exc).__name__}); retrying in {wait:.1f}s")
            time.sleep(wait)

def main():
    banner("1) Retry with backoff on a flaky tool")
    print("  result:", flaky_weather("Delhi"))

    banner("2) Do NOT retry permanent errors")

    @retry(times=3, retry_on=(TransientError,))
    def lookup(city):
        return get_weather(city)          # raises KeyError for unknown city - not transient
    try:
        lookup("Atlantis")
    except KeyError as exc:
        print("  failed immediately (no retries):", exc)

    banner("3) Idempotency: retrying a payment is safe")
    print(" ", charge_card(500, "order-A100-attempt"))
    print(" ", charge_card(500, "order-A100-attempt"))

    banner("4) Live: model asks for weather, the tool is flaky but our retry hides it")
    _calls["n"] = 0
    messages = [{"role": "user", "content": "What's the weather in Paris?"}]
    print("Assistant:", run_tool_loop(messages, [WEATHER_TOOL], make_executor({"get_weather": flaky_weather})))


if __name__ == "__main__":
    main()
