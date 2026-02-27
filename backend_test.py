#!/usr/bin/env python3
"""
Backend API Testing for LottieFlow Studio
Tests all API endpoints for the Lottie Animation Maker platform
"""

import requests
import sys
import json
import time
from datetime import datetime

class LottieFlowAPITester:
    def __init__(self, base_url="https://anim-craft-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def log_result(self, test_name, success, message="", error_details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.errors.append(f"{test_name}: {error_details}")
            print(f"❌ {test_name}: {error_details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "LottieFlow Studio API" in data.get("message", ""):
                    self.log_result("API Root", True, f"Status: {response.status_code}, Message: {data['message']}")
                    return True
                else:
                    self.log_result("API Root", False, "", f"Unexpected message: {data}")
                    return False
            else:
                self.log_result("API Root", False, "", f"Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Root", False, "", f"Request failed: {str(e)}")
            return False

    def test_get_templates(self):
        """Test GET /api/templates endpoint"""
        try:
            response = requests.get(f"{self.api_url}/templates", timeout=10)
            if response.status_code == 200:
                templates = response.json()
                if isinstance(templates, list) and len(templates) >= 6:
                    # Verify template structure
                    required_keys = ['id', 'name', 'category', 'description', 'lottie_json']
                    template_names = [t.get('name', '') for t in templates]
                    expected_templates = ['Pulsing Circle', 'Spinning Star', 'Bouncing Ball', 'Loading Dots', 'Success Checkmark', 'Wave Line']
                    
                    if all(key in templates[0] for key in required_keys):
                        self.log_result("Templates", True, f"Found {len(templates)} templates: {', '.join(template_names)}")
                        return True, templates
                    else:
                        self.log_result("Templates", False, "", f"Missing required keys in template structure")
                        return False, []
                else:
                    self.log_result("Templates", False, "", f"Expected list with 6+ templates, got {type(templates)} with {len(templates) if isinstance(templates, list) else 'N/A'} items")
                    return False, []
            else:
                self.log_result("Templates", False, "", f"Expected 200, got {response.status_code}")
                return False, []
        except Exception as e:
            self.log_result("Templates", False, "", f"Request failed: {str(e)}")
            return False, []

    def test_generate_animation(self, test_prompt="a red circle", api_key=None):
        """Test POST /api/generate endpoint"""
        try:
            payload = {
                "prompt": test_prompt,
                "provider": "openai",
                "model": "gpt-5.2"
            }
            if api_key:
                payload["api_key"] = api_key
            
            print(f"🔄 Generating animation (this may take 15-30 seconds)...")
            response = requests.post(f"{self.api_url}/generate", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "lottie_json" in data:
                    lottie_json = data["lottie_json"]
                    # Validate lottie JSON structure
                    if isinstance(lottie_json, dict) and "v" in lottie_json and "layers" in lottie_json:
                        self.log_result("Generate Animation", True, f"Successfully generated animation for: '{test_prompt}'")
                        return True, data
                    else:
                        self.log_result("Generate Animation", False, "", f"Invalid Lottie JSON structure")
                        return False, None
                else:
                    self.log_result("Generate Animation", False, "", f"Response missing success or lottie_json: {data}")
                    return False, None
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.headers.get("content-type", "").startswith("application/json") else f"HTTP {response.status_code}"
                self.log_result("Generate Animation", False, "", f"Expected 200, got {response.status_code}: {error_detail}")
                return False, None
        except Exception as e:
            self.log_result("Generate Animation", False, "", f"Request failed: {str(e)}")
            return False, None

    def test_enhance_animation(self, lottie_json, enhance_prompt="make it green", api_key=None):
        """Test POST /api/enhance endpoint"""
        if not lottie_json:
            self.log_result("Enhance Animation", False, "", "No lottie_json provided for enhancement")
            return False, None
        
        try:
            payload = {
                "lottie_json": lottie_json,
                "prompt": enhance_prompt,
                "provider": "openai", 
                "model": "gpt-5.2"
            }
            if api_key:
                payload["api_key"] = api_key

            print(f"🔄 Enhancing animation (this may take 15-30 seconds)...")
            response = requests.post(f"{self.api_url}/enhance", json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "lottie_json" in data:
                    enhanced_json = data["lottie_json"]
                    if isinstance(enhanced_json, dict) and "v" in enhanced_json and "layers" in enhanced_json:
                        self.log_result("Enhance Animation", True, f"Successfully enhanced animation with: '{enhance_prompt}'")
                        return True, data
                    else:
                        self.log_result("Enhance Animation", False, "", f"Invalid enhanced Lottie JSON structure")
                        return False, None
                else:
                    self.log_result("Enhance Animation", False, "", f"Response missing success or lottie_json: {data}")
                    return False, None
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.headers.get("content-type", "").startswith("application/json") else f"HTTP {response.status_code}"
                self.log_result("Enhance Animation", False, "", f"Expected 200, got {response.status_code}: {error_detail}")
                return False, None
        except Exception as e:
            self.log_result("Enhance Animation", False, "", f"Request failed: {str(e)}")
            return False, None

    def test_save_animation(self, lottie_json, name="Test Animation", prompt="test prompt"):
        """Test POST /api/history endpoint (save animation)"""
        if not lottie_json:
            self.log_result("Save Animation", False, "", "No lottie_json provided for saving")
            return False, None
        
        try:
            payload = {
                "name": name,
                "prompt": prompt,
                "lottie_json": lottie_json
            }
            
            response = requests.post(f"{self.api_url}/history", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and "created_at" in data:
                    self.log_result("Save Animation", True, f"Saved animation with ID: {data['id']}")
                    return True, data
                else:
                    self.log_result("Save Animation", False, "", f"Response missing id or created_at: {data}")
                    return False, None
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.headers.get("content-type", "").startswith("application/json") else f"HTTP {response.status_code}"
                self.log_result("Save Animation", False, "", f"Expected 200, got {response.status_code}: {error_detail}")
                return False, None
        except Exception as e:
            self.log_result("Save Animation", False, "", f"Request failed: {str(e)}")
            return False, None

    def test_get_history(self):
        """Test GET /api/history endpoint"""
        try:
            response = requests.get(f"{self.api_url}/history", timeout=10)
            if response.status_code == 200:
                history = response.json()
                if isinstance(history, list):
                    self.log_result("Get History", True, f"Retrieved {len(history)} saved animations")
                    return True, history
                else:
                    self.log_result("Get History", False, "", f"Expected list, got {type(history)}")
                    return False, []
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.headers.get("content-type", "").startswith("application/json") else f"HTTP {response.status_code}"
                self.log_result("Get History", False, "", f"Expected 200, got {response.status_code}: {error_detail}")
                return False, []
        except Exception as e:
            self.log_result("Get History", False, "", f"Request failed: {str(e)}")
            return False, []

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"\n🚀 Starting LottieFlow API Tests")
        print(f"Backend URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)

        # Test 1: API Root
        api_available = self.test_api_root()
        
        # Test 2: Templates
        templates_success, templates = self.test_get_templates()
        
        # Test 3: History (initial state)
        history_success, initial_history = self.test_get_history()
        
        # Test 4: Generate Animation (requires LLM call)
        generate_success, generated_data = self.test_generate_animation()
        
        lottie_json = None
        if generate_success and generated_data:
            lottie_json = generated_data.get("lottie_json")
            
        # Test 5: Save Animation (if generation succeeded)
        save_success = False
        if lottie_json:
            save_success, saved_data = self.test_save_animation(lottie_json)
            
        # Test 6: Enhanced History (after save)
        if save_success:
            enhanced_history_success, enhanced_history = self.test_get_history()
            if enhanced_history_success and len(enhanced_history) > len(initial_history):
                self.log_result("History Update", True, f"History updated: {len(initial_history)} -> {len(enhanced_history)}")
            
        # Test 7: Enhance Animation (if generation succeeded)
        if lottie_json:
            enhance_success, enhanced_data = self.test_enhance_animation(lottie_json)

        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.errors:
            print(f"\n❌ Failed tests:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.tests_passed, self.tests_run, self.errors

def main():
    tester = LottieFlowAPITester()
    passed, total, errors = tester.run_all_tests()
    
    # Return appropriate exit code
    if passed == total:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())