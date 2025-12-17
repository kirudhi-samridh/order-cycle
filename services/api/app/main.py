import os
from datetime import timedelta
import uuid
import structlog
from fastapi import FastAPI, HTTPException
from temporalio import client


logger = structlog.get_logger()
app = FastAPI(title="Trellis Temporal Order Lifecycle API")
_temporal: client.Client | None = None


async def get_temporal() -> client.Client:
    global _temporal
    if _temporal is None:
        target = os.getenv("TEMPORAL_SERVER", "localhost:7233")
        logger.info("temporal.connect", target=target)
        _temporal = await client.Client.connect(target)
    return _temporal


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/orders/{order_id}/start")
async def start_order(order_id: str, payment_id: str | None = None) -> dict:
    c = await get_temporal()
    # Validate/generate UUIDs
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        order_uuid = uuid.uuid4()
    if payment_id is None:
        payment_id = str(uuid.uuid4())
    else:
        try:
            uuid.UUID(payment_id)
        except ValueError:
            payment_id = str(uuid.uuid4())
    handle = await c.start_workflow(
        "OrderWorkflow",
        str(order_uuid),
        payment_id,
        id=f"order-{order_uuid}",
        task_queue="order-tq",
        run_timeout=timedelta(seconds=15),
    )
    logger.info("workflow.started", workflow_id=handle.id, order_id=str(order_uuid))
    return {"order_id": str(order_uuid), "payment_id": payment_id, "workflow_id": handle.id}


@app.post("/orders/{order_id}/signals/cancel")
async def cancel_order(order_id: str) -> dict:
    c = await get_temporal()
    # Accept either raw UUID or previous prefix format
    try:
        order_uuid = str(uuid.UUID(order_id))
    except ValueError:
        order_uuid = order_id
    handle = c.get_workflow_handle(f"order-{order_uuid}")
    await handle.signal("CancelOrder")
    logger.info("workflow.signal.sent", workflow_id=handle.id, signal="CancelOrder")
    return {"order_id": order_id, "signal": "cancel", "sent": True}


@app.post("/orders/{order_id}/signals/update_address")
async def update_address(order_id: str, address: dict) -> dict:
    c = await get_temporal()
    try:
        order_uuid = str(uuid.UUID(order_id))
    except ValueError:
        order_uuid = order_id
    handle = c.get_workflow_handle(f"order-{order_uuid}")
    await handle.signal("UpdateAddress", address)
    logger.info("workflow.signal.sent", workflow_id=handle.id, signal="UpdateAddress")
    return {"order_id": order_id, "signal": "update_address", "address": address, "sent": True}


@app.get("/orders/{order_id}/status")
async def get_status(order_id: str) -> dict:
    c = await get_temporal()
    try:
        try:
            order_uuid = str(uuid.UUID(order_id))
        except ValueError:
            order_uuid = order_id
        handle = c.get_workflow_handle(f"order-{order_uuid}")
        status = await handle.query("status")
        logger.info("workflow.status", workflow_id=handle.id, status=status)
        return {"order_id": order_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


