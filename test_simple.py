"""
Simple test script to demonstrate the Local AI Agent
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig
from src.utils.storage import ExportConfig
from src.memory.session_memory import MemoryFactory


async def test_simple_search():
    """Test a simple search task"""
    print("🤖 Local AI Agent - Simple Test")
    print("=" * 50)
    
    try:
        # Configure components
        browser_config = BrowserConfig(
            headless=True,  # Set to False to see browser
            browser_type="chromium"
        )
        
        storage_config = ExportConfig(
            output_dir="test_exports",
            json_format=True,
            csv_format=True
        )
        
        memory = MemoryFactory.create_memory(
            persist_to_disk=False  # Don't persist for test
        )
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            browser_config=browser_config,
            storage_config=storage_config,
            memory=memory
        )
        
        print("✅ Orchestrator created successfully")
        
        # Test instruction
        instruction = "search for information about Python programming"
        print(f"📝 Instruction: {instruction}")
        print("⏳ Executing task...")
        
        # Execute task
        result = await orchestrator.execute(instruction)
        
        # Display results
        print(f"\n📊 Results:")
        print(f"   Task ID: {result.task_id}")
        print(f"   Status: {result.status}")
        print(f"   Execution Time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"   Error: {result.error_message}")
        else:
            print(f"   Results Count: {len(result.results)}")
            if result.results:
                print("   Sample Results:")
                for i, item in enumerate(result.results[:3], 1):
                    print(f"     {i}. {item.get('title', 'N/A')}")
                    if item.get('url'):
                        print(f"        URL: {item['url']}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Make sure you have configured an LLM (Ollama, GPT4All, or LLaMA)")


if __name__ == "__main__":
    asyncio.run(test_simple_search())
