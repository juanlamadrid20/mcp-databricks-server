#!/usr/bin/env python3
"""
Unit tests for SQL warehouse connection debugging with profile-based authentication.

This module investigates different approaches to SQL authentication with CLI-based profiles
and tests various token extraction methods.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging
import configparser

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config.manager import EnvironmentManager


class TestSQLDebug(unittest.TestCase):
    """Test cases for SQL authentication debugging functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.env_manager = None
        self.credentials = None
        self.profile_name = None
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.env_manager:
            try:
                self.env_manager.set_active_to_default()
            except:
                pass
    
    def test_environment_setup(self):
        """Test setting up environment for debugging."""
        try:
            self.env_manager = EnvironmentManager()
            self.env_manager.load_configuration()
            self.env_manager.set_active_to_default()
            
            self.credentials = self.env_manager.get_active_credentials()
            
            self.assertIsNotNone(self.credentials)
            self.assertIsInstance(self.credentials, dict)
            
            if 'profile' in self.credentials:
                self.profile_name = self.credentials['profile']
                self.assertIsNotNone(self.profile_name)
                self.assertIsInstance(self.profile_name, str)
            else:
                self.skipTest("Not using profile-based auth")
                
        except Exception as e:
            self.fail(f"Failed to set up environment: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_workspace_client_token_extraction(self):
        """Test extracting token via WorkspaceClient."""
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError:
            self.skipTest("databricks-sdk library not available")
        
        self.test_environment_setup()
        
        try:
            w = WorkspaceClient(profile=self.profile_name)
            
            # Access the internal auth provider
            if hasattr(w.config, 'authenticate'):
                auth_provider = w.config.authenticate()
                self.assertIsNotNone(auth_provider)
                
                if callable(auth_provider):
                    auth_headers = auth_provider()
                    self.assertIsNotNone(auth_headers)
                    
                    if isinstance(auth_headers, dict) and 'Authorization' in auth_headers:
                        token = auth_headers['Authorization'].replace('Bearer ', '')
                        self.assertIsNotNone(token)
                        self.assertIsInstance(token, str)
                        self.assertGreater(len(token), 0)
                        
                        # Test SQL connection with extracted token
                        self._test_sql_connection_with_token(token)
                    else:
                        self.fail("Auth headers not in expected format")
                else:
                    self.fail("Auth provider is not callable")
            else:
                self.fail("WorkspaceClient config does not have authenticate method")
                
        except Exception as e:
            self.fail(f"WorkspaceClient token extraction failed: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_config_token_extraction(self):
        """Test extracting token via Config directly."""
        try:
            from databricks.sdk.core import Config
        except ImportError:
            self.skipTest("databricks-sdk library not available")
        
        self.test_environment_setup()
        
        try:
            cfg = Config(profile=self.profile_name)
            self.assertIsNotNone(cfg)
            self.assertEqual(cfg.host, self.credentials['host'])
            
            auth_provider = cfg.authenticate()
            self.assertIsNotNone(auth_provider)
            
            if callable(auth_provider):
                auth_result = auth_provider()
                self.assertIsNotNone(auth_result)
                
                if isinstance(auth_result, dict) and 'Authorization' in auth_result:
                    token = auth_result['Authorization'].replace('Bearer ', '')
                    self.assertIsNotNone(token)
                    self.assertIsInstance(token, str)
                    self.assertGreater(len(token), 0)
                else:
                    self.fail("Auth result not in expected format")
            else:
                self.fail("Auth provider is not callable")
                
        except Exception as e:
            self.fail(f"Config token extraction failed: {e}")
    
    def test_databricks_config_file_reading(self):
        """Test reading databricks configuration file."""
        self.test_environment_setup()
        
        try:
            config_path = os.path.expanduser('~/.databrickscfg')
            config = configparser.ConfigParser()
            config.read(config_path)
            
            self.assertIn(self.profile_name, config, 
                         f"Profile {self.profile_name} not found in ~/.databrickscfg")
            
            profile_config = config[self.profile_name]
            self.assertIsNotNone(profile_config)
            
            # Check required fields
            self.assertIn('host', profile_config)
            self.assertEqual(profile_config['host'], self.credentials['host'])
            
            # Check auth type
            auth_type = profile_config.get('auth_type', 'token')
            self.assertIsInstance(auth_type, str)
            
        except FileNotFoundError:
            self.fail("~/.databrickscfg file not found")
        except Exception as e:
            self.fail(f"Failed to read databricks config: {e}")
    
    @unittest.skipIf(
        not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"),
        "Skipping live connection test - missing environment variables"
    )
    def test_cli_token_extraction(self):
        """Test extracting token using databricks CLI."""
        self.test_environment_setup()
        
        try:
            import subprocess
            import json
            
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--profile', self.profile_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                token_data = json.loads(result.stdout)
                self.assertIsInstance(token_data, dict)
                self.assertIn('access_token', token_data)
                
                token = token_data['access_token']
                self.assertIsNotNone(token)
                self.assertIsInstance(token, str)
                self.assertGreater(len(token), 0)
                
                # Test SQL connection with CLI token
                self._test_sql_connection_with_token(token)
            else:
                self.fail(f"CLI token command failed: {result.stderr}")
                
        except FileNotFoundError:
            self.skipTest("databricks CLI not found in PATH")
        except subprocess.TimeoutExpired:
            self.fail("CLI token command timed out")
        except Exception as e:
            self.fail(f"CLI token extraction failed: {e}")
    
    def _test_sql_connection_with_token(self, token):
        """Helper method to test SQL connection with a given token."""
        try:
            from databricks.sql import connect
        except ImportError:
            self.skipTest("databricks-sql-connector library not available")
        
        conn = None
        try:
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
            
        except Exception as e:
            self.fail(f"SQL connection with token failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def test_token_comparison(self):
        """Test comparing tokens from different extraction methods."""
        self.test_environment_setup()
        
        tokens = {}
        
        # Method 1: WorkspaceClient
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient(profile=self.profile_name)
            if hasattr(w.config, 'authenticate'):
                auth_provider = w.config.authenticate()
                if callable(auth_provider):
                    auth_headers = auth_provider()
                    if isinstance(auth_headers, dict) and 'Authorization' in auth_headers:
                        tokens['workspace_client'] = auth_headers['Authorization'].replace('Bearer ', '')
        except Exception:
            pass
        
        # Method 2: Config
        try:
            from databricks.sdk.core import Config
            cfg = Config(profile=self.profile_name)
            auth_provider = cfg.authenticate()
            if callable(auth_provider):
                auth_result = auth_provider()
                if isinstance(auth_result, dict) and 'Authorization' in auth_result:
                    tokens['config'] = auth_result['Authorization'].replace('Bearer ', '')
        except Exception:
            pass
        
        # Method 3: CLI
        try:
            import subprocess
            import json
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--profile', self.profile_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                token_data = json.loads(result.stdout)
                tokens['cli'] = token_data['access_token']
        except Exception:
            pass
        
        # Compare tokens
        if len(tokens) > 1:
            token_values = list(tokens.values())
            # All tokens should be the same
            for i in range(1, len(token_values)):
                self.assertEqual(token_values[0], token_values[i], 
                               f"Tokens from different methods should be identical")
        else:
            self.skipTest("Could not extract tokens from multiple methods for comparison")


if __name__ == "__main__":
    unittest.main(verbosity=2)

