#!/usr/bin/env python3
"""
Test actual Databricks connections using profile-based authentication.

This script validates that profile-based auth can successfully connect
to Databricks and perform basic operations.
"""

import sys
import logging

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging setup
from config.manager import EnvironmentManager
from databricks.sdk import WorkspaceClient
from databricks.sql import connect
from databricks.sdk.core import Config


def test_profile_connection():
    """Test actual Databricks connection using profile-based auth."""
    print("=" * 70)
    print("Testing Profile-Based Authentication - Live Connection")
    print("=" * 70)
    
    try:
        # Initialize environment manager
        print("\n1. Loading configuration...")
        env_manager = EnvironmentManager()
        env_manager.load_configuration()
        env_manager.set_active_to_default()
        
        active_name = env_manager.get_active_environment_name()
        credentials = env_manager.get_active_credentials()
        
        print(f"   ✅ Active environment: {active_name}")
        
        if 'profile' not in credentials:
            print(f"   ⚠️  Environment uses token-based auth, not profile-based")
            print(f"      Skipping profile connection test")
            return True
        
        profile_name = credentials['profile']
        print(f"   ✅ Using profile: {profile_name}")
        
        # Test 1: WorkspaceClient connection
        print(f"\n2. Testing WorkspaceClient with profile '{profile_name}'...")
        try:
            w = WorkspaceClient(profile=profile_name)
            
            # Try to get current user info (simple API call)
            current_user = w.current_user.me()
            print(f"   ✅ Successfully authenticated!")
            print(f"      User: {current_user.user_name}")
            print(f"      Active: {current_user.active}")
            
        except Exception as e:
            print(f"   ❌ WorkspaceClient connection failed: {e}")
            logger.error(f"WorkspaceClient error: {e}", exc_info=True)
            return False
        
        # Test 2: List clusters (another API call)
        print(f"\n3. Testing Clusters API...")
        try:
            clusters = list(w.clusters.list())
            cluster_count = len(clusters)
            print(f"   ✅ Clusters API working!")
            print(f"      Found {cluster_count} cluster(s)")
            
            if cluster_count > 0:
                print(f"      First cluster: {clusters[0].cluster_name} ({clusters[0].state.value})")
                
        except Exception as e:
            print(f"   ⚠️  Clusters API call failed: {e}")
            # Not critical, continue
        
        # Test 3: SQL Connection with profile
        print(f"\n4. Testing SQL connection with profile '{profile_name}'...")
        try:
            # Use databricks CLI to get the token (same as main.py implementation)
            import json
            import subprocess
            
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--profile', profile_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            # Parse the JSON response and extract access_token
            token_data = json.loads(result.stdout)
            token = token_data['access_token']
            print(f"      Token obtained (expires: {token_data.get('expiry', 'N/A')})")
            
            conn = connect(
                server_hostname=credentials['host'],
                http_path=credentials['http_path'],
                access_token=token
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print(f"   ✅ SQL connection successful!")
                print(f"      Test query executed: SELECT 1 AS test")
                print(f"      Result: {result[0]}")
            else:
                print(f"   ❌ SQL query returned unexpected result: {result}")
                return False
                
            conn.close()
            
        except Exception as e:
            print(f"   ❌ SQL connection failed: {e}")
            logger.error(f"SQL connection error: {e}", exc_info=True)
            return False
        
        # Test 4: Switch environments and test again
        print(f"\n5. Testing environment switching...")
        all_envs = env_manager.list_all_environments()
        
        if len(all_envs) > 1:
            for env_name in all_envs.keys():
                if env_name != active_name:
                    print(f"\n   Switching to: {env_name}")
                    env_manager.switch_to_environment(env_name)
                    
                    new_creds = env_manager.get_active_credentials()
                    if 'profile' in new_creds:
                        try:
                            w2 = WorkspaceClient(profile=new_creds['profile'])
                            user = w2.current_user.me()
                            print(f"   ✅ Connected as: {user.user_name}")
                        except Exception as e:
                            print(f"   ⚠️  Connection to {env_name} failed: {e}")
                    break
        
        # Switch back
        env_manager.set_active_to_default()
        print(f"\n   Switched back to: {env_manager.get_active_environment_name()}")
        
        print("\n" + "=" * 70)
        print("✅ All connection tests passed!")
        print("=" * 70)
        print("\n🎉 Profile-based authentication is working correctly!")
        print("   You can now use the MCP server with CLI authentication.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_profile_connection()
    sys.exit(0 if success else 1)

