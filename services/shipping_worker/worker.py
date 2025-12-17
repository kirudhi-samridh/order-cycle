import asyncio
import os
import structlog
from temporalio import worker, client


logger = structlog.get_logger()


async def main() -> None:
    temporal_target = os.getenv("TEMPORAL_SERVER", "localhost:7233")
    task_queue = os.getenv("SHIPPING_TASK_QUEUE", "shipping-tq")
    c = await client.Client.connect(temporal_target)

    # Register shipping workflows and activities
    async with worker.Worker(
        c,
        task_queue=task_queue,
        workflows=[
            __import__("services.shipping_worker.workflows", fromlist=["ShippingWorkflow"]).ShippingWorkflow,
        ],
        activities=[
            __import__("services.shipping_worker.activities", fromlist=[
                "prepare_package_activity",
                "dispatch_carrier_activity",
            ]).prepare_package_activity,
            __import__("services.shipping_worker.activities", fromlist=[
                "prepare_package_activity",
                "dispatch_carrier_activity",
            ]).dispatch_carrier_activity,
        ],
    ):
        logger.info("shipping-worker.started", task_queue=task_queue, target=temporal_target)
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())


