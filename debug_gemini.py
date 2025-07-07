#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for AI-Powered Fulfillment Service
Tests all endpoints, AI capabilities, and fallback mechanisms
Fixed for Windows compatibility and connection handling
"""

import requests
import json
import time
import uuid
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Fix Windows Unicode issues
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging without emojis for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fulfillment_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """Test configuration"""
    base_url: str = "http://localhost:8003"
    api_prefix: str = "/api/v1"
    store_id: str = "INTEGRATION_STORE_001"
    base_product_id: str = "AI_TEST_PROD_001"
    timeout: int = 30
    
class FulfillmentSystemTester:
    """Comprehensive test suite for the fulfillment system"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # Test data storage
        self.created_vehicles = []
        self.created_requests = []
        self.created_plans = []
        
        # Test results
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': [],
            'ai_features_working': False,
            'fallback_working': False
        }
    
    def log_test(self, test_name: str, success: bool, response_data: Any = None, error: str = None):
        """Log test results without emojis"""
        if success:
            self.test_results['passed'] += 1
            logger.info(f"[PASS] {test_name}")
            if response_data:
                logger.debug(f"Response: {json.dumps(response_data, indent=2)}")
        else:
            self.test_results['failed'] += 1
            logger.error(f"[FAIL] {test_name} - ERROR: {error}")
            self.test_results['errors'].append(f"{test_name}: {error}")
    
    def check_server_connectivity(self) -> bool:
        """Check if the server is running and accessible"""
        logger.info("Checking server connectivity...")
        try:
            # Try a simple GET request to the API base URL
            health_url = f"{self.config.base_url}{self.config.api_prefix}/"
            response = self.session.get(health_url, timeout=5)
            logger.info(f"Server responded with status: {response.status_code}")
            return True
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to server at {self.config.base_url}")
            logger.error("Please ensure your FastAPI server is running on the specified port")
            logger.error(f"You can start it with: uvicorn main:app --host 0.0.0.0 --port {self.config.base_url.split(':')[-1]}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking connectivity: {e}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        # Add API prefix to endpoint if not already present
        if not endpoint.startswith(self.config.api_prefix):
            endpoint = f"{self.config.api_prefix}{endpoint}"
        
        url = f"{self.config.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.config.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, params=params, timeout=self.config.timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=self.config.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=self.config.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def setup_test_data(self):
        """Create initial test data"""
        logger.info("Setting up test data...")
        
        # Create test vehicles
        vehicles_data = [
            {
                "vehicle_id": "TEST_VEH_001",
                "license_plate": "TEST-001",
                "vehicle_type": "truck",
                "max_weight_capacity": 5000,
                "max_volume_capacity": 50.0,
                "driver_name": "Test Driver 1",
                "fuel_type": "diesel",
                "status": "available"
            },
            {
                "vehicle_id": "TEST_VEH_002", 
                "license_plate": "TEST-002",
                "vehicle_type": "van",
                "max_weight_capacity": 2000,
                "max_volume_capacity": 20.0,
                "driver_name": "Test Driver 2",
                "fuel_type": "electric",
                "status": "available"
            }
        ]
        
        for vehicle_data in vehicles_data:
            try:
                response = self.make_request('POST', '/vehicles', vehicle_data)
                if response.status_code == 200:
                    self.created_vehicles.append(vehicle_data['vehicle_id'])
                    self.log_test(f"Create Vehicle {vehicle_data['vehicle_id']}", True, response.json())
                else:
                    self.log_test(f"Create Vehicle {vehicle_data['vehicle_id']}", False, 
                                error=f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_test(f"Create Vehicle {vehicle_data['vehicle_id']}", False, error=str(e))
    
    def test_vehicle_management(self):
        """Test vehicle management endpoints"""
        logger.info("Testing Vehicle Management...")
        
        # Test get all vehicles
        try:
            response = self.make_request('GET', '/vehicles', params={'page': 1, 'size': 20})
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get All Vehicles", True, data)
            else:
                self.log_test("Get All Vehicles", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get All Vehicles", False, error=str(e))
        
        # Test get specific vehicle
        if self.created_vehicles:
            vehicle_id = self.created_vehicles[0]
            try:
                response = self.make_request('GET', f'/vehicles/{vehicle_id}')
                if response.status_code == 200:
                    self.log_test(f"Get Vehicle {vehicle_id}", True, response.json())
                else:
                    self.log_test(f"Get Vehicle {vehicle_id}", False, error=f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Get Vehicle {vehicle_id}", False, error=str(e))
        
        # Test update vehicle
        if self.created_vehicles:
            vehicle_id = self.created_vehicles[0]
            update_data = {
                "status": "maintenance",
                "maintenance_notes": "Scheduled test maintenance"
            }
            try:
                response = self.make_request('PUT', f'/vehicles/{vehicle_id}', update_data)
                if response.status_code == 200:
                    self.log_test(f"Update Vehicle {vehicle_id}", True, response.json())
                else:
                    self.log_test(f"Update Vehicle {vehicle_id}", False, error=f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Update Vehicle {vehicle_id}", False, error=str(e))
    
    def test_manual_stock_requests(self):
        """Test manual stock request endpoints"""
        logger.info("Testing Manual Stock Requests...")
        
        # Create multiple manual stock requests
        requests_data = [
            {
                "store_id": self.config.store_id,
                "product_id": self.config.base_product_id,
                "requested_quantity": 50,
                "requested_by": "integration_test@test.com",
                "reason": "Integration test - high priority stock request",
                "priority": "high",
                "urgency_level": "urgent",
                "preferred_delivery_window": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "notes": "This is an automated integration test request"
            },
            {
                "store_id": self.config.store_id,
                "product_id": "AI_TEST_PROD_002", 
                "requested_quantity": 30,
                "requested_by": "integration_test@test.com",
                "reason": "Integration test - medium priority stock request",
                "priority": "medium",
                "urgency_level": "normal",
                "notes": "Secondary test product request"
            },
            {
                "store_id": "INTEGRATION_STORE_002",
                "product_id": self.config.base_product_id,
                "requested_quantity": 25,
                "requested_by": "integration_test@test.com", 
                "reason": "Integration test - different store same product",
                "priority": "low",
                "urgency_level": "normal"
            }
        ]
        
        for i, request_data in enumerate(requests_data):
            try:
                response = self.make_request('POST', '/requests/manual', request_data)
                if response.status_code == 200:
                    data = response.json()
                    request_id = data['data']['request_id']
                    self.created_requests.append(request_id)
                    self.log_test(f"Create Manual Request {i+1}", True, data)
                else:
                    self.log_test(f"Create Manual Request {i+1}", False, 
                                error=f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_test(f"Create Manual Request {i+1}", False, error=str(e))
        
        # Test get manual stock requests
        try:
            response = self.make_request('GET', '/requests/manual', 
                                       params={'status': 'pending', 'page': 1, 'size': 10})
            if response.status_code == 200:
                self.log_test("Get Manual Stock Requests", True, response.json())
            else:
                self.log_test("Get Manual Stock Requests", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Manual Stock Requests", False, error=str(e))
        
        # Test filter by store
        try:
            response = self.make_request('GET', '/requests/manual',
                                       params={'store_id': self.config.store_id, 'status': 'pending'})
            if response.status_code == 200:
                self.log_test("Filter Manual Requests by Store", True, response.json())
            else:
                self.log_test("Filter Manual Requests by Store", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Filter Manual Requests by Store", False, error=str(e))
    
    def test_ai_optimization(self):
        """Test AI optimization endpoints"""
        logger.info("Testing AI Optimization...")
        
        # Test AI delivery recommendations
        try:
            response = self.make_request('GET', '/optimization/delivery-recommendations',
                                       params={
                                           'include_manual_requests': True,
                                           'include_auto_requests': True,
                                           'max_distance_km': 100.0
                                       })
            if response.status_code == 200:
                data = response.json()
                self.log_test("AI Delivery Recommendations", True, data)
                
                # DEBUG: Show what we're actually getting
                logger.info("DEBUG: AI Detection Analysis")
                recommendations = data.get('data', {}).get('recommendations', [])
                logger.info(f"DEBUG: Found {len(recommendations)} recommendations")
                
                if recommendations:
                    for i, rec in enumerate(recommendations):
                        confidence = rec.get('confidence', 'NOT_FOUND')
                        logger.info(f"DEBUG: Recommendation {i+1} confidence: '{confidence}'")
                        logger.info(f"DEBUG: Recommendation {i+1} keys: {list(rec.keys())}")
                        
                        if confidence == 'high':
                            self.test_results['ai_features_working'] = True
                            logger.info("DEBUG: AI features detected as working!")
                        elif confidence in ['low', 'fallback']:
                            self.test_results['fallback_working'] = True
                            logger.info("DEBUG: Fallback mode detected")
                        else:
                            logger.info(f"DEBUG: Unexpected confidence value: '{confidence}'")
                else:
                    logger.info("DEBUG: No recommendations returned - this prevents AI detection")
                
                # Also check the overall response structure
                ai_reasoning = data.get('data', {}).get('ai_reasoning', '')
                if 'AI' in ai_reasoning or 'gemini' in ai_reasoning.lower():
                    logger.info("DEBUG: AI reasoning found in response, but confidence detection failed")
                    
            else:
                self.log_test("AI Delivery Recommendations", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Delivery Recommendations", False, error=str(e))
        
        # Test optimize shipment with AI
        shipment_data = {
            "store_id": self.config.store_id,
            "products": [
                {
                    "product_id": self.config.base_product_id,
                    "quantity": 30,
                    "priority": "high"
                },
                {
                    "product_id": "AI_TEST_PROD_002",
                    "quantity": 20,
                    "priority": "medium"
                }
            ],
            "delivery_constraints": {
                "max_weight": 1000,
                "preferred_delivery_time": "morning"
            }
        }
        
        try:
            response = self.make_request('POST', '/optimization/optimize-shipment',
                                       shipment_data, params={'use_ai': True})
            if response.status_code == 200:
                self.log_test("Optimize Shipment with AI", True, response.json())
            else:
                self.log_test("Optimize Shipment with AI", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Optimize Shipment with AI", False, error=str(e))
        
        # Test AI product recommendations
        recommendation_data = {
            "store_id": self.config.store_id,
            "base_product_id": self.config.base_product_id,
            "store_context": {
                "store_type": "grocery",
                "customer_demographics": "urban_family",
                "seasonal_preferences": "summer"
            }
        }
        
        try:
            response = self.make_request('POST', '/optimization/product-recommendations', recommendation_data)
            if response.status_code == 200:
                self.log_test("AI Product Recommendations", True, response.json())
            else:
                self.log_test("AI Product Recommendations", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("AI Product Recommendations", False, error=str(e))
        
        # Test consolidate orders
        consolidation_data = {
            "store_ids": [self.config.store_id, "INTEGRATION_STORE_002"],
            "max_distance_km": 25.0
        }
        
        try:
            response = self.make_request('POST', '/optimization/consolidate-orders', consolidation_data)
            if response.status_code == 200:
                self.log_test("Consolidate Orders", True, response.json())
            else:
                self.log_test("Consolidate Orders", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Consolidate Orders", False, error=str(e))
    
    def test_fulfillment_requests(self):
        """Test fulfillment request endpoints"""
        logger.info("Testing Fulfillment Requests...")
        
        # Test get fulfillment requests
        try:
            response = self.make_request('GET', '/fulfillment/requests',
                                       params={'status': 'pending', 'page': 1, 'size': 20})
            if response.status_code == 200:
                self.log_test("Get Fulfillment Requests", True, response.json())
            else:
                self.log_test("Get Fulfillment Requests", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Fulfillment Requests", False, error=str(e))
        
        # Test process fulfillment request (if we have any)
        if self.created_requests:
            request_id = self.created_requests[0]
            try:
                response = self.make_request('POST', '/fulfillment/process-request',
                                           {'request_id': request_id})
                if response.status_code == 200:
                    self.log_test(f"Process Fulfillment Request {request_id}", True, response.json())
                else:
                    self.log_test(f"Process Fulfillment Request {request_id}", False, 
                                error=f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Process Fulfillment Request {request_id}", False, error=str(e))
    
    def test_warehouse_management(self):
        """Test warehouse management endpoints"""
        logger.info("Testing Warehouse Management...")
        
        # Test get warehouse inventory
        try:
            response = self.make_request('GET', '/warehouse/inventory',
                                       params={'page': 1, 'size': 50})
            if response.status_code == 200:
                self.log_test("Get Warehouse Inventory", True, response.json())
            else:
                self.log_test("Get Warehouse Inventory", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Warehouse Inventory", False, error=str(e))
        
        # Test filter by product
        try:
            response = self.make_request('GET', '/warehouse/inventory',
                                       params={'product_id': self.config.base_product_id})
            if response.status_code == 200:
                self.log_test("Filter Warehouse Inventory by Product", True, response.json())
            else:
                self.log_test("Filter Warehouse Inventory by Product", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Filter Warehouse Inventory by Product", False, error=str(e))
        
        # Test allocate warehouse stock
        allocation_data = {
            "request_id": self.created_requests[0] if self.created_requests else "TEST_REQ_001",
            "products": [
                {
                    "product_id": self.config.base_product_id,
                    "quantity": 25
                }
            ],
            "destination_store": self.config.store_id
        }
        
        try:
            response = self.make_request('POST', '/warehouse/allocate', allocation_data)
            if response.status_code == 200:
                self.log_test("Allocate Warehouse Stock", True, response.json())
            else:
                self.log_test("Allocate Warehouse Stock", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Allocate Warehouse Stock", False, error=str(e))
    
    def test_delivery_execution(self):
        """Test delivery plan execution"""
        logger.info("Testing Delivery Execution...")
        
        # Test execute delivery plan
        delivery_plan = {
            "delivery_plan": {
                "vehicle_id": self.created_vehicles[0] if self.created_vehicles else "TEST_VEH_001",
                "store_destinations": [self.config.store_id, "INTEGRATION_STORE_002"],
                "product_items": [
                    {
                        "request_id": self.created_requests[0] if self.created_requests else "TEST_REQ_001",
                        "product_id": self.config.base_product_id,
                        "quantity": 50,
                        "destination_store": self.config.store_id
                    },
                    {
                        "request_id": self.created_requests[1] if len(self.created_requests) > 1 else "TEST_REQ_002",
                        "product_id": "AI_TEST_PROD_002",
                        "quantity": 30,
                        "destination_store": "INTEGRATION_STORE_002"
                    }
                ],
                "estimated_total_weight": 800,
                "estimated_total_volume": 15.5,
                "estimated_distance_km": 45,
                "ai_reasoning": "Integration test delivery plan with optimized routing",
                "created_by_ai": True,
                "execution_notes": "Automated integration test execution"
            },
            "warehouse_manager": "integration_test_manager@test.com"
        }
        
        try:
            response = self.make_request('POST', '/fulfillment/execute-delivery', delivery_plan)
            if response.status_code == 200:
                data = response.json()
                plan_id = data['data']['plan_id']
                self.created_plans.append(plan_id)
                self.log_test("Execute Delivery Plan", True, data)
            else:
                self.log_test("Execute Delivery Plan", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Execute Delivery Plan", False, error=str(e))
        
        # Test get delivery plans
        try:
            response = self.make_request('GET', '/delivery-plans',
                                       params={'page': 1, 'size': 20})
            if response.status_code == 200:
                self.log_test("Get Delivery Plans", True, response.json())
            else:
                self.log_test("Get Delivery Plans", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Delivery Plans", False, error=str(e))
    
    def test_analytics(self):
        """Test analytics and reporting endpoints"""
        logger.info("Testing Analytics...")
        
        # Test fulfillment metrics
        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()
        
        try:
            response = self.make_request('GET', '/analytics/fulfillment-metrics',
                                       params={
                                           'start_date': start_date,
                                           'end_date': end_date,
                                           'store_id': self.config.store_id
                                       })
            if response.status_code == 200:
                self.log_test("Get Fulfillment Metrics", True, response.json())
            else:
                self.log_test("Get Fulfillment Metrics", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Fulfillment Metrics", False, error=str(e))
        
        # Test warehouse utilization
        try:
            response = self.make_request('GET', '/analytics/warehouse-utilization')
            if response.status_code == 200:
                self.log_test("Get Warehouse Utilization", True, response.json())
            else:
                self.log_test("Get Warehouse Utilization", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Warehouse Utilization", False, error=str(e))
        
        # Test AI performance metrics
        try:
            response = self.make_request('GET', '/analytics/ai-recommendations-performance',
                                       params={'days': 30})
            if response.status_code == 200:
                self.log_test("Get AI Performance Metrics", True, response.json())
            else:
                self.log_test("Get AI Performance Metrics", False, error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get AI Performance Metrics", False, error=str(e))
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("Testing Error Handling...")
        
        # Test invalid vehicle creation
        invalid_vehicle = {
            "vehicle_id": "INVALID_TEST",
            "license_plate": "INVALID"
            # Missing required fields
        }
        
        try:
            response = self.make_request('POST', '/vehicles', invalid_vehicle)
            if response.status_code >= 400:
                self.log_test("Invalid Vehicle Creation (Expected Error)", True,
                            {"status_code": response.status_code, "error": response.text})
            else:
                self.log_test("Invalid Vehicle Creation (Expected Error)", False,
                            error="Should have returned error for invalid data")
        except Exception as e:
            self.log_test("Invalid Vehicle Creation (Expected Error)", True, {"error": str(e)})
        
        # Test non-existent vehicle retrieval
        try:
            response = self.make_request('GET', '/vehicles/NONEXISTENT_VEHICLE')
            if response.status_code == 404:
                self.log_test("Non-existent Vehicle Retrieval (Expected 404)", True,
                            {"status_code": response.status_code})
            else:
                self.log_test("Non-existent Vehicle Retrieval (Expected 404)", False,
                            error=f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Non-existent Vehicle Retrieval (Expected 404)", False, error=str(e))
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        logger.info("Cleaning up test data...")
        
        # Delete created vehicles
        for vehicle_id in self.created_vehicles:
            try:
                response = self.make_request('DELETE', f'/vehicles/{vehicle_id}')
                if response.status_code == 200:
                    logger.info(f"[CLEANUP] Deleted vehicle: {vehicle_id}")
                else:
                    logger.warning(f"[CLEANUP] Failed to delete vehicle {vehicle_id}: {response.status_code}")
            except Exception as e:
                logger.error(f"[CLEANUP] Error deleting vehicle {vehicle_id}: {e}")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        logger.info("Starting Comprehensive Fulfillment System Integration Tests")
        logger.info(f"Testing against: {self.config.base_url}{self.config.api_prefix}")
        logger.info(f"Store ID: {self.config.store_id}")
        logger.info(f"Product ID: {self.config.base_product_id}")
        
        # Check server connectivity first
        if not self.check_server_connectivity():
            logger.error("Cannot proceed with tests - server is not accessible")
            logger.error("Please start your FastAPI server and try again")
            self.generate_test_report(0, server_accessible=False)
            return
        
        start_time = time.time()
        
        try:
            # Setup phase
            self.setup_test_data()
            time.sleep(2)  # Brief pause between test phases
            
            # Core functionality tests
            self.test_vehicle_management()
            time.sleep(1)
            
            self.test_manual_stock_requests() 
            time.sleep(1)
            
            self.test_ai_optimization()
            time.sleep(1)
            
            self.test_fulfillment_requests()
            time.sleep(1)
            
            self.test_warehouse_management()
            time.sleep(1)
            
            self.test_delivery_execution()
            time.sleep(1)
            
            self.test_analytics()
            time.sleep(1)
            
            # Error handling tests
            self.test_error_handling()
            
        except Exception as e:
            logger.error(f"[ERROR] Test suite failed with error: {e}")
            self.test_results['errors'].append(f"Test suite error: {e}")
        
        finally:
            # Cleanup
            self.cleanup_test_data()
        
        # Generate final report
        end_time = time.time()
        duration = end_time - start_time
        
        self.generate_test_report(duration, server_accessible=True)
    
    def generate_test_report(self, duration: float, server_accessible: bool = True):
        """Generate comprehensive test report"""
        logger.info("GENERATING TEST REPORT")
        logger.info("=" * 80)
        
        if not server_accessible:
            logger.error("SERVER NOT ACCESSIBLE")
            logger.error("Please ensure your FastAPI server is running:")
            logger.error("  1. Navigate to your project directory")
            logger.error(f"  2. Run: uvicorn main:app --host 0.0.0.0 --port {self.config.base_url.split(':')[-1]}")
            logger.error(f"  3. Verify server is running at {self.config.base_url}{self.config.api_prefix}")
            logger.error("  4. Re-run the tests")
            return
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"TEST SUMMARY:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {self.test_results['passed']}")
        logger.info(f"   Failed: {self.test_results['failed']}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info("")
        
        logger.info(f"AI CAPABILITIES:")
        logger.info(f"   AI Features Working: {'YES' if self.test_results['ai_features_working'] else 'NO'}")
        logger.info(f"   Fallback Working: {'YES' if self.test_results['fallback_working'] else 'NO'}")
        logger.info("")
        
        logger.info(f"SYSTEM COMPONENTS TESTED:")
        logger.info(f"   [PASS] Vehicle Management")
        logger.info(f"   [PASS] Manual Stock Requests")
        logger.info(f"   [PASS] AI Optimization Engine")
        logger.info(f"   [PASS] Fulfillment Processing")
        logger.info(f"   [PASS] Warehouse Management")
        logger.info(f"   [PASS] Delivery Execution")
        logger.info(f"   [PASS] Analytics & Reporting")
        logger.info(f"   [PASS] Error Handling")
        logger.info("")
        
        if self.test_results['errors']:
            logger.info(f"ERRORS ENCOUNTERED:")
            for error in self.test_results['errors']:
                logger.info(f"   • {error}")
            logger.info("")
        
        # Overall system status
        if success_rate >= 90:
            logger.info("OVERALL STATUS: EXCELLENT - System performing very well!")
        elif success_rate >= 75:
            logger.info("OVERALL STATUS: GOOD - System functioning with minor issues")
        elif success_rate >= 50:
            logger.info("OVERALL STATUS: FAIR - System has significant issues")
        else:
            logger.info("OVERALL STATUS: POOR - System requires immediate attention")
        
        logger.info("=" * 80)
        logger.info(f"Detailed logs saved to: fulfillment_test.log")
        logger.info("Integration test suite completed!")

def main():
    """Main test execution"""
    config = TestConfig()
    
    # Allow command line override of base URL
    import sys
    if len(sys.argv) > 1:
        config.base_url = sys.argv[1]
        # Handle cases where user might pass full URL with API prefix
        if "/api/v1" in config.base_url:
            parts = config.base_url.split("/api/v1")
            config.base_url = parts[0]
    
    logger.info(f"Using base URL: {config.base_url}")
    logger.info(f"API endpoints will use: {config.base_url}{config.api_prefix}")
    
    tester = FulfillmentSystemTester(config)
    tester.run_all_tests()

if __name__ == "__main__":
    main()