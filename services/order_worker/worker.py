import asyncio
import os
import structlog
from temporalio import worker, client


logger = structlog.get_logger()


async def main() -> None:
    temporal_target = os.getenv("TEMPORAL_SERVER", "localhost:7233")
    task_queue = os.getenv("ORDER_TASK_QUEUE", "order-tq")
    c = await client.Client.connect(temporal_target)

    # Register workflows and activities
    async with worker.Worker(
        c,
        task_queue=task_queue,
        workflows=[
            __import__("services.order_worker.workflows", fromlist=["OrderWorkflow"]).OrderWorkflow,
        ],
        activities=[
            __import__("services.order_worker.activities", fromlist=[
                "receive_order_activity",
                "validate_order_activity",
                "charge_payment_activity",
            ]).receive_order_activity,
            __import__("services.order_worker.activities", fromlist=[
                "receive_order_activity",
                "validate_order_activity",
                "charge_payment_activity",
            ]).validate_order_activity,
            __import__("services.order_worker.activities", fromlist=[
                "receive_order_activity",
                "validate_order_activity",
                "charge_payment_activity",
            ]).charge_payment_activity,
        ],
    ):
        logger.info("order-worker.started", task_queue=task_queue, target=temporal_target)
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())


