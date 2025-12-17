from __future__ import annotations

from typing import Any, Dict

from temporalio import activity
from trellis_common.business_logic import (
    package_prepared,
    carrier_dispatched,
    order_shipped,
)
from trellis_common import db


@activity.defn(name="PreparePackage")
async def prepare_package_activity(order: Dict[str, Any]) -> str:
    result = await package_prepared(order)
    db.insert_event(order["order_id"], "package_prepared", {"result": result})
    return result


@activity.defn(name="DispatchCarrier")
async def dispatch_carrier_activity(order: Dict[str, Any]) -> str:
    result = await carrier_dispatched(order)
    db.insert_event(order["order_id"], "carrier_dispatched", {"result": result})
    db.update_order_state(order["order_id"], state="shipped")
    return result


