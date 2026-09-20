"""
LESSON 18 - TOOL EXECUTION ERRORS
---------------------------------
The arguments were fine, but the tool still FAILED while running: database down, order not found, a bug.
Golden rules:
  1) Catch every exception. Always send a `tool` message back (otherwise the API complains).
  2) CLASSIFY the error - it tells the model what to do next:
        user_fixable  (not found)        -> ask the user to check the input
        transient     (service down)     -> maybe retry / try again later
        internal      (a bug)            -> apologise, do not try again
  3) Tell the MODEL a safe summary; keep the stack trace and secrets in YOUR logs only.

PROJECT: an order-status tool with three failure modes (ids A100 ok, Z999 missing, A500 outage, A666 crash).
Run:  python 18_tool_execution_errors.py
"""
import json
import logging

from common import banner, run_tool_loop
from demo_tools import ORDER_TOOL, ORDERS

logging.basicConfig(filename="tool_errors.log", level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")


class OrderNotFound(Exception):
    pass


def order_status(order_id):
    order_id = order_id.strip().upper()
    if order_id == "A500":
        raise ConnectionError("db connection refused at 10.0.0.5:5432 (user=admin)")   # secrets we must NOT leak
    if order_id == "A666":
        return 1 / 0                                                                    # a real bug
    if order_id not in ORDERS:
        raise OrderNotFound(order_id)
    return {"order_id": order_id, **ORDERS[order_id]}


def executor(name, raw_args, call_id):
    try:
        args = json.loads(raw_args)
        return json.dumps({"ok": True, "data": order_status(**args)})
    except OrderNotFound as exc:
        return json.dumps({"ok": False, "error": {"type": "user_fixable", "message": f"Order '{exc}' was not found.",
                                                  "hint": "Ask the user to double-check the order id."}})
    except (ConnectionError, TimeoutError):
        logging.exception("transient failure in %s (call %s)", name, call_id)          # full detail -> log only
        return json.dumps({"ok": False, "error": {"type": "transient", "message": "The order service is temporarily unavailable.",
                                                  "hint": "Tell the user to try again in a few minutes."}})
    except Exception:
        logging.exception("BUG in %s (call %s)", name, call_id)
        return json.dumps({"ok": False, "error": {"type": "internal", "message": "The tool crashed unexpectedly.",
                                                  "hint": "Apologise. Do not retry."}})


def main():
    banner("Four situations, four different (good) replies")
    system = {"role": "system", "content": "You are a support agent. Use tools to look up orders. Be brief and kind."}
    for order in ["A100", "Z999", "A500", "A666"]:
        prompt = f"What is the status of order {order}?"
        print(f"\nUser: {prompt}")
        print("Assistant:", run_tool_loop([system, {"role": "user", "content": prompt}], [ORDER_TOOL], executor, verbose=False))
    print("\nFull technical details were written to tool_errors.log (never shown to the model or user).")


if __name__ == "__main__":
    main()
