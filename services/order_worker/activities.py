from __future__ import annotations

import asyncio
from typing import Any, Dict

from temporalio import activity
from trellis_common.business_logic import (
    order_received,
    order_validated,
    payment_charged,
)
from trellis_common import db


@activity.defn(name="ReceiveOrder")
async def receive_order_activity(order_id: str) -> Dict[str, Any]:
    result = await order_received(order_id)
    oid = result.get("order_id", order_id)
    db.upsert_order(oid, state="received")
    db.insert_event(oid, "order_received", {"result": result})
    return result


@activity.defn(name="ValidateOrder")
async def validate_order_activity(order: Dict[str, Any]) -> bool:
    ok = await order_validated(order)
    db.update_order_state(order["order_id"], state="validated")
    db.insert_event(order["order_id"], "order_validated", {"ok": ok})
    return ok


@activity.defn(name="ChargePayment")
async def charge_payment_activity(order: Dict[str, Any], payment_id: str) -> Dict[str, Any]:
    # Idempotency via payments.payment_id unique key
    existing = db.get_payment_status(payment_id)
    if existing == "charged":
        amount = sum(i.get("qty", 1) for i in order.get("items", []))
        return {"status": "charged", "amount": amount, "idempotent": True}
    result = await payment_charged(order, payment_id)
    amount = int(result.get("amount", 0))
    db.upsert_payment(payment_id, order_id=order["order_id"], status="charged", amount=amount)
    db.update_order_state(order["order_id"], state="paid")
    db.insert_event(order["order_id"], "payment_charged", {"payment_id": payment_id, "amount": amount})
    return result


