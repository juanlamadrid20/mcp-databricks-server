#!/usr/bin/env python3
"""
Quick test to verify SQL queries work without hanging.
"""

import sys
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the main module which has our timeout-protected functions
from main import get_databricks_connection

def main():
    print("=" * 70)
    print("Testing SQL Query (with timeout protection)")
    print("=" * 70)
    
    try:
        # Test 1: Get connection (should complete in < 3 seconds)
        print("\n[1/2] Getting SQL connection...")
        start = time.time()
        conn = get_databricks_connection()
        elapsed = time.time() - start
        print(f"   [OK] Connection established in {elapsed:.2f}s")
        
        # Test 2: Run a simple query
        print("\n[2/2] Running test query: SELECT 1 AS test")
        start = time.time()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS test")
        result = cursor.fetchone()
        elapsed = time.time() - start
        
        if result and result[0] == 1:
            print(f"   [OK] Query executed successfully in {elapsed:.2f}s")
            print(f"   [OK] Result: {result[0]}")
        else:
            print(f"   [ERROR] Unexpected result: {result}")
            return 1
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("[SUCCESS] SQL queries work without hanging!")
        print("=" * 70)
        return 0
        
    except TimeoutError as e:
        print(f"\n[TIMEOUT ERROR] {e}")
        print("\nThe authentication is still hanging. This means:")
        print("  1. Your profile might need interactive re-authentication")
        print("  2. Or there's a network/firewall issue")
        print("\nTry running: databricks auth login --profile anfdev")
        return 1
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        logger.exception("Test failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

