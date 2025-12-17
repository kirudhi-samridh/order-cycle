import json
import sys
import time
import uuid
from urllib import request, error


BASE_URL = "http://localhost:8000"


def http(method: str, path: str, body: dict | None = None, timeout: float = 5.0) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = request.Request(url=url, data=data, method=method.upper(), headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            text = resp.read().decode("utf-8")
            return status, (json.loads(text) if text else {})
    except error.HTTPError as e:
        payload = e.read().decode("utf-8")
        try:
            return e.code, json.loads(payload)
        except Exception:
            return e.code, {"error": payload}


def wait_for_status(order_id: str, want: set[str], timeout_sec: float = 20.0) -> dict:
    deadline = time.time() + timeout_sec
    last = {}
    while time.time() < deadline:
        status, payload = http("GET", f"/orders/{order_id}/status")
        if status == 200:
            last = payload
            state = payload.get("status", {}).get("state")
            if state in want:
                return payload
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for states {want}. Last: {last}")


def test_health() -> None:
    status, payload = http("GET", "/health")
    assert status == 200 and payload.get("status") == "ok", payload


def test_happy_path() -> None:
    order_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())
    # start
    status, payload = http("POST", f"/orders/{order_id}/start?payment_id={payment_id}")
    assert status == 200, payload
    # update address (optional)
    http("POST", f"/orders/{order_id}/signals/update_address", {"street": "123 Main", "city": "SF"})
    # wait for completion
    payload = wait_for_status(order_id, {"completed"}, timeout_sec=25.0)
    state = payload.get("status", {}).get("state")
    assert state == "completed", payload


def test_cancel_path() -> None:
    order_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())
    status, payload = http("POST", f"/orders/{order_id}/start?payment_id={payment_id}")
    assert status == 200, payload
    # send cancel immediately
    http("POST", f"/orders/{order_id}/signals/cancel")
    payload = wait_for_status(order_id, {"cancelled"}, timeout_sec=15.0)
    state = payload.get("status", {}).get("state")
    assert state == "cancelled", payload


def main() -> int:
    tests = [
        ("health", test_health),
        ("happy_path", test_happy_path),
        ("cancel_path", test_cancel_path),
    ]
    failures: list[str] = []
    for name, fn in tests:
        try:
            print(f"[e2e] running {name}...")
            fn()
            print(f"[e2e] {name}: OK")
        except Exception as e:
            failures.append(f"{name}: {e}")
            print(f"[e2e] {name}: FAIL - {e}")
    if failures:
        print("\nFailures:\n" + "\n".join(failures))
        return 1
    print("\nAll e2e tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())


