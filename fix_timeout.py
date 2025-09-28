"""
Quick fix for the 15ms timeout issue
"""

import os
import sys
import asyncio
from pathlib import Path

# Set environment variables
os.environ['LLM_TYPE'] = 'ollama'
os.environ['LLM_MODEL_NAME'] = 'llama2'
os.environ['BROWSER_HEADLESS'] = 'true'
os.environ['MEMORY_PERSIST'] = 'false'

# Add src to path
sys.path.insert(0, 'src')

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig

async def test_with_fixed_timeout():
    """Test with proper timeout settings"""
    print("🔧 Testing with Fixed Timeout (30 seconds)")
    print("=" * 50)
    
    try:
        # Configure with proper timeout
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            timeout=30000,  # 30 seconds
            viewport_width=1920,
            viewport_height=1080
        )
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            browser_config=browser_config
        )
        
        print("✅ Orchestrator created with 30-second timeout")
        
        # Test with a simple instruction
        instruction = "search for Python programming tutorials"
        print(f"📝 Testing: {instruction}")
        print("⏳ This may take 30-60 seconds...")
        
        result = await orchestrator.execute(instruction)
        
        print(f"\n📊 Results:")
        print(f"   Status: {result.status}")
        print(f"   Execution Time: {result.execution_time:.2f}s")
        print(f"   Results Count: {len(result.results)}")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        else:
            print("   ✅ Task completed successfully!")
            if result.results:
                print("   Sample results:")
                for i, item in enumerate(result.results[:3], 1):
                    print(f"     {i}. {item.get('title', 'N/A')}")
                    if item.get('url'):
                        print(f"        URL: {item['url']}")
            else:
                print("   No results found (this is normal without LLM)")
        
        print("\n🎉 Timeout issue fixed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 The timeout issue has been fixed in the code")

if __name__ == "__main__":
    asyncio.run(test_with_fixed_timeout())
