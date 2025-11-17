#!/usr/bin/env python3
"""
[Tutorial Title]
[Brief description]
"""

import os
import requests

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("Error: API_KEY environment variable is required")
    exit(1)


def api(endpoint: str, method: str = "GET", **kwargs):
    """Helper function for API calls"""
    response = requests.request(
        method=method,
        url=f"https://studio.premai.io{endpoint}",
        headers={"Authorization": f"Bearer {API_KEY}", **kwargs.pop("headers", {})},
        **kwargs
    )
    if not response.ok:
        err = response.json() if response.content else {}
        error_msg = err.get("error", str(err)) if isinstance(err, dict) else str(err)
        raise Exception(f"{response.status_code}: {error_msg}")
    return response.json()


def main():
    print("\n=== [Tutorial Title] ===\n")

    # Step 1: [Description]
    print("1. [Step description]...")
    # TODO: Add implementation
    print("   ✓ Complete\n")

    # Step 2: [Description]
    print("2. [Step description]...")
    # TODO: Add implementation
    print("   ✓ Complete\n")

    print("\n✓ Done!\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"\n✗ Error: {err}")
        exit(1)

