#!/usr/bin/env python3
"""
Unit tests for profile-based authentication functionality.

This module tests that the profile-based authentication works correctly
by attempting to load the configuration and initialize connections.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.manager import EnvironmentManager
from utils.logger import logger


class TestProfileAuth(unittest.TestCase):
    """Test cases for profile-based authentication functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.env_manager = None
    
    def tearDown(self):
        """Clean up after each test method."""
        if self.env_manager:
            # Reset to default environment if needed
            try:
                self.env_manager.set_active_to_default()
            except:
                pass
    
    def test_environment_manager_initialization(self):
        """Test that EnvironmentManager can be initialized."""
        try:
            self.env_manager = EnvironmentManager()
            self.assertIsNotNone(self.env_manager)
        except Exception as e:
            self.fail(f"Failed to initialize EnvironmentManager: {e}")
    
    def test_configuration_loading(self):
        """Test that configuration can be loaded."""
        self.env_manager = EnvironmentManager()
        
        try:
            self.env_manager.load_configuration()
            self.assertIsNotNone(self.env_manager._configuration)
        except Exception as e:
            self.fail(f"Failed to load configuration: {e}")
    
    def test_set_active_to_default(self):
        """Test setting active environment to default."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        
        try:
            self.env_manager.set_active_to_default()
            active_name = self.env_manager.get_active_environment_name()
            self.assertIsNotNone(active_name)
        except Exception as e:
            self.fail(f"Failed to set active to default: {e}")
    
    def test_get_active_environment_name(self):
        """Test getting the active environment name."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        self.env_manager.set_active_to_default()
        
        try:
            active_name = self.env_manager.get_active_environment_name()
            self.assertIsInstance(active_name, str)
            self.assertGreater(len(active_name), 0)
        except Exception as e:
            self.fail(f"Failed to get active environment name: {e}")
    
    def test_get_active_credentials(self):
        """Test getting active environment credentials."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        self.env_manager.set_active_to_default()
        
        try:
            credentials = self.env_manager.get_active_credentials()
            self.assertIsInstance(credentials, dict)
            
            # Check that credentials contain required keys
            required_keys = ['host', 'http_path']
            for key in required_keys:
                self.assertIn(key, credentials, f"Missing required credential key: {key}")
            
            # Check that credentials contain either 'profile' or 'token'
            auth_keys = ['profile', 'token']
            auth_present = any(key in credentials for key in auth_keys)
            self.assertTrue(auth_present, "Credentials must contain either 'profile' or 'token'")
            
        except Exception as e:
            self.fail(f"Failed to get active credentials: {e}")
    
    def test_list_all_environments(self):
        """Test listing all available environments."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        
        try:
            all_envs = self.env_manager.list_all_environments()
            self.assertIsInstance(all_envs, dict)
            self.assertGreater(len(all_envs), 0, "Should have at least one environment")
            
            # Check that each environment has required attributes
            for env_name, env_config in all_envs.items():
                self.assertIsInstance(env_name, str)
                self.assertIsNotNone(env_config)
                
        except Exception as e:
            self.fail(f"Failed to list all environments: {e}")
    
    def test_environment_switching(self):
        """Test switching between environments."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        
        try:
            all_envs = self.env_manager.list_all_environments()
            
            if len(all_envs) > 1:
                # Test switching to each environment
                for env_name in all_envs.keys():
                    result = self.env_manager.switch_to_environment(env_name)
                    active_name = self.env_manager.get_active_environment_name()
                    self.assertEqual(active_name, env_name, 
                                   f"Failed to switch to environment {env_name}")
                
                # Switch back to default
                self.env_manager.set_active_to_default()
                default_name = self.env_manager.get_active_environment_name()
                self.assertIsNotNone(default_name)
            else:
                self.skipTest("Only one environment available, skipping switching test")
                
        except Exception as e:
            self.fail(f"Failed to switch environments: {e}")
    
    def test_environment_configuration_structure(self):
        """Test that environment configuration has expected structure."""
        self.env_manager = EnvironmentManager()
        self.env_manager.load_configuration()
        
        try:
            all_envs = self.env_manager.list_all_environments()
            
            for env_name, env_config in all_envs.items():
                # Check required attributes
                self.assertIsNotNone(env_config.host)
                self.assertIsNotNone(env_config.http_path)
                self.assertIsNotNone(env_config.description)
                
                # Check that either profile or token is present
                has_profile = hasattr(env_config, 'profile') and env_config.profile
                has_token = hasattr(env_config, 'token') and env_config.token
                self.assertTrue(has_profile or has_token, 
                               f"Environment {env_name} must have either profile or token")
                
        except Exception as e:
            self.fail(f"Failed to validate environment configuration structure: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

