"""
Local + Production Health Check Script.
Run BEFORE and AFTER every deployment.
Usage:
  python scripts/verify_prod_health.py --env local
  python scripts/verify_prod_health.py --env prod
"""
import requests
import sys
import argparse
import json

ENVS = {
    "local": "http://localhost:8000",
    "prod":  "http://52.66.111.65:8000",
}

API_KEY  = "demo-key-123"
USERNAME = "admin"
PASSWORD = "Admin@123"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results = []

def check(label, method, path, headers=None, body=None, expected=200):
    """Run a single check and record the result."""
    url = f"{BASE_URL}{path}"
    try:
        r = requests.request(method, url, headers=headers or {}, json=body, timeout=12)
        ok  = r.status_code == expected
        tag = PASS if ok else FAIL
        print(f"  [{tag}]  {label} ({r.status_code})")
        if not ok:
            print(f"         Response: {r.text[:200]}")
        results.append((label, ok))
        return r
    except Exception as e:
        print(f"  [{FAIL}]  {label} (ERROR: {e})")
        results.append((label, False))
        return None


def main():
    global BASE_URL
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["local", "prod"], default="local")
    args = parser.parse_args()
    BASE_URL = ENVS[args.env]
    print(f"\n{'='*55}")
    print(f"  UAE PINT AE — Production Smoke Test ({args.env.upper()})")
    print(f"  Target: {BASE_URL}")
    print(f"{'='*55}\n")

    # ──────────────────────────────────────────────────────────
    # 1. Public / Health
    # ──────────────────────────────────────────────────────────
    print("1. HEALTH ENDPOINTS")
    check("Liveness  (/health/live)",  "GET", "/health/live")
    check("Readiness (/health/ready)", "GET", "/health/ready")

    # ──────────────────────────────────────────────────────────
    # 2. Login → get Bearer token
    # ──────────────────────────────────────────────────────────
    print("\n2. AUTHENTICATION")
    r_login = check("Login (admin/admin123)", "POST", "/auth/login",
                    body={"username": USERNAME, "password": PASSWORD})
    token = None
    if r_login and r_login.status_code == 200:
        try:
            token = r_login.json()["access_token"]
            print(f"         Token acquired: {token[:30]}…")
        except Exception:
            print(f"         Could not parse token from: {r_login.text[:200]}")

    bearer = {"Authorization": f"Bearer {token}"} if token else {}

    # ──────────────────────────────────────────────────────────
    # 3. Dashboard / UI Endpoints  (must use Bearer)
    # ──────────────────────────────────────────────────────────
    print("\n3. DASHBOARD / ANALYTICS (Bearer Token)")
    check("Analytics Summary",   "GET", "/api/v1/analytics/summary",   bearer)
    check("Analytics Rules",     "GET", "/api/v1/analytics/rules",     bearer)
    check("Validation History",  "GET", "/api/v1/history",              bearer)
    check("Reports",             "GET", "/api/v1/reports",              bearer)
    check("Users List",          "GET", "/auth/users",                  bearer)
    check("Audit Log",           "GET", "/auth/audit-log?limit=5",      bearer)

    # ──────────────────────────────────────────────────────────
    # 4. ERP Integration Endpoints  (must use X-API-Key)
    # ──────────────────────────────────────────────────────────
    print("\n4. ERP INTEGRATION (X-API-Key)")
    erp_h = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    check("Integration Connections",  "GET", "/api/v1/integrations/connections", erp_h)
    check("System Keys List",         "GET", "/api/v1/system/keys",              {})      # Exempt

    # ──────────────────────────────────────────────────────────
    # 5. Security: raw api call without any auth MUST be blocked
    # ──────────────────────────────────────────────────────────
    print("\n5. SECURITY CHECKS (must fail = PASS for us)")
    check("No-auth API call blocked (401)", "GET", "/api/v1/history", expected=401)

    # ──────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print(f"\n{'='*55}")
    print(f"  RESULT: {passed}/{total} checks passed")
    if passed == total:
        print(f"  \033[92mAll checks passed. Safe to deploy.\033[0m")
    else:
        failed = [name for name, ok in results if not ok]
        print(f"  \033[91mFailed checks: {', '.join(failed)}\033[0m")
        print(f"  \033[91mDo NOT deploy until these are resolved.\033[0m")
        sys.exit(1)
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
