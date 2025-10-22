#!/usr/bin/env python3
"""
Diagnostic script to identify where authentication is hanging.
"""

import sys
import logging
import time
from threading import Thread, Event

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.manager import EnvironmentManager
from databricks.sdk import WorkspaceClient


def test_with_timeout(func, timeout=5):
    """Run a function with a timeout."""
    result = [None]
    error = [None]
    done = Event()
    
    def wrapper():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
        finally:
            done.set()
    
    thread = Thread(target=wrapper)
    thread.daemon = True
    thread.start()
    
    if done.wait(timeout):
        if error[0]:
            raise error[0]
        return result[0]
    else:
        raise TimeoutError(f"Function timed out after {timeout} seconds")


def main():
    print("=" * 70)
    print("Authentication Hang Diagnostic")
    print("=" * 70)
    
    try:
        # Step 1: Load configuration
        print("\n[1/5] Loading configuration...")
        start = time.time()
        env_manager = EnvironmentManager()
        env_manager.load_configuration()
        env_manager.set_active_to_default()
        print(f"   ✅ Configuration loaded in {time.time() - start:.2f}s")
        
        credentials = env_manager.get_active_credentials()
        profile = credentials.get('profile')
        host = credentials.get('host')
        
        print(f"   Profile: {profile}")
        print(f"   Host: {host}")
        
        # Step 2: Initialize WorkspaceClient
        print("\n[2/5] Initializing WorkspaceClient...")
        start = time.time()
        
        def init_client():
            return WorkspaceClient(profile=profile)
        
        try:
            client = test_with_timeout(init_client, timeout=5)
            print(f"   ✅ WorkspaceClient initialized in {time.time() - start:.2f}s")
        except TimeoutError:
            print(f"   ❌ HUNG: WorkspaceClient initialization timed out after 5s")
            print("   This indicates the SDK is trying to do interactive authentication")
            return
        
        # Step 3: Get auth headers
        print("\n[3/5] Getting authentication headers...")
        start = time.time()
        
        def get_auth():
            return client.config.authenticate()({})
        
        try:
            headers = test_with_timeout(get_auth, timeout=5)
            print(f"   ✅ Auth headers obtained in {time.time() - start:.2f}s")
            
            auth_header = headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                print(f"   Token preview: {token[:20]}...")
            else:
                print(f"   ❌ No valid Bearer token in headers: {headers}")
                return
        except TimeoutError:
            print(f"   ❌ HUNG: Getting auth headers timed out after 5s")
            print("   This indicates authentication is hanging")
            return
        
        # Step 4: Test SQL connection
        print("\n[4/5] Testing SQL connection...")
        start = time.time()
        
        from databricks.sql import connect
        
        def test_sql():
            conn = connect(
                server_hostname=host,
                http_path=credentials['http_path'],
                access_token=token
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()
            conn.close()
            return result
        
        try:
            result = test_with_timeout(test_sql, timeout=10)
            print(f"   ✅ SQL query executed in {time.time() - start:.2f}s")
            print(f"   Result: {result}")
        except TimeoutError:
            print(f"   ❌ HUNG: SQL query timed out after 10s")
            print("   This indicates SQL warehouse connection is hanging")
            return
        
        # Step 5: Test simple API call
        print("\n[5/5] Testing REST API call...")
        start = time.time()
        
        def test_api():
            return client.clusters.list()
        
        try:
            clusters = test_with_timeout(test_api, timeout=10)
            clusters_list = list(clusters)
            print(f"   ✅ API call completed in {time.time() - start:.2f}s")
            print(f"   Found {len(clusters_list)} clusters")
        except TimeoutError:
            print(f"   ❌ HUNG: API call timed out after 10s")
            return
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - No hanging detected!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

