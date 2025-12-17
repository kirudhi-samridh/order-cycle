from __future__ import annotations

from typing import Any, Dict, Optional

from temporalio import workflow

ManualReviewApproved = workflow.SignalChannel[str]
CancelOrderSignal = workflow.SignalChannel[str]


@workflow.defn(name="OrderWorkflow")
class OrderWorkflow:
    def __init__(self) -> None:
        self.state: str = "starting"
        self.order: Dict[str, Any] | None = None
        self.address: Optional[Dict[str, Any]] = None
        self.cancelled: bool = False
        self.approved: bool = False
        self.dispatch_failures: int = 0

    @workflow.signal
    def CancelOrder(self) -> None:
        self.cancelled = True

    @workflow.signal
    def UpdateAddress(self, address: Dict[str, Any]) -> None:
        self.address = address

    @workflow.query
    def status(self) -> Dict[str, Any]:
        return {"state": self.state, "order": self.order, "address": self.address, "cancelled": self.cancelled, "dispatch_failures": self.dispatch_failures}

    @workflow.signal
    def DispatchFailed(self, payload: Dict[str, Any]) -> None:
        self.dispatch_failures += 1

    @workflow.run
    async def run(self, order_id: str, payment_id: str) -> str:
        self.state = "receiving"
        order = await workflow.execute_activity(
            "ReceiveOrder",
            order_id,
            schedule_to_close_timeout=5,
            start_to_close_timeout=5,
            retry_policy=workflow.RetryPolicy(maximum_attempts=3),
            task_queue="order-tq",
        )
        order["order_id"] = order.get("order_id", order_id)
        if self.address:
            order["address"] = self.address
        self.order = order

        self.state = "validating"
        await workflow.execute_activity(
            "ValidateOrder",
            order,
            schedule_to_close_timeout=5,
            start_to_close_timeout=5,
            retry_policy=workflow.RetryPolicy(maximum_attempts=3),
            task_queue="order-tq",
        )

        # Manual review timer and approval window
        self.state = "manual_review"
        timer = workflow.start_timer(2)
        await timer
        if self.cancelled:
            self.state = "cancelled"
            return "cancelled"

        # Assume approval after timer for MVP
        self.state = "charging"
        await workflow.execute_activity(
            "ChargePayment",
            order,
            payment_id,
            schedule_to_close_timeout=3,
            start_to_close_timeout=3,
            retry_policy=workflow.RetryPolicy(maximum_attempts=1),
            task_queue="order-tq",
        )

        # Child workflow for shipping on separate task queue
        self.state = "shipping"
        # Retry shipping child once if it fails via our signal notification
        retries = 0
        while True:
            result = await workflow.execute_child_workflow(
                "ShippingWorkflow",
                order,
                id=f"ship-{order['order_id']}-{retries}",
                task_queue="shipping-tq",
                retry_policy=workflow.RetryPolicy(maximum_attempts=1),
                execution_timeout=5,
            )
            if self.dispatch_failures == 0:
                break
            # reset signal counter and retry once
            self.dispatch_failures = 0
            retries += 1
            if retries > 1:
                break

        self.state = "completed"
        return result


