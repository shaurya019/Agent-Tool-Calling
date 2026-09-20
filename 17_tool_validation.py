"""
LESSON 17 - TOOL VALIDATION
---------------------------
Validation = checking a tool call BEFORE running it. Think of 4 gates:

  Gate 1  Is the JSON readable?                     (parse)
  Gate 2  Does it match the schema?                 (types, required, enum, ranges)
  Gate 3  Does it make BUSINESS sense?              (order exists? amount <= what was paid?)
  Gate 4  Is it ALLOWED?                            (risky action -> ask a human to approve)

The model can pass gate 2 and still ask for something silly or dangerous. Gates 3 and 4 protect you.

PROJECT: a refund tool with all 4 gates.
Run:  python 17_tool_validation.py     (you may be asked to type y/n for a big refund)
"""
import json

from jsonschema import Draft202012Validator

from common import banner, run_tool_loop

REFUND_TOOL = {
    "type": "function",
    "function": {
        "name": "issue_refund",
        "description": "Refund money for an order. Needs order id, amount in INR and a reason.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "pattern": r"^A\d{3}$", "description": "Like 'A100'"},
                "amount": {"type": "number", "exclusiveMinimum": 0, "description": "Refund amount in INR"},
                "reason": {"type": "string", "minLength": 3, "maxLength": 200},
            },
            "required": ["order_id", "amount", "reason"],
            "additionalProperties": False,
        },
    },
}
VALIDATOR = Draft202012Validator(REFUND_TOOL["function"]["parameters"])

ORDERS = {"A100": {"total": 1499, "refunded": 0}, "A200": {"total": 12000, "refunded": 0}}
APPROVAL_LIMIT = 5000        # refunds above this need a human


class ToolRejected(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


def validate(name, raw_args):
    if name != "issue_refund":                                                     # gate 0
        raise ToolRejected("unknown_tool", f"No tool named {name}")
    try:                                                                            # gate 1
        args = json.loads(raw_args)
    except json.JSONDecodeError as exc:
        raise ToolRejected("invalid_json", str(exc))
    problems = [f"{'.'.join(map(str, e.path)) or 'arguments'}: {e.message}" for e in VALIDATOR.iter_errors(args)]
    if problems:                                                                    # gate 2
        raise ToolRejected("invalid_arguments", "; ".join(problems))
    order = ORDERS.get(args["order_id"])                                            # gate 3
    if order is None:
        raise ToolRejected("order_not_found", f"Order {args['order_id']} does not exist")
    remaining = order["total"] - order["refunded"]
    if args["amount"] > remaining:
        raise ToolRejected("amount_too_high", f"Only {remaining} INR can still be refunded on this order")
    return args, order


def approve(args):                                                                  # gate 4
    answer = input(f"\n  !! HUMAN APPROVAL: refund {args['amount']} INR on {args['order_id']}? [y/N] ").strip().lower()
    return answer == "y"


def executor(name, raw_args, call_id):
    try:
        args, order = validate(name, raw_args)
    except ToolRejected as rej:
        return json.dumps({"error": rej.code, "message": rej.message})
    if args["amount"] > APPROVAL_LIMIT and not approve(args):
        return json.dumps({"error": "approval_denied", "message": "A human reviewer declined this refund."})
    order["refunded"] += args["amount"]
    return json.dumps({"status": "refunded", "order_id": args["order_id"], "amount": args["amount"]})


def main():
    banner("Refund bot with 4 validation gates")
    system = {"role": "system", "content": "You are a support agent. Use issue_refund when asked to refund. Be brief."}
    for prompt in [
        "Refund 1499 rupees for order A100, the shoes arrived damaged.",     # passes all gates
        "Refund 5000 for order A100 please.",                                # gate 3: more than remains
        "Refund order Z999 for 200 rupees, wrong colour.",                   # gate 2: pattern / not found
        "Refund 9000 rupees on order A200, customer is unhappy.",            # gate 4: needs human approval
    ]:
        print(f"\nUser: {prompt}")
        print("Assistant:", run_tool_loop([system, {"role": "user", "content": prompt}], [REFUND_TOOL], executor))


if __name__ == "__main__":
    main()
