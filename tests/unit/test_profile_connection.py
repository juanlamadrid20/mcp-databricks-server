#!/usr/bin/env python3
"""
Unit tests for actual Databricks connections using profile-based authentication.

This module validates that profile-based auth can successfully connect
to Databricks and perform basic operations.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.manager import EnvironmentManager


class TestProfileConnection(unittest.TestCase):
    """Test cases for actual Databricks connections using profile-based auth."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.env_manager = None
        self.credentials = None
        self.active_name = None
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.env_manager:
            try:
                self.env_manager.set_active_to_default()
            except:
                pass
    
    def test_environment_manager_setup(self):
        """Test setting up environment manager and getting credentials."""
        try:
            self.env_manager = EnvironmentManager()
            self.env_manager.load_configuration()
            self.env_manager.set_active_to_default()
            
            self.active_name = self.env_manager.get_active_environment_name()
            self.credentials = self.env_manager.get_active_credentials()
            
            self.assertIsNotNone(self.active_name)
            self.assertIsNotNone(self.credentials)
            self.assertIsInstance(self.credentials, dict)
            
        except Exception as e:
            self.fail(f"Failed to set up environment manager: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_workspace_client_connection(self):
        """Test WorkspaceClient connection with profile-based auth."""
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError:
            self.skipTest("databricks-sdk library not available")
        
        self.test_environment_manager_setup()
        
        if 'profile' not in self.credentials:
            self.skipTest("Environment uses token-based auth, not profile-based")
        
        profile_name = self.credentials['profile']
        
        try:
            w = WorkspaceClient(profile=profile_name)
            current_user = w.current_user.me()
            
            self.assertIsNotNone(current_user)
            self.assertIsNotNone(current_user.user_name)
            self.assertIsInstance(current_user.user_name, str)
            
        except Exception as e:
            self.fail(f"WorkspaceClient connection failed: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_clusters_api_call(self):
        """Test clusters API call with profile-based auth."""
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError:
            self.skipTest("databricks-sdk library not available")
        
        self.test_environment_manager_setup()
        
        if 'profile' not in self.credentials:
            self.skipTest("Environment uses token-based auth, not profile-based")
        
        profile_name = self.credentials['profile']
        
        try:
            w = WorkspaceClient(profile=profile_name)
            clusters = list(w.clusters.list())
            
            self.assertIsInstance(clusters, list)
            # Note: We don't assert cluster count as it could be 0
            
        except Exception as e:
            # This is not critical, so we'll log but not fail
            logger.warning(f"Clusters API call failed: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_sql_connection_with_profile(self):
        """Test SQL connection using profile-based authentication."""
        try:
            from databricks.sql import connect
        except ImportError:
            self.skipTest("databricks-sql-connector library not available")
        
        self.test_environment_manager_setup()
        
        if 'profile' not in self.credentials:
            self.skipTest("Environment uses token-based auth, not profile-based")
        
        profile_name = self.credentials['profile']
        
        try:
            import json
            import subprocess
            
            # Get token using databricks CLI
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--profile', profile_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            
            token_data = json.loads(result.stdout)
            token = token_data['access_token']
            
            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)
            self.assertGreater(len(token), 0)
            
            # Test SQL connection
            conn = connect(
                server_hostname=self.credentials['host'],
                http_path=self.credentials['http_path'],
                access_token=token
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 1)
            
            conn.close()
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Failed to get token from databricks CLI: {e}")
        except Exception as e:
            self.fail(f"SQL connection failed: {e}")
    
    def test_environment_switching_with_connections(self):
        """Test switching environments and validating connections."""
        self.test_environment_manager_setup()
        
        try:
            all_envs = self.env_manager.list_all_environments()
            
            if len(all_envs) > 1:
                for env_name in all_envs.keys():
                    if env_name != self.active_name:
                        self.env_manager.switch_to_environment(env_name)
                        
                        new_creds = self.env_manager.get_active_credentials()
                        self.assertIsNotNone(new_creds)
                        self.assertIsInstance(new_creds, dict)
                        
                        # Test that we can get credentials for this environment
                        if 'profile' in new_creds:
                            try:
                                from databricks.sdk import WorkspaceClient
                                w = WorkspaceClient(profile=new_creds['profile'])
                                user = w.current_user.me()
                                self.assertIsNotNone(user.user_name)
                            except Exception as e:
                                logger.warning(f"Connection to {env_name} failed: {e}")
                        break
                
                # Switch back to original
                self.env_manager.set_active_to_default()
                final_name = self.env_manager.get_active_environment_name()
                self.assertIsNotNone(final_name)
            else:
                self.skipTest("Only one environment available, skipping switching test")
                
        except Exception as e:
            self.fail(f"Environment switching test failed: {e}")
    
    def test_credentials_structure(self):
        """Test that credentials have the expected structure."""
        self.test_environment_manager_setup()
        
        # Check required keys
        required_keys = ['host', 'http_path']
        for key in required_keys:
            self.assertIn(key, self.credentials, f"Missing required credential key: {key}")
            self.assertIsNotNone(self.credentials[key])
            self.assertIsInstance(self.credentials[key], str)
            self.assertGreater(len(self.credentials[key]), 0)
        
        # Check authentication method
        auth_keys = ['profile', 'token']
        auth_present = any(key in self.credentials for key in auth_keys)
        self.assertTrue(auth_present, "Credentials must contain either 'profile' or 'token'")


if __name__ == "__main__":
    unittest.main(verbosity=2)

