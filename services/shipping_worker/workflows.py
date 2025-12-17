from __future__ import annotations

from typing import Any, Dict

from temporalio import workflow


@workflow.defn(name="ShippingWorkflow")
class ShippingWorkflow:
    def __init__(self) -> None:
        self.order: Dict[str, Any] | None = None

    @workflow.run
    async def run(self, order: Dict[str, Any]) -> str:
        self.order = order
        result = await workflow.execute_activity(
            "PreparePackage",
            order,
            schedule_to_close_timeout=2,
            start_to_close_timeout=2,
            retry_policy=workflow.RetryPolicy(maximum_attempts=1),
            task_queue="shipping-tq",
        )

        try:
            dispatch = await workflow.execute_activity(
                "DispatchCarrier",
                order,
                schedule_to_close_timeout=2,
                start_to_close_timeout=2,
                retry_policy=workflow.RetryPolicy(maximum_attempts=1),
                task_queue="shipping-tq",
            )
            return dispatch
        except Exception as err:  # Notify parent and re-raise
            info = workflow.info()
            if info.parent_workflow_id:
                parent = workflow.get_external_workflow_handle(info.parent_workflow_id)
                await parent.signal("DispatchFailed", {"reason": str(err)})
            raise


