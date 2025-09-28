"""
Test the professional UI with speech features
"""

import requests
import json
import time

def test_professional_ui():
    """Test the professional UI interface"""
    print("🎨 Testing Professional UI with Speech Features")
    print("=" * 60)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
        
        # Test main page
        print("2. Testing main page...")
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Main page loaded successfully")
            if "AI Agent Pro" in response.text:
                print("   ✅ Professional branding detected")
            if "speechToText" in response.text:
                print("   ✅ Speech-to-Text feature detected")
            if "textToSpeech" in response.text:
                print("   ✅ Text-to-Speech feature detected")
            if "particles" in response.text:
                print("   ✅ Animated particles detected")
            if "glass-card" in response.text:
                print("   ✅ Glass morphism design detected")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
            return
        
        # Test task execution with mock data
        print("3. Testing task execution...")
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
        print("4. Testing stats endpoint...")
        response = requests.get("http://localhost:5000/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("   ✅ Stats retrieved successfully")
            print(f"   📊 Total Tasks: {stats.get('total_tasks', 0)}")
            print(f"   📊 Success Rate: {stats.get('success_rate', 0):.1%}")
        else:
            print(f"   ❌ Stats failed: {response.status_code}")
        
        # Test history endpoint
        print("5. Testing history endpoint...")
        response = requests.get("http://localhost:5000/history", timeout=5)
        if response.status_code == 200:
            history = response.json()
            print("   ✅ History retrieved successfully")
            print(f"   📊 History entries: {len(history)}")
        else:
            print(f"   ❌ History failed: {response.status_code}")
        
        print("\n🎉 Professional UI Features:")
        print("   ✨ Glass morphism design")
        print("   ✨ Animated gradient background")
        print("   ✨ Floating particles animation")
        print("   ✨ Speech-to-Text integration")
        print("   ✨ Text-to-Speech integration")
        print("   ✨ Professional color scheme")
        print("   ✨ Responsive design")
        print("   ✨ Smooth animations")
        print("   ✨ Modern typography")
        print("   ✨ Interactive elements")
        
        print("\n🌐 Open http://localhost:5000 in your browser to see the amazing UI!")
        print("🎤 Try the speech features - click the microphone and speaker buttons!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to web server")
        print("💡 Make sure the server is running: python app_fixed.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_professional_ui()
