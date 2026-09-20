"""
LESSON 19 - TOOL RESULT FORMATTING
----------------------------------
The model reads your result like a person reads a note. Make it easy:
  * keep ONLY fields that matter for the question (less noise, fewer tokens, lower cost)
  * human-readable values: "shipped" not 3, "2026-09-24" not 1790200000
  * include units/currency:  price_inr: 1499
  * consistent key names, no internal ids, no giant nested logs
  * add a short "summary" or "next_step" when helpful

PROJECT: take an ugly database record, format it, and compare the model's answer AND token cost.
Run:  python 19_tool_result_formatting.py
"""
import json
from datetime import datetime, timezone

from common import MODEL, banner, client, fabricate_tool_turn
from demo_tools import ORDER_TOOL

STATUS = {1: "placed", 2: "packed", 3: "shipped", 4: "delivered"}


def ts(iso):
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp())


def build_raw_order():
    """What a real database might give you: cryptic, huge, full of internals."""
    return {
        "_id": "64f1c2ab9e77d0", "__v": 3, "ord_ref_no": "A100", "cust_fk": 88213, "wh_cd": "BLR-07", "stat_cd": 3,
        "created_ts": ts("2026-09-15T08:30:00"), "eta_ts": ts("2026-09-24T00:00:00"),
        "items": [{"sku_id": "SKU-99182", "nm": "Running shoes", "qty": 1, "unit_price_paise": 149900,
                   "tax_paise": 26982, "meta": {"color_cd": "BL", "size_cd": "9", "bin": "R12-C4"}}],
        "audit_log": [{"ts": ts("2026-09-15T08:30:00") + i * 900, "event": f"internal_event_{i}", "by": "sys"} for i in range(25)],
        "internal_flags": {"fraud_score": 0.02, "manual_review": False, "cost_center": "CC-771"},
    }


def format_order(raw):
    """Curated version: only what a customer-support answer needs."""
    return {
        "order_id": raw["ord_ref_no"],
        "status": STATUS[raw["stat_cd"]],
        "items": [{"name": i["nm"], "quantity": i["qty"], "price_inr": i["unit_price_paise"] / 100} for i in raw["items"]],
        "estimated_delivery": datetime.fromtimestamp(raw["eta_ts"], tz=timezone.utc).date().isoformat(),
    }


def ask(result_text):
    history = fabricate_tool_turn(
        "Where is order A100 and when will it arrive?", "get_order_status", '{"order_id": "A100"}', result_text,
        system="You are a support agent. Today is 2026-09-19. Answer briefly.")
    resp = client.chat.completions.create(model=MODEL, messages=history, tools=[ORDER_TOOL])
    return resp.choices[0].message.content, resp.usage.prompt_tokens


def main():
    raw = json.dumps(build_raw_order())
    neat = json.dumps(format_order(build_raw_order()))

    banner("RAW result")
    print(raw[:300], "...")
    answer, tokens = ask(raw)
    print(f"\n{len(raw)} characters | {tokens} prompt tokens\nAssistant: {answer}")

    banner("FORMATTED result")
    print(neat)
    answer, tokens = ask(neat)
    print(f"\n{len(neat)} characters | {tokens} prompt tokens\nAssistant: {answer}")
    print("\nSmaller + clearer = cheaper, faster and less likely to confuse the model.")


if __name__ == "__main__":
    main()
