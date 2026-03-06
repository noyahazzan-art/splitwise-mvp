#!/usr/bin/env python3
"""
Splitwise Vision AI smoke test.
Creates a minimal test image, POSTs to /expenses/upload, verifies response format.
Requires: Splitwise app running (uvicorn), optionally Ollama with llava for real extraction.
Run: python scripts/smoke_test_vision.py
"""
import base64
import io
import sys

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)

# Minimal 1x1 PNG (valid image)
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def main() -> None:
    base = "http://127.0.0.1:8000"  # Default Splitwise port
    if len(sys.argv) > 1:
        base = sys.argv[1].rstrip("/")
    url = f"{base}/expenses/upload"
    print(f"Smoke test: POST {url}")
    print("Sending 1x1 PNG...")
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                url,
                files={"file": ("test.png", io.BytesIO(PNG_1X1), "image/png")},
            )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Response: {data}")
            if "amount" in data or "description" in data or "date" in data:
                print("OK: Vision AI returned expected JSON keys.")
            else:
                print("WARN: Response missing amount/description/date keys.")
        elif r.status_code == 422:
            print(f"Response: {r.json()}")
            print("INFO: Validation error (e.g. Ollama unavailable). Endpoint exists.")
        elif r.status_code == 500:
            print(f"Response: {r.text[:200]}")
            print("INFO: Server error (Ollama/vision may be down). Endpoint exists.")
        else:
            print(f"Body: {r.text[:300]}")
    except httpx.ConnectError as e:
        print(f"ERROR: Cannot connect. Is Splitwise running? {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
