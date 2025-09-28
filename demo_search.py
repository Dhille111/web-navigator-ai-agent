"""
Demo script showing how to use the Local AI Agent
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig
from src.utils.storage import ExportConfig
from src.memory.session_memory import MemoryFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_search_laptops():
    """Demo: Search for laptops under ₹50,000"""
    print("="*60)
    print("DEMO: Search for laptops under ₹50,000")
    print("="*60)
    
    # Configure components
    browser_config = BrowserConfig(
        headless=True,  # Set to False to see browser in action
        browser_type="chromium"
    )
    
    storage_config = ExportConfig(
        output_dir="demo_exports",
        json_format=True,
        csv_format=True
    )
    
    memory = MemoryFactory.create_memory(
        persist_to_disk=True,
        memory_file="demo_memory.json"
    )
    
    # Create orchestrator
    orchestrator = OrchestratorFactory.create_orchestrator(
        browser_config=browser_config,
        storage_config=storage_config,
        memory=memory
    )
    
    try:
        # Execute search task
        instruction = "search laptops under ₹50,000 and list top 5 with price and link"
        print(f"Instruction: {instruction}")
        print("\nExecuting task...")
        
        result = await orchestrator.execute(instruction)
        
        # Display results
        print(f"\nTask ID: {result.task_id}")
        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        else:
            print(f"\nResults ({len(result.results)} items):")
            print("-" * 50)
            
            for i, item in enumerate(result.results, 1):
                print(f"{i}. {item.get('title', 'N/A')}")
                if item.get('price'):
                    print(f"   Price: {item['price']}")
                if item.get('url'):
                    print(f"   URL: {item['url']}")
                if item.get('description'):
                    print(f"   Description: {item['description']}")
                print()
        
        # Show session stats
        stats = orchestrator.get_session_stats()
        print(f"\nSession Stats:")
        print(f"Total Tasks: {stats.get('total_tasks', 0)}")
        print(f"Successful: {stats.get('successful_tasks', 0)}")
        print(f"Failed: {stats.get('failed_tasks', 0)}")
        print(f"Success Rate: {(stats.get('success_rate', 0) * 100):.1f}%")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")


async def demo_navigate_and_screenshot():
    """Demo: Navigate to a website and take screenshot"""
    print("\n" + "="*60)
    print("DEMO: Navigate to website and take screenshot")
    print("="*60)
    
    # Configure components
    browser_config = BrowserConfig(
        headless=False,  # Show browser for this demo
        browser_type="chromium"
    )
    
    storage_config = ExportConfig(
        output_dir="demo_exports",
        json_format=True,
        csv_format=True
    )
    
    memory = MemoryFactory.create_memory(
        persist_to_disk=True,
        memory_file="demo_memory.json"
    )
    
    # Create orchestrator
    orchestrator = OrchestratorFactory.create_orchestrator(
        browser_config=browser_config,
        storage_config=storage_config,
        memory=memory
    )
    
    try:
        # Execute navigation task
        instruction = "navigate to https://www.google.com and take a screenshot"
        print(f"Instruction: {instruction}")
        print("\nExecuting task...")
        
        result = await orchestrator.execute(instruction)
        
        # Display results
        print(f"\nTask ID: {result.task_id}")
        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        else:
            print("Navigation completed successfully!")
            if result.metadata.get('screenshot_path'):
                print(f"Screenshot saved to: {result.metadata['screenshot_path']}")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")


async def demo_extract_content():
    """Demo: Extract content from a webpage"""
    print("\n" + "="*60)
    print("DEMO: Extract content from webpage")
    print("="*60)
    
    # Configure components
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium"
    )
    
    storage_config = ExportConfig(
        output_dir="demo_exports",
        json_format=True,
        csv_format=True
    )
    
    memory = MemoryFactory.create_memory(
        persist_to_disk=True,
        memory_file="demo_memory.json"
    )
    
    # Create orchestrator
    orchestrator = OrchestratorFactory.create_orchestrator(
        browser_config=browser_config,
        storage_config=storage_config,
        memory=memory
    )
    
    try:
        # Execute extraction task
        instruction = "extract all product information from https://example.com"
        print(f"Instruction: {instruction}")
        print("\nExecuting task...")
        
        result = await orchestrator.execute(instruction)
        
        # Display results
        print(f"\nTask ID: {result.task_id}")
        print(f"Status: {result.status}")
        print(f"Execution Time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        else:
            print(f"\nExtracted {len(result.results)} items:")
            for i, item in enumerate(result.results, 1):
                print(f"{i}. {item.get('title', 'N/A')}")
                if item.get('text'):
                    print(f"   Text: {item['text'][:100]}...")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")


def demo_cli_usage():
    """Demo: Show CLI usage examples"""
    print("\n" + "="*60)
    print("DEMO: CLI Usage Examples")
    print("="*60)
    
    print("Here are some example CLI commands you can try:")
    print()
    print("1. Basic search:")
    print("   python cli.py \"search laptops under ₹50,000 and list top 5 with price and link\"")
    print()
    print("2. Navigate with visible browser:")
    print("   python cli.py \"navigate to https://example.com and take a screenshot\" --headful")
    print()
    print("3. Extract content:")
    print("   python cli.py \"extract all product information from the current page\"")
    print()
    print("4. Save results to file:")
    print("   python cli.py \"search gaming laptops\" --output results.json --format json")
    print()
    print("5. Show session statistics:")
    print("   python cli.py --stats")
    print()
    print("6. Show task history:")
    print("   python cli.py --history --limit 10")
    print()
    print("7. Clear session memory:")
    print("   python cli.py --clear-memory")
    print()
    print("8. Export session memory:")
    print("   python cli.py --export-memory memory_backup.json")


def demo_web_interface():
    """Demo: Show web interface usage"""
    print("\n" + "="*60)
    print("DEMO: Web Interface Usage")
    print("="*60)
    
    print("To use the web interface:")
    print()
    print("1. Start the Flask server:")
    print("   python app.py")
    print()
    print("2. Open your browser and go to:")
    print("   http://localhost:5000")
    print()
    print("3. Enter your instruction in the text area")
    print("4. Click 'Execute Task' to run the task")
    print("5. View results, export data, and check history")
    print()
    print("Available endpoints:")
    print("  GET  /              - Web interface")
    print("  POST /run           - Execute task")
    print("  GET  /results/<id>  - Get task results")
    print("  GET  /export/<id>/csv - Export as CSV")
    print("  GET  /export/<id>/json - Export as JSON")
    print("  GET  /history       - Get task history")
    print("  GET  /stats         - Get session stats")


async def main():
    """Main demo function"""
    print("Local AI Agent - Demo Script")
    print("="*60)
    print("This demo shows how to use the Local AI Agent")
    print("Make sure you have set up the required dependencies first!")
    print()
    
    # Check if required environment variables are set
    if not os.getenv('LLM_MODEL_PATH') and not os.getenv('LLM_TYPE'):
        print("WARNING: No LLM configuration found!")
        print("Please set LLM_MODEL_PATH or LLM_TYPE environment variable")
        print("Example: export LLM_TYPE=ollama")
        print()
    
    try:
        # Run demos
        await demo_search_laptops()
        await demo_navigate_and_screenshot()
        await demo_extract_content()
        
        # Show usage examples
        demo_cli_usage()
        demo_web_interface()
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("Check the 'demo_exports' directory for saved results")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")
        print("Make sure all dependencies are installed and configured correctly")


if __name__ == "__main__":
    asyncio.run(main())
