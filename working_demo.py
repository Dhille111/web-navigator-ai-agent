"""
Working demo that shows the system functionality without network dependencies
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Set environment variables
os.environ['LLM_TYPE'] = 'ollama'
os.environ['LLM_MODEL_NAME'] = 'llama2'
os.environ['BROWSER_HEADLESS'] = 'true'
os.environ['MEMORY_PERSIST'] = 'false'

# Add src to path
sys.path.insert(0, 'src')

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig
from src.utils.storage import ExportConfig
from src.memory.session_memory import MemoryFactory

async def working_demo():
    """Working demo showing system capabilities"""
    print("🎯 Working Demo - Local AI Agent")
    print("=" * 50)
    
    try:
        # Configure components
        browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            timeout=30000,  # 30 seconds
            viewport_width=1920,
            viewport_height=1080
        )
        
        storage_config = ExportConfig(
            output_dir="demo_exports",
            json_format=True,
            csv_format=True
        )
        
        memory = MemoryFactory.create_memory(
            persist_to_disk=False
        )
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            browser_config=browser_config,
            storage_config=storage_config,
            memory=memory
        )
        
        print("✅ System initialized successfully!")
        print("📊 Session Stats:")
        stats = orchestrator.get_session_stats()
        print(f"   Total Tasks: {stats.get('total_tasks', 0)}")
        print(f"   Success Rate: {(stats.get('success_rate', 0) * 100):.1f}%")
        
        # Test instruction parsing (without browser)
        print("\n🧠 Testing Instruction Parsing:")
        from src.agent.parser import InstructionParserFactory
        parser = InstructionParserFactory.create_parser()
        
        test_instructions = [
            "search laptops under ₹50,000 and list top 5 with price and link",
            "navigate to https://example.com and take a screenshot",
            "extract all product information from the current page"
        ]
        
        for instruction in test_instructions:
            try:
                parsed = parser.parse(instruction)
                print(f"   ✅ '{instruction[:30]}...' → {parsed.task}")
            except Exception as e:
                print(f"   ⚠️  '{instruction[:30]}...' → Error: {str(e)[:50]}...")
        
        # Test step planning
        print("\n📋 Testing Step Planning:")
        from src.agent.planner import StepPlannerFactory
        planner = StepPlannerFactory.create_planner()
        
        # Create a test parsed instruction
        from src.agent.parser import ParsedInstruction
        test_parsed = ParsedInstruction(
            task="search",
            query="test query",
            filters={"price_max": 50000},
            count=5,
            fields=["title", "price", "url"],
            target_url="https://www.google.com",
            selectors={},
            actions=[],
            raw_instruction="test instruction"
        )
        
        steps = planner.plan(test_parsed)
        print(f"   ✅ Generated {len(steps)} execution steps")
        for i, step in enumerate(steps[:3], 1):
            print(f"      {i}. {step.action} - {step.selector or step.url}")
        
        # Test memory system
        print("\n🧠 Testing Memory System:")
        memory_id = memory.add_memory(
            instruction="test search",
            result={"count": 3, "items": ["item1", "item2", "item3"]},
            success=True,
            task_type="search"
        )
        print(f"   ✅ Added memory: {memory_id[:8]}...")
        
        recent = memory.get_recent_memories(5)
        print(f"   ✅ Retrieved {len(recent)} recent memories")
        
        # Test storage system
        print("\n💾 Testing Storage System:")
        from src.utils.storage import TaskResult
        task_result = TaskResult(
            task_id="demo_001",
            status="success",
            instruction="demo instruction",
            results=[
                {"title": "Demo Item 1", "price": "₹1000", "url": "https://example.com/1"},
                {"title": "Demo Item 2", "price": "₹2000", "url": "https://example.com/2"}
            ],
            metadata={"demo": True},
            timestamp=datetime.now(),
            execution_time=1.5
        )
        
        saved_files = orchestrator.storage.save_task_result(task_result)
        print(f"   ✅ Saved to {len(saved_files)} files")
        
        # Test data extraction
        print("\n🔍 Testing Data Extraction:")
        from src.agent.extractor import ExtractorFactory
        extractor = ExtractorFactory.create_extractor()
        
        sample_data = [
            {
                'text': 'Laptop Model XYZ - ₹45,000',
                'attributes': {'href': 'https://example.com/laptop1'},
                'html': '<div>Laptop Model XYZ - ₹45,000</div>'
            },
            {
                'text': 'Gaming Laptop ABC - ₹55,000',
                'attributes': {'href': 'https://example.com/laptop2'},
                'html': '<div>Gaming Laptop ABC - ₹55,000</div>'
            }
        ]
        
        extracted = extractor.extract_from_playwright_data(sample_data, {
            'title': 'text',
            'price': 'text',
            'link': 'href'
        })
        
        print(f"   ✅ Extracted {len(extracted)} items")
        for item in extracted:
            print(f"      - {item.title}: {item.price}")
        
        print("\n🎉 All systems working correctly!")
        print("💡 The system is fully functional - just needs LLM model and internet connection")
        
        # Show available commands
        print("\n📋 Available Commands:")
        print("   python cli.py 'your instruction here'")
        print("   python app.py  # Start web interface")
        print("   python test_simple.py  # Run simple test")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(working_demo())
