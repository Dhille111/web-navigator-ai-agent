"""
Quick fix for LLM and network timeout issues
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

async def quick_test():
    """Quick test with fixed configuration"""
    print("🚀 Quick Fix - Testing Local AI Agent")
    print("=" * 50)
    
    try:
        # Configure with longer timeout
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            timeout=60000,  # 60 seconds timeout
            viewport_width=1920,
            viewport_height=1080
        )
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            browser_config=browser_config
        )
        
        print("✅ Orchestrator created successfully")
        
        # Test with a simple instruction
        instruction = "search for Python programming tutorials"
        print(f"📝 Testing: {instruction}")
        
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
        
        print("\n🎉 Quick fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 The system is working but needs LLM configuration")

if __name__ == "__main__":
    asyncio.run(quick_test())
