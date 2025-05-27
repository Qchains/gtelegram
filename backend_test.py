
import requests
import json
import time
import sys
from datetime import datetime

class PandoraAPITester:
    def __init__(self, base_url="https://7be87c8e-c47f-4215-b277-ec3ea9f491b9.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            
            result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success
            }
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.status_code != 204:  # If not No Content
                    result["response"] = response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    result["error"] = response.text
            
            self.test_results.append(result)
            return success, response.json() if success and response.status_code != 204 else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": str(e)
            })
            return False, {}

    def test_portal_endpoint(self):
        """Test the main Pandora 5o portal endpoint"""
        return self.run_test(
            "Pandora Portal Endpoint",
            "GET",
            "pandora/runtime/5o",
            200
        )

    def test_status_endpoint(self):
        """Test the Pandora status endpoint"""
        return self.run_test(
            "Pandora Status Endpoint",
            "GET",
            "pandora/status",
            200
        )

    def test_memory_endpoint(self):
        """Test the memory lines retrieval endpoint"""
        return self.run_test(
            "Memory Lines Retrieval",
            "GET",
            "pandora/memory",
            200
        )

    def test_collector_endpoint(self):
        """Test the FloJsonOutputCollector status endpoint"""
        return self.run_test(
            "Collector Status",
            "GET",
            "pandora/collector",
            200
        )

    def test_config_endpoint(self):
        """Test the Pandora configuration endpoint"""
        return self.run_test(
            "Pandora Configuration",
            "GET",
            "pandora/config",
            200
        )

    def test_introspective_query(self, query="test query"):
        """Test the introspective traversal query endpoint"""
        return self.run_test(
            "Introspective Query",
            "POST",
            "pandora/query",
            200,
            data={"query": query, "action": "introspect"}
        )

    def test_promise_chain(self, data={"test": "data", "identity": "Flo-integrated Nexus"}):
        """Test the promise chain execution endpoint"""
        return self.run_test(
            "Promise Chain Execution",
            "POST",
            "pandora/promise",
            200,
            data={"data": data, "chain_type": "promise_then_this"}
        )

    def test_snapshot_commit(self):
        """Test the memory snapshot commit endpoint"""
        return self.run_test(
            "Memory Snapshot Commit",
            "POST",
            "pandora/snapshot",
            200
        )

    def verify_breath_cycle(self):
        """Verify the breath cycle is incrementing"""
        print("\n🔍 Testing Breath Cycle Increment...")
        
        try:
            # Get initial breath cycle count
            response1 = requests.get(f"{self.base_url}/api/pandora/status")
            initial_count = response1.json()["breath_cycle"]
            print(f"Initial breath cycle count: {initial_count}")
            
            # Wait for 3.5 seconds (slightly longer than the 3.0 second breath cycle)
            print("Waiting for breath cycle (3.5 seconds)...")
            time.sleep(3.5)
            
            # Get updated breath cycle count
            response2 = requests.get(f"{self.base_url}/api/pandora/status")
            updated_count = response2.json()["breath_cycle"]
            print(f"Updated breath cycle count: {updated_count}")
            
            # Check if the count has increased
            success = updated_count > initial_count
            
            result = {
                "name": "Breath Cycle Increment",
                "initial_count": initial_count,
                "updated_count": updated_count,
                "success": success
            }
            
            self.tests_run += 1
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Breath cycle incremented from {initial_count} to {updated_count}")
            else:
                print(f"❌ Failed - Breath cycle did not increment (still at {updated_count})")
            
            self.test_results.append(result)
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": "Breath Cycle Increment",
                "success": False,
                "error": str(e)
            })
            return False

    def verify_memory_persistence(self):
        """Verify memory lines are being persisted"""
        print("\n🔍 Testing Memory Persistence...")
        
        try:
            # Get initial memory count
            response1 = requests.get(f"{self.base_url}/api/pandora/memory")
            initial_count = response1.json()["total_memory_lines"]
            print(f"Initial memory lines count: {initial_count}")
            
            # Create a new memory line via introspective query
            query_data = {"query": f"test_query_{datetime.now().strftime('%H%M%S')}", "action": "introspect"}
            requests.post(f"{self.base_url}/api/pandora/query", json=query_data)
            
            # Wait briefly for processing
            time.sleep(1)
            
            # Get updated memory count
            response2 = requests.get(f"{self.base_url}/api/pandora/memory")
            updated_count = response2.json()["total_memory_lines"]
            print(f"Updated memory lines count: {updated_count}")
            
            # Check if the count has increased
            success = updated_count > initial_count
            
            result = {
                "name": "Memory Persistence",
                "initial_count": initial_count,
                "updated_count": updated_count,
                "success": success
            }
            
            self.tests_run += 1
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Memory lines increased from {initial_count} to {updated_count}")
            else:
                print(f"❌ Failed - Memory lines did not increase (still at {updated_count})")
            
            self.test_results.append(result)
            return success
            
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": "Memory Persistence",
                "success": False,
                "error": str(e)
            })
            return False

    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*50)
        print(f"📊 PANDORA 5o API TEST SUMMARY")
        print("="*50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0:.2f}%")
        print("="*50)
        
        # Print detailed results
        for result in self.test_results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status} - {result['name']}")
            
            if not result["success"] and "error" in result:
                print(f"  Error: {result['error']}")
        
        print("="*50)

def main():
    # Get the backend URL from environment or use default
    tester = PandoraAPITester()
    
    # Run basic endpoint tests
    tester.test_portal_endpoint()
    tester.test_status_endpoint()
    tester.test_memory_endpoint()
    tester.test_collector_endpoint()
    tester.test_config_endpoint()
    
    # Test introspective query
    tester.test_introspective_query()
    
    # Test promise chain
    tester.test_promise_chain()
    
    # Test snapshot commit
    tester.test_snapshot_commit()
    
    # Verify breath cycle is incrementing
    tester.verify_breath_cycle()
    
    # Verify memory persistence
    tester.verify_memory_persistence()
    
    # Print summary
    tester.print_summary()
    
    # Return success/failure code
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
