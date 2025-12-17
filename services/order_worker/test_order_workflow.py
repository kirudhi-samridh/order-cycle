import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio import client, worker

from services.order_worker.workflows import OrderWorkflow
from services.order_worker.activities import (
    receive_order_activity,
    validate_order_activity,
    charge_payment_activity,
)


@pytest.mark.asyncio
async def test_order_workflow_happy_path():
    async with await WorkflowEnvironment.start_time_skipping() as env:
        c = await env.client()
        async with worker.Worker(
            c,
            task_queue="test-order-tq",
            workflows=[OrderWorkflow],
            activities=[receive_order_activity, validate_order_activity, charge_payment_activity],
        ):
            handle = await c.start_workflow(
                OrderWorkflow.run,
                "o-1",
                "p-1",
                id="test-order-o-1",
                task_queue="test-order-tq",
            )
            status = await handle.query("status")
            assert "state" in status

