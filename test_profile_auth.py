#!/usr/bin/env python3
"""
Test script for profile-based authentication.

This script tests that the profile-based authentication works correctly
by attempting to load the configuration and initialize connections.
"""

import sys
from config.manager import EnvironmentManager
from utils.logger import logger


def test_profile_auth():
    """Test profile-based authentication configuration."""
    print("=" * 60)
    print("Testing Profile-Based Authentication")
    print("=" * 60)
    
    try:
        # Initialize environment manager
        print("\n1. Loading configuration...")
        env_manager = EnvironmentManager()
        env_manager.load_configuration()
        
        # Set active environment to default
        print("2. Setting active environment to default...")
        env_manager.set_active_to_default()
        
        # Get current environment info
        active_env = env_manager.get_active_environment()
        print(f"\n✅ Active Environment: {active_env.name}")
        print(f"   Host: {active_env.config.host}")
        print(f"   HTTP Path: {active_env.config.http_path}")
        
        # Check authentication method
        credentials = env_manager.get_active_credentials()
        if 'profile' in credentials:
            print(f"   Auth Method: Profile-based (profile: {credentials['profile']})")
            print(f"   Profile Reference: ~/.databrickscfg [{credentials['profile']}]")
        elif 'token' in credentials:
            print(f"   Auth Method: Token-based")
            print(f"   Token: {credentials['token'][:10]}...")
        
        print(f"   Description: {active_env.config.description}")
        print(f"   Tags: {', '.join(active_env.config.tags)}")
        
        # List all environments
        print("\n3. Available environments:")
        config = env_manager.config
        for env_name, env_config in config.environments.items():
            auth_type = "profile" if env_config.profile else "token"
            auth_value = env_config.profile if env_config.profile else f"{env_config.token[:10]}..."
            print(f"   - {env_name}: {auth_type}={auth_value}")
        
        print("\n" + "=" * 60)
        print("✅ Configuration loaded successfully!")
        print("=" * 60)
        
        # Test environment switching
        print("\n4. Testing environment switching...")
        all_envs = list(config.environments.keys())
        if len(all_envs) > 1:
            for env_name in all_envs:
                print(f"\n   Switching to: {env_name}")
                env_manager.switch_environment(env_name)
                active = env_manager.get_active_environment()
                creds = env_manager.get_active_credentials()
                auth_method = "profile" if 'profile' in creds else "token"
                print(f"   ✅ Active: {active.name} ({auth_method})")
            
            # Switch back to default
            env_manager.set_active_to_default()
            print(f"\n   Switched back to default: {env_manager.get_active_environment().name}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_profile_auth()
    sys.exit(0 if success else 1)

