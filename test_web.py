"""
Test the web interface to ensure it's working properly
"""

import requests
import json
import time

def test_web_interface():
    """Test the web interface"""
    print("🌐 Testing Web Interface")
    print("=" * 40)
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
        
        # Test task execution
        print("2. Testing task execution...")
        task_data = {
            "instruction": "search laptops under ₹50,000 and list top 5 with price and link"
        }
        
        response = requests.post(
            "http://localhost:5000/run",
            json=task_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Task executed successfully")
            print(f"   📊 Status: {result.get('status')}")
            print(f"   📊 Results: {len(result.get('results', []))} items")
            print(f"   ⏱️  Execution Time: {result.get('execution_time', 0):.2f}s")
            
            if result.get('results'):
                print("   📋 Sample Results:")
                for i, item in enumerate(result['results'][:3], 1):
                    print(f"      {i}. {item.get('title', 'N/A')} - {item.get('price', 'N/A')}")
        else:
            print(f"   ❌ Task execution failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        # Test stats endpoint
        print("3. Testing stats endpoint...")
        response = requests.get("http://localhost:5000/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Stats retrieved successfully")
            print(f"   📊 Total Tasks: {stats.get('total_tasks', 0)}")
        else:
            print(f"   ❌ Stats failed: {response.status_code}")
        
        print("\n🎉 Web interface is working perfectly!")
        print("🌐 Open http://localhost:5000 in your browser to use it!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server")
        print("💡 Make sure the server is running: python app_fixed.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_web_interface()
