"""Full operational test - starts real server, tests all endpoints end-to-end."""
import os
import socket
import subprocess
import sys
import time

import httpx

BASE = "http://127.0.0.1:8765"
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
results = []


def check(name: str, cond: bool, detail: str = ""):
    tag = PASS if cond else FAIL
    msg = f"{tag} {name}"
    if detail:
        msg += f"  →  {detail}"
    print(msg)
    results.append((name, cond))


def h(token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def run():
    client = httpx.Client(base_url=BASE, timeout=10)
    # shorthand wrappers using safe_request
    def GET(url, **kw): return safe_request(client, "GET", url, **kw)
    def POST(url, **kw): return safe_request(client, "POST", url, **kw)
    def PUT(url, **kw): return safe_request(client, "PUT", url, **kw)
    def DELETE(url, **kw): return safe_request(client, "DELETE", url, **kw)

    # unique suffix so re-runs don't hit duplicate-email errors
    TS = str(int(time.time()))[-6:]
    alice_email = f"alice{TS}@example.com"
    bob_email   = f"bob{TS}@example.com"

    # ── 1. Health ───────────────────────────────────────────────────────────
    print("\n── Health ──────────────────────────────────────────────────")
    r = GET("/api")
    check("GET /api  →  200", r.status_code == 200, r.text[:60])

    # ── 2. Register users ───────────────────────────────────────────────────
    print("\n── Auth ────────────────────────────────────────────────────")
    r = POST("/auth/register", json={"name": "Alice", "email": alice_email, "password": "password123"})
    check("POST /auth/register Alice  →  201", r.status_code == 201, str(r.json().get("id")))

    r = POST("/auth/register", json={"name": "Bob", "email": bob_email, "password": "password123"})
    check("POST /auth/register Bob    →  201", r.status_code == 201)
    bob_id = r.json().get("id")

    r = POST("/auth/register", json={"name": "Alice", "email": alice_email, "password": "password123"})
    check("POST /auth/register duplicate  →  400", r.status_code == 400)

    r = POST("/auth/register", json={"name": "<script>", "email": "xss@example.com", "password": "password123"})
    check("POST /auth/register XSS name  →  422", r.status_code == 422)

    r = POST("/auth/register", json={"name": "Bad", "email": "bad@example..com", "password": "password123"})
    check("POST /auth/register bad email  →  422", r.status_code == 422)

    # ── 3. Login ─────────────────────────────────────────────────────────────
    r = POST("/auth/login", json={"email": alice_email, "password": "password123"})
    check("POST /auth/login Alice  →  200", r.status_code == 200)
    alice_token = r.json().get("access_token", "")

    r = POST("/auth/login", json={"email": bob_email, "password": "password123"})
    check("POST /auth/login Bob    →  200", r.status_code == 200)
    bob_token = r.json().get("access_token", "")

    r = POST("/auth/login", json={"email": alice_email, "password": "wrong"})
    check("POST /auth/login wrong password  →  401", r.status_code == 401)

    # ── 4. Token refresh ─────────────────────────────────────────────────────
    r = POST("/auth/refresh", headers=h(alice_token))
    check("POST /auth/refresh  →  200", r.status_code == 200)
    new_token = r.json().get("access_token", "")
    check("Refresh token is different", new_token != alice_token)
    alice_token = new_token

    # ── 5. Get /auth/me ──────────────────────────────────────────────────────
    r = GET("/auth/me", headers=h(alice_token))
    check("GET /auth/me  →  200", r.status_code == 200, r.json().get("email"))

    r = GET("/auth/me")
    check("GET /auth/me  no token  →  403", r.status_code in (401, 403))

    # ── 6. Groups ────────────────────────────────────────────────────────────
    print("\n── Groups ──────────────────────────────────────────────────")
    r = POST("/groups/", json={"name": "Trip to Eilat"}, headers=h(alice_token))
    check("POST /groups/  →  201", r.status_code == 201)
    group_id = r.json().get("id")

    r = POST("/groups/", json={"name": "<bad>"}, headers=h(alice_token))
    check("POST /groups/ XSS name  →  422", r.status_code == 422)

    r = GET("/groups/", headers=h(alice_token))
    check("GET /groups/  →  200", r.status_code == 200, f"{len(r.json())} groups")

    r = GET(f"/groups/{group_id}", headers=h(alice_token))
    check(f"GET /groups/{group_id}  →  200", r.status_code == 200)

    r = POST(f"/groups/{group_id}/members", json={"user_id": bob_id}, headers=h(alice_token))
    check("POST /groups/{id}/members  →  200", r.status_code == 200)

    r = POST(f"/groups/{group_id}/members", json={"user_id": bob_id}, headers=h(bob_token))
    check("POST /groups/{id}/members not-owner  →  403", r.status_code == 403)

    # ── 7. Expenses ──────────────────────────────────────────────────────────
    print("\n── Expenses ────────────────────────────────────────────────")
    alice_id = GET("/auth/me", headers=h(alice_token)).json()["id"]

    r = POST("/expenses/", json={
        "group_id": group_id, "payer_id": alice_id,
        "amount": 100.0, "description": "Hotel", "currency": "ILS"
    }, headers=h(alice_token))
    check("POST /expenses/ equal split  →  201", r.status_code == 201)
    exp_id = r.json().get("id")

    r = POST("/expenses/", json={
        "group_id": group_id, "payer_id": bob_id,
        "amount": 60.0, "description": "Dinner", "currency": "ILS",
        "shares": [{"user_id": alice_id, "share_amount": 30.0}, {"user_id": bob_id, "share_amount": 30.0}]
    }, headers=h(bob_token))
    check("POST /expenses/ manual split  →  201", r.status_code == 201)

    r = POST("/expenses/", json={
        "group_id": group_id, "payer_id": alice_id,
        "amount": 50.0, "description": "Taxi", "currency": "ILS",
        "shares": [{"user_id": alice_id, "share_amount": 10.0}]
    }, headers=h(alice_token))
    check("POST /expenses/ bad share sum  →  422", r.status_code == 422)

    r = GET("/expenses/", headers=h(alice_token))
    check("GET /expenses/  →  200", r.status_code == 200, f"{len(r.json())} expenses")

    r = GET(f"/expenses/{exp_id}", headers=h(alice_token))
    check(f"GET /expenses/{exp_id}  →  200", r.status_code == 200)

    r = PUT(f"/expenses/{exp_id}", json={"description": "Hotel room"}, headers=h(alice_token))
    check("PUT /expenses/{id}  →  200", r.status_code == 200)

    # ── 8. Balance ───────────────────────────────────────────────────────────
    print("\n── Balance ─────────────────────────────────────────────────")
    r = GET(f"/balance/groups/{group_id}/balances", headers=h(alice_token))
    check("GET /balance/.../balances  →  200", r.status_code == 200, str(r.json()))

    net_sum = sum(b["balance"] for b in r.json())
    check("Net balance sum ≈ 0", abs(net_sum) < 0.01, f"sum={net_sum:.4f}")

    r = GET(f"/balance/groups/{group_id}/settle", headers=h(alice_token))
    check("GET /balance/.../settle  →  200", r.status_code == 200, str(r.json()))

    # ── 9. Rate limiting ─────────────────────────────────────────────────────
    print("\n── Rate limiting headers ────────────────────────────────────")
    r = GET("/api")
    check("X-RateLimit-Limit header present", "X-RateLimit-Limit" in r.headers)
    check("X-RateLimit-Remaining header present", "X-RateLimit-Remaining" in r.headers)

    # ── 10. Security headers ─────────────────────────────────────────────────
    print("\n── Security headers ─────────────────────────────────────────")
    check("X-Content-Type-Options", "X-Content-Type-Options" in r.headers)
    check("X-Frame-Options", "X-Frame-Options" in r.headers)
    check("Strict-Transport-Security", "Strict-Transport-Security" in r.headers)

    # ── 11. Cleanup ──────────────────────────────────────────────────────────
    print("\n── Cleanup ──────────────────────────────────────────────────")
    r = DELETE(f"/expenses/{exp_id}", headers=h(alice_token))
    check("DELETE /expenses/{id}  →  200", r.status_code == 200)


    # ── Summary ──────────────────────────────────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*55}")
    print(f"  Result: {passed}/{total} checks passed")
    if passed == total:
        print("  \033[92mALL OPERATIONAL CHECKS PASSED ✓\033[0m")
    else:
        failed = [name for name, ok in results if not ok]
        print(f"  \033[91mFailed: {failed}\033[0m")
    print('='*55)
    client.close()
    return passed == total


def kill_port(port: int, max_wait: float = 6.0) -> None:
    """Kill any process listening on port, then wait until the port is actually free."""
    try:
        r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        pids: set[str] = set()
        for line in r.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pids.add(line.split()[-1])
        for pid in pids:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        if pids:
            print(f"  killed PID(s) {pids} holding port {port}")
    except Exception:
        pass
    # wait until socket bind succeeds (port truly free)
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                return  # port is free
        except OSError:
            time.sleep(0.25)
    print(f"Warning: port {port} may still be in use after {max_wait}s")


def safe_request(client: httpx.Client, method: str, url: str, **kwargs) -> httpx.Response:
    """Retry once on WinError 10054 connection reset."""
    for attempt in range(2):
        try:
            return client.request(method, url, **kwargs)
        except (httpx.ReadError, httpx.ConnectError):
            if attempt == 1:
                raise
            time.sleep(0.5)
    raise RuntimeError("unreachable")


if __name__ == "__main__":
    # Kill any leftover server and wait until port is truly free
    print(f"Ensuring port 8765 is free...")
    kill_port(8765)

    # Start our own server
    env = {**os.environ, "SECRET_KEY": "op-test-secret-key-not-for-production-1234567890!"}
    srv = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8765", "--log-level", "error"],
        env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    # Brief pause then check it didn't exit immediately (e.g. port still busy)
    time.sleep(0.5)
    if srv.poll() is not None:
        print(f"Server process exited immediately (code {srv.poll()}) — port conflict or startup error")
        sys.exit(1)

    # Wait for server to respond
    started = False
    for _ in range(40):
        time.sleep(0.5)
        if srv.poll() is not None:
            print(f"Server process died during startup (code {srv.poll()})")
            sys.exit(1)
        try:
            httpx.get(f"{BASE}/api", timeout=1)
            started = True
            break
        except Exception:
            pass
    if not started:
        print("Server failed to become ready in time")
        srv.terminate()
        sys.exit(1)

    try:
        ok = run()
    finally:
        srv.terminate()
        srv.wait(timeout=5)
    sys.exit(0 if ok else 1)
