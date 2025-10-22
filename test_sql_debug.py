#!/usr/bin/env python3
"""
Debug SQL warehouse connection with profile-based authentication.

This script investigates the HTTP 400 error and tests different approaches
to SQL authentication with CLI-based profiles.
"""

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.manager import EnvironmentManager
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from databricks.sql import connect


def test_token_extraction():
    """Test different methods of extracting tokens from profile auth."""
    print("=" * 70)
    print("SQL Authentication Debug - Testing Token Extraction Methods")
    print("=" * 70)
    
    try:
        # Load configuration
        print("\n1. Loading configuration...")
        env_manager = EnvironmentManager()
        env_manager.load_configuration()
        env_manager.set_active_to_default()
        
        credentials = env_manager.get_active_credentials()
        
        if 'profile' not in credentials:
            print("   ⚠️  Not using profile-based auth, skipping")
            return False
        
        profile_name = credentials['profile']
        print(f"   ✅ Profile: {profile_name}")
        print(f"   ✅ Host: {credentials['host']}")
        print(f"   ✅ HTTP Path: {credentials['http_path']}")
        
        # Method 1: Using WorkspaceClient to get token
        print("\n2. Method 1: Extract token via WorkspaceClient...")
        try:
            w = WorkspaceClient(profile=profile_name)
            
            # Access the internal auth provider
            if hasattr(w.config, 'authenticate'):
                auth_provider = w.config.authenticate()
                print(f"   ✅ Auth provider type: {type(auth_provider)}")
                
                if callable(auth_provider):
                    auth_headers = auth_provider()
                    print(f"   ✅ Auth headers type: {type(auth_headers)}")
                    print(f"   ✅ Auth headers keys: {auth_headers.keys() if isinstance(auth_headers, dict) else 'N/A'}")
                    
                    if isinstance(auth_headers, dict) and 'Authorization' in auth_headers:
                        token = auth_headers['Authorization'].replace('Bearer ', '')
                        print(f"   ✅ Token extracted (length: {len(token)})")
                        print(f"   ✅ Token prefix: {token[:20]}...")
                        
                        # Try connecting with this token
                        print("\n3. Testing SQL connection with extracted token...")
                        try:
                            conn = connect(
                                server_hostname=credentials['host'],
                                http_path=credentials['http_path'],
                                access_token=token
                            )
                            cursor = conn.cursor()
                            cursor.execute("SELECT 1 AS test")
                            result = cursor.fetchone()
                            
                            if result and result[0] == 1:
                                print("   ✅ SQL connection SUCCESS!")
                                print(f"   ✅ Query result: {result[0]}")
                                conn.close()
                                return True
                            else:
                                print(f"   ❌ Unexpected result: {result}")
                                
                        except Exception as e:
                            print(f"   ❌ SQL connection failed: {e}")
                            logger.error("SQL connection error", exc_info=True)
            
        except Exception as e:
            print(f"   ❌ Method 1 failed: {e}")
            logger.error("Method 1 error", exc_info=True)
        
        # Method 2: Using Config directly
        print("\n4. Method 2: Extract token via Config...")
        try:
            cfg = Config(profile=profile_name)
            print(f"   ✅ Config created for profile: {profile_name}")
            print(f"   ✅ Config host: {cfg.host}")
            print(f"   ✅ Config auth_type: {cfg.auth_type if hasattr(cfg, 'auth_type') else 'N/A'}")
            
            # Try to get credentials
            if hasattr(cfg, 'credentials'):
                creds = cfg.credentials
                print(f"   ✅ Credentials type: {type(creds)}")
            
            auth_provider = cfg.authenticate()
            print(f"   ✅ Auth provider obtained: {type(auth_provider)}")
            
            if callable(auth_provider):
                auth_result = auth_provider()
                print(f"   ✅ Auth result type: {type(auth_result)}")
                
                if isinstance(auth_result, dict):
                    print(f"   ✅ Auth result keys: {list(auth_result.keys())}")
                    if 'Authorization' in auth_result:
                        token2 = auth_result['Authorization'].replace('Bearer ', '')
                        print(f"   ✅ Token extracted (length: {len(token2)})")
                        print(f"   ✅ Same as Method 1: {token == token2 if 'token' in locals() else 'N/A'}")
                        
        except Exception as e:
            print(f"   ❌ Method 2 failed: {e}")
            logger.error("Method 2 error", exc_info=True)
        
        # Method 3: Check if we need OAuth vs PAT
        print("\n5. Checking authentication type...")
        try:
            import configparser
            import os
            
            config_path = os.path.expanduser('~/.databrickscfg')
            config = configparser.ConfigParser()
            config.read(config_path)
            
            if profile_name in config:
                profile_config = config[profile_name]
                print(f"   ✅ Profile config found in ~/.databrickscfg")
                print(f"   ✅ Auth type: {profile_config.get('auth_type', 'token')}")
                print(f"   ✅ Host: {profile_config.get('host', 'N/A')}")
                
                # Check if token is directly in config
                if 'token' in profile_config:
                    print(f"   ✅ Token in config: Yes (length: {len(profile_config['token'])})")
                else:
                    print(f"   ℹ️  Token in config: No (using CLI auth)")
                    
        except Exception as e:
            print(f"   ⚠️  Could not read config: {e}")
        
        # Method 4: Try using databricks-cli token directly
        print("\n6. Method 4: Try databricks CLI token command...")
        try:
            import subprocess
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--profile', profile_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                cli_token = result.stdout.strip()
                print(f"   ✅ CLI token obtained (length: {len(cli_token)})")
                print(f"   ✅ CLI token prefix: {cli_token[:20]}...")
                
                # Try SQL connection with CLI token
                print("\n7. Testing SQL with CLI token...")
                try:
                    conn = connect(
                        server_hostname=credentials['host'],
                        http_path=credentials['http_path'],
                        access_token=cli_token
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1 AS test")
                    result = cursor.fetchone()
                    
                    if result and result[0] == 1:
                        print("   ✅ SQL connection with CLI token SUCCESS! 🎉")
                        print(f"   ✅ Query result: {result[0]}")
                        conn.close()
                        return True
                    
                except Exception as e:
                    print(f"   ❌ SQL with CLI token failed: {e}")
                    logger.error("CLI token SQL error", exc_info=True)
            else:
                print(f"   ❌ CLI token command failed: {result.stderr}")
                
        except FileNotFoundError:
            print("   ⚠️  databricks CLI not found in PATH")
        except Exception as e:
            print(f"   ❌ Method 4 failed: {e}")
            logger.error("Method 4 error", exc_info=True)
        
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.error("Test failed", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_token_extraction()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ SQL authentication working!")
    else:
        print("⚠️  SQL authentication needs more investigation")
    print("=" * 70)
    
    sys.exit(0 if success else 1)

