import requests
import sys
import json
from datetime import datetime

class ShadiroAPITester:
    def __init__(self, base_url="https://eventbridge-38.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")

            return success, response.json() if response.content else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, response = self.run_test(
            "Get Categories",
            "GET", 
            "categories",
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} categories")
            if response:
                print(f"   Sample category: {response[0].get('name', 'N/A')}")
        return success

    def test_vendors_endpoint(self):
        """Test vendors endpoint without filters"""
        success, response = self.run_test(
            "Get All Vendors",
            "GET",
            "vendors", 
            200
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} vendors")
            if response:
                print(f"   Sample vendor: {response[0].get('business_name', 'N/A')}")
        return success

    def test_vendors_with_filters(self):
        """Test vendors endpoint with filters"""
        # Test with city filter
        success1, response1 = self.run_test(
            "Get Vendors by City",
            "GET",
            "vendors",
            200,
            params={"city": "Mumbai"}
        )
        
        # Test with price range filter
        success2, response2 = self.run_test(
            "Get Vendors by Price Range",
            "GET", 
            "vendors",
            200,
            params={"min_price": 10000, "max_price": 50000}
        )
        
        # Test with search filter
        success3, response3 = self.run_test(
            "Get Vendors by Search",
            "GET",
            "vendors", 
            200,
            params={"search": "wedding"}
        )
        
        return success1 and success2 and success3

    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "name": "Test User",
            "email": self.test_user_email,
            "password": "TestPass123!",
            "phone": "+91 9876543210",
            "role": "user"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Registered user: {response.get('user', {}).get('name', 'N/A')}")
            return True
        return False

    def test_user_login(self):
        """Test user login with registered user"""
        login_data = {
            "email": self.test_user_email,
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in user: {response.get('user', {}).get('name', 'N/A')}")
            return True
        return False

    def test_get_current_user(self):
        """Test get current user endpoint"""
        if not self.token:
            print("❌ No token available for authentication test")
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        
        if success:
            print(f"   Current user: {response.get('name', 'N/A')} ({response.get('email', 'N/A')})")
        return success

def main():
    print("🚀 Starting Shadiro API Testing...")
    print("=" * 50)
    
    # Setup
    tester = ShadiroAPITester()
    
    # Test basic endpoints first
    print("\n📋 Testing Basic Endpoints...")
    tester.test_root_endpoint()
    tester.test_categories_endpoint()
    tester.test_vendors_endpoint()
    tester.test_vendors_with_filters()
    
    # Test authentication flow
    print("\n🔐 Testing Authentication Flow...")
    if tester.test_user_registration():
        tester.test_get_current_user()
        
        # Test login with same user
        tester.token = None  # Clear token to test login
        if tester.test_user_login():
            tester.test_get_current_user()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())