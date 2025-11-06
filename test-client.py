#!/usr/bin/env python3
"""
Bulut Backend - Interactive Test Client
Fully functional test script to verify all API endpoints
"""

import requests
import json
from typing import Dict, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_ADDRESS = "0x1234567890abcdef1234567890abcdef12345678"

class BulutTestClient:
    """Interactive test client for Bulut API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def print_response(self, title: str, response: requests.Response):
        """Pretty print API response"""
        print(f"\n{'='*70}")
        print(f"📡 {title}")
        print(f"{'='*70}")
        print(f"Status: {response.status_code}")
        print(f"\nResponse:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
        print(f"{'='*70}\n")
    
    def test_health(self):
        """Test health check endpoint"""
        response = self.session.get(f"{self.base_url}/health")
        self.print_response("Health Check", response)
        return response.status_code == 200
    
    def test_root(self):
        """Test root endpoint"""
        response = self.session.get(f"{self.base_url}/")
        self.print_response("Root Endpoint", response)
        return response.status_code == 200
    
    def test_register_alias(self, alias: str, address: str):
        """Test alias registration"""
        data = {
            "alias": alias,
            "address": address,
            "signature": "0x" + "a"*64
        }
        response = self.session.post(
            f"{self.base_url}/alias/register",
            json=data
        )
        self.print_response(f"Register Alias: {alias}", response)
        return response.status_code == 201
    
    def test_get_alias(self, alias: str):
        """Test alias resolution"""
        response = self.session.get(f"{self.base_url}/alias/{alias}")
        self.print_response(f"Get Alias: {alias}", response)
        return response.status_code == 200
    
    def test_get_address_alias(self, address: str):
        """Test reverse alias lookup"""
        response = self.session.get(f"{self.base_url}/address/{address}/alias")
        self.print_response(f"Get Address Alias: {address[:10]}...", response)
        return response.status_code == 200
    
    def test_process_command(self, command: str):
        """Test payment command processing"""
        data = {
            "text": command,
            "user_id": "test_user",
            "timezone": "UTC"
        }
        response = self.session.post(
            f"{self.base_url}/process_command",
            json=data
        )
        self.print_response(f"Process Command: '{command}'", response)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    
    def test_execute_payment(self, payment_intent: Dict, user_address: str):
        """Test payment execution"""
        data = {
            "intent_id": f"test_{datetime.now().timestamp()}",
            "payment_intent": payment_intent,
            "user_signature": "0x" + "b"*64,
            "user_address": user_address
        }
        
        headers = {
            "X-Wallet-Address": user_address,
            "X-Signature": "0x" + "b"*64
        }
        
        response = self.session.post(
            f"{self.base_url}/execute_payment",
            json=data,
            headers=headers
        )
        self.print_response("Execute Payment", response)
        return response.status_code == 200
    
    def test_get_history(self, address: str):
        """Test transaction history"""
        response = self.session.get(f"{self.base_url}/history/{address}")
        self.print_response(f"Transaction History: {address[:10]}...", response)
        return response.status_code == 200
    
    def test_get_subscriptions(self, address: str):
        """Test subscriptions"""
        response = self.session.get(f"{self.base_url}/subscriptions/{address}")
        self.print_response(f"Subscriptions: {address[:10]}...", response)
        return response.status_code == 200
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("\n" + "="*70)
        print("🧪 BULUT BACKEND - COMPREHENSIVE TEST SUITE")
        print("="*70 + "\n")
        
        results = []
        
        # Test 1: Health Check
        print("TEST 1: Health Check")
        results.append(("Health Check", self.test_health()))
        
        # Test 2: Root Endpoint
        print("\nTEST 2: Root Endpoint")
        results.append(("Root Endpoint", self.test_root()))
        
        # Test 3: Get Demo Alias
        print("\nTEST 3: Get Demo Alias (@alice)")
        results.append(("Get Demo Alias", self.test_get_alias("@alice")))
        
        # Test 4: Get Address Alias (reverse lookup)
        print("\nTEST 4: Reverse Alias Lookup")
        results.append(("Reverse Lookup", self.test_get_address_alias(
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        )))
        
        # Test 5: Register New Alias
        print("\nTEST 5: Register New Alias (@testuser)")
        test_alias = "@testuser"
        test_address = DEMO_ADDRESS
        results.append(("Register Alias", self.test_register_alias(test_alias, test_address)))
        
        # Test 6: Get Newly Registered Alias
        print("\nTEST 6: Get Newly Registered Alias")
        results.append(("Get New Alias", self.test_get_alias(test_alias)))
        
        # Test 7: Process Single Payment Command
        print("\nTEST 7: Process Single Payment Command")
        success, intent = self.test_process_command("Send $50 to @alice for lunch")
        results.append(("Single Payment Command", success))
        
        # Test 8: Execute Single Payment
        if success and intent:
            print("\nTEST 8: Execute Single Payment")
            results.append(("Execute Payment", self.test_execute_payment(intent, test_address)))
        
        # Test 9: Process Split Payment
        print("\nTEST 9: Process Split Payment Command")
        success, intent = self.test_process_command("Split $120 between @alice and @bob")
        results.append(("Split Payment Command", success))
        
        # Test 10: Process Subscription
        print("\nTEST 10: Process Subscription Command")
        success, intent = self.test_process_command("Pay @alice $9.99 every month")
        results.append(("Subscription Command", success))
        
        # Test 11: Get Transaction History
        print("\nTEST 11: Get Transaction History")
        results.append(("Transaction History", self.test_get_history(test_address)))
        
        # Test 12: Get Subscriptions
        print("\nTEST 12: Get Active Subscriptions")
        results.append(("Get Subscriptions", self.test_get_subscriptions(test_address)))
        
        # Print Summary
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:10} | {test_name}")
        
        print("="*70)
        print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
        print("="*70 + "\n")
        
        return passed == total

def interactive_mode():
    """Interactive testing mode"""
    client = BulutTestClient()
    
    print("\n" + "="*70)
    print("🌥️  BULUT BACKEND - INTERACTIVE TEST CLIENT")
    print("="*70)
    print("\nCommands:")
    print("  1 - Run all tests")
    print("  2 - Test specific endpoint")
    print("  3 - Process custom payment command")
    print("  4 - Get alias")
    print("  5 - Register alias")
    print("  h - Health check")
    print("  q - Quit")
    print("="*70 + "\n")
    
    while True:
        choice = input("Enter command: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        
        elif choice == '1':
            client.run_all_tests()
        
        elif choice == '2':
            print("\nAvailable endpoints:")
            print("  1. Health check")
            print("  2. Get alias")
            print("  3. Register alias")
            print("  4. Process command")
            print("  5. Transaction history")
            endpoint = input("Choose endpoint: ").strip()
            
            if endpoint == '1':
                client.test_health()
            elif endpoint == '2':
                alias = input("Enter alias (e.g., @alice): ").strip()
                client.test_get_alias(alias)
            elif endpoint == '3':
                alias = input("Enter alias (e.g., @newuser): ").strip()
                address = input("Enter address: ").strip()
                client.test_register_alias(alias, address)
            elif endpoint == '4':
                command = input("Enter payment command: ").strip()
                client.test_process_command(command)
            elif endpoint == '5':
                address = input("Enter address: ").strip()
                client.test_get_history(address)
        
        elif choice == '3':
            command = input("Enter payment command: ").strip()
            client.test_process_command(command)
        
        elif choice == '4':
            alias = input("Enter alias (e.g., @alice): ").strip()
            client.test_get_alias(alias)
        
        elif choice == '5':
            alias = input("Enter alias (e.g., @newuser): ").strip()
            address = input("Enter address (0x...): ").strip()
            client.test_register_alias(alias, address)
        
        elif choice == 'h':
            client.test_health()
        
        else:
            print("Invalid command. Try again.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Run automated test suite
        client = BulutTestClient()
        success = client.run_all_tests()
        sys.exit(0 if success else 1)
    else:
        # Run interactive mode
        interactive_mode()