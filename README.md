# Trellis Temporal Order Lifecycle

Overview

This repository scaffolds a microservices layout to implement the Temporal take‑home using Python for API and workers, Postgres for persistence, and Drizzle ORM (Node) for schema management and migrations.

Services

- api (FastAPI): HTTP endpoints to start workflows, send signals, and query status.
- order-worker (Python): Temporal worker for `OrderWorkflow` and related activities.
- shipping-worker (Python): Temporal worker for `ShippingWorkflow` on its own task queue.
- migrations (Node): Drizzle ORM project to manage the Postgres schema.
- postgres: Database for orders/payments/events.
- temporal: Temporal dev server.

Quick Start

1. Start dev (cross-platform via Node):

   npm install
   npm run dev

2. API will be available at:

   http://localhost:8000

3. Temporal gRPC is exposed at `localhost:7233` for local tooling.

Notes

- `npm run dev` will: build and start Postgres/Temporal, install Python deps in .venv, run Drizzle migrations (from migrations/drizzle), then launch API and both workers concurrently using the venv Python.

API Usage

- POST `/orders/{order_id}/start?payment_id=...`
- POST `/orders/{order_id}/signals/cancel`
- POST `/orders/{order_id}/signals/update_address` (JSON body)
- GET `/orders/{order_id}/status`

Testing

- Install dev deps inside worker images or locally and run pytest for basic workflow tests.


Tech Stack Decisions

- Python 3.11 for API and workers (Temporal Python SDK, FastAPI, uvicorn).
- Postgres 16 for durable state.
- Drizzle ORM (Node) for migrations (`drizzle-kit push`) with TypeScript schema.
- Separate task queues: `order-tq` and `shipping-tq`.

Directory Layout

packages/
  common/
    trellis_common/                 # Shared Python module (flaky_call + stubs)
migrations/
  drizzle/                          # Drizzle project (schema + config)
services/
  api/                              # FastAPI app
  order_worker/                     # Temporal order worker
  shipping_worker/                  # Temporal shipping worker

Next Steps

- Implement workflows/activities and wire DB via psycopg.
- Flesh out FastAPI endpoints to invoke/query Temporal.
- Add tests using Temporal Python testing utilities.


