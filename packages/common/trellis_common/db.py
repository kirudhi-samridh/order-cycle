import json
import os
import uuid
from typing import Any, Optional

import psycopg


def get_connection() -> psycopg.Connection:
    database_url = os.getenv("DATABASE_URL", "postgres://trellis:trellis@localhost:5432/trellis")
    return psycopg.connect(database_url)


def upsert_order(order_id: str, state: str, address_json: Optional[dict] = None) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO orders (id, state, address_json)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET state = EXCLUDED.state, address_json = EXCLUDED.address_json, updated_at = NOW()
            """,
            (order_id, state, json.dumps(address_json) if address_json is not None else None),
        )


def update_order_state(order_id: str, state: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("UPDATE orders SET state=%s, updated_at=NOW() WHERE id=%s", (state, order_id))


def upsert_payment(payment_id: str, order_id: str, status: str, amount: int) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO payments (payment_id, order_id, status, amount)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (payment_id) DO UPDATE SET status = EXCLUDED.status, amount = EXCLUDED.amount
            """,
            (payment_id, order_id, status, amount),
        )


def get_payment_status(payment_id: str) -> Optional[str]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT status FROM payments WHERE payment_id=%s", (payment_id,))
        row = cur.fetchone()
        return row[0] if row else None


def insert_event(order_id: str, event_type: str, payload: Optional[dict] = None) -> None:
    event_id = str(uuid.uuid4())
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (id, order_id, type, payload_json)
            VALUES (%s, %s, %s, %s)
            """,
            (event_id, order_id, event_type, json.dumps(payload) if payload is not None else None),
        )


