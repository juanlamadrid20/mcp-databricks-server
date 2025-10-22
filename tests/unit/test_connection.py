#!/usr/bin/env python3
"""
Unit tests for Databricks connection functionality.

This module tests the connection to Databricks using credentials from the .env file.
It attempts to connect to both the SQL warehouse and the Databricks API.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestDatabricksConnection(unittest.TestCase):
    """Test cases for Databricks connection functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.databricks_host = os.getenv("DATABRICKS_HOST")
        self.databricks_token = os.getenv("DATABRICKS_TOKEN")
        self.databricks_http_path = os.getenv("DATABRICKS_HTTP_PATH")
        
        # Required environment variables
        self.required_vars = [
            "DATABRICKS_HOST",
            "DATABRICKS_TOKEN", 
            "DATABRICKS_HTTP_PATH"
        ]
    
    def tearDown(self):
        """Clean up after each test method."""
        pass
    
    def test_environment_variables_present(self):
        """Test that all required environment variables are set."""
        missing = []
        for var in self.required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        self.assertEqual(
            len(missing), 0,
            f"Missing required environment variables: {missing}. "
            "Please check your .env file and make sure all required variables are set."
        )
    
    @unittest.skipIf(
        not all(os.getenv(var) for var in ["DATABRICKS_HOST", "DATABRICKS_TOKEN"]),
        "Skipping API test - missing required environment variables"
    )
    def test_databricks_api_connection(self):
        """Test connection to Databricks API."""
        try:
            import requests
        except ImportError:
            self.skipTest("requests library not available")
        
        headers = {
            "Authorization": f"Bearer {self.databricks_token}",
            "Content-Type": "application/json"
        }
        
        url = f"https://{self.databricks_host}/api/2.0/clusters/list-node-types"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            self.assertEqual(
                response.status_code, 200,
                f"Failed to connect to Databricks API: {response.status_code} - {response.text}"
            )
        except requests.exceptions.RequestException as e:
            self.fail(f"Error connecting to Databricks API: {str(e)}")
    
    @unittest.skipIf(
        not all(os.getenv(var) for var in ["DATABRICKS_HOST", "DATABRICKS_TOKEN", "DATABRICKS_HTTP_PATH"]),
        "Skipping SQL test - missing required environment variables"
    )
    def test_sql_warehouse_connection(self):
        """Test connection to Databricks SQL warehouse."""
        try:
            from databricks.sql import connect
        except ImportError:
            self.skipTest("databricks-sql-connector library not available")
        
        conn = None
        try:
            conn = connect(
                server_hostname=self.databricks_host,
                http_path=self.databricks_http_path,
                access_token=self.databricks_token
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS test")
            result = cursor.fetchall()
            
            self.assertIsNotNone(result, "Failed to get result from SQL warehouse")
            self.assertEqual(len(result), 1, "Expected exactly one row")
            self.assertEqual(result[0][0], 1, "Expected test value to be 1")
            
        except Exception as e:
            self.fail(f"Error connecting to Databricks SQL warehouse: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def test_credentials_format(self):
        """Test that credentials are in expected format."""
        if self.databricks_host:
            self.assertIsInstance(self.databricks_host, str)
            self.assertGreater(len(self.databricks_host), 0)
        
        if self.databricks_token:
            self.assertIsInstance(self.databricks_token, str)
            self.assertGreater(len(self.databricks_token), 0)
        
        if self.databricks_http_path:
            self.assertIsInstance(self.databricks_http_path, str)
            self.assertGreater(len(self.databricks_http_path), 0)


if __name__ == "__main__":
    # Check for dependencies
    try:
        import requests
        from databricks.sql import connect
    except ImportError as e:
        print(f"❌ Missing dependency: {str(e)}")
        print("Please run: pip install -r requirements.txt")
        exit(1)
    
    # Run the tests
    unittest.main(verbosity=2) 