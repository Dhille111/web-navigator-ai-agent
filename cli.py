"""
Command-line interface for the Local AI Agent
"""

import asyncio
import argparse
import json
import os
import sys
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

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


class CLIManager:
    """Command-line interface manager"""
    
    def __init__(self):
        self.orchestrator = None
        self.setup_orchestrator()
    
    def setup_orchestrator(self):
        """Setup orchestrator with CLI configuration"""
        try:
            # Configure components
            browser_config = BrowserConfig(
                headless=os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true',
                browser_type=os.getenv('BROWSER_TYPE', 'chromium')
            )
            
            storage_config = ExportConfig(
                output_dir=os.getenv('OUTPUT_DIR', 'exports'),
                json_format=True,
                csv_format=True
            )
            
            memory = MemoryFactory.create_memory(
                persist_to_disk=os.getenv('MEMORY_PERSIST', 'true').lower() == 'true'
            )
            
            self.orchestrator = OrchestratorFactory.create_orchestrator(
                browser_config=browser_config,
                storage_config=storage_config,
                memory=memory
            )
            
            logger.info("Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            sys.exit(1)
    
    async def execute_task(self, instruction: str, output_format: str = 'json', output_file: Optional[str] = None) -> Dict[str, Any]:
        """Execute a task and return results"""
        try:
            logger.info(f"Executing task: {instruction}")
            
            result = await self.orchestrator.execute(instruction)
            
            # Prepare output
            output = {
                'task_id': result.task_id,
                'status': result.status,
                'instruction': result.instruction,
                'results': result.results,
                'execution_time': result.execution_time,
                'error_message': result.error_message,
                'metadata': result.metadata
            }
            
            # Save to file if specified
            if output_file:
                self._save_output(output, output_file, output_format)
            
            return output
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
    
    def _save_output(self, output: Dict[str, Any], filename: str, format: str):
        """Save output to file"""
        try:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(output, f, indent=2, ensure_ascii=False)
            elif format.lower() == 'csv':
                import pandas as pd
                if output.get('results'):
                    df = pd.DataFrame(output['results'])
                    df.to_csv(filepath, index=False, encoding='utf-8')
                else:
                    # Create empty CSV with metadata
                    df = pd.DataFrame([{
                        'task_id': output['task_id'],
                        'status': output['status'],
                        'instruction': output['instruction'],
                        'execution_time': output['execution_time']
                    }])
                    df.to_csv(filepath, index=False, encoding='utf-8')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Output saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save output: {e}")
    
    def show_stats(self):
        """Show session statistics"""
        try:
            stats = self.orchestrator.get_session_stats()
            
            print("\n" + "="*50)
            print("SESSION STATISTICS")
            print("="*50)
            print(f"Session ID: {stats.get('session_id', 'N/A')}")
            print(f"Start Time: {stats.get('start_time', 'N/A')}")
            print(f"Last Activity: {stats.get('last_activity', 'N/A')}")
            print(f"Total Tasks: {stats.get('total_tasks', 0)}")
            print(f"Successful: {stats.get('successful_tasks', 0)}")
            print(f"Failed: {stats.get('failed_tasks', 0)}")
            print(f"Success Rate: {(stats.get('success_rate', 0) * 100):.1f}%")
            print("="*50)
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
    
    def show_history(self, limit: int = 10):
        """Show task history"""
        try:
            history = self.orchestrator.get_task_history()
            
            if not history:
                print("No task history available")
                return
            
            print(f"\n{'='*80}")
            print("TASK HISTORY")
            print(f"{'='*80}")
            print(f"{'Task ID':<12} {'Status':<8} {'Instruction':<40} {'Results':<8} {'Time':<8}")
            print("-" * 80)
            
            for task in history[:limit]:
                task_id = task['task_id'][:8] + "..."
                status = task['status']
                instruction = task['instruction'][:37] + "..." if len(task['instruction']) > 40 else task['instruction']
                results = task.get('result_count', 0)
                time_str = f"{task.get('execution_time', 0):.1f}s"
                
                print(f"{task_id:<12} {status:<8} {instruction:<40} {results:<8} {time_str:<8}")
            
            print(f"{'='*80}")
            
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
    
    def clear_memory(self):
        """Clear session memory"""
        try:
            self.orchestrator.clear_memory()
            print("Session memory cleared successfully")
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
    
    def export_memory(self, filename: str):
        """Export session memory"""
        try:
            filepath = self.orchestrator.memory.export_memories(filename)
            if filepath:
                print(f"Memory exported to: {filepath}")
            else:
                print("Failed to export memory")
                
        except Exception as e:
            logger.error(f"Failed to export memory: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Local AI Agent - Execute natural language instructions with web automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "search laptops under ₹50,000 and list top 5 with price and link"
  python cli.py "navigate to https://example.com and take a screenshot" --headful
  python cli.py "extract all product information from the current page" --output results.json
  python cli.py --stats
  python cli.py --history --limit 20
  python cli.py --clear-memory
        """
    )
    
    # Main command
    parser.add_argument(
        'instruction',
        nargs='?',
        help='Natural language instruction to execute'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        help='Output file path'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )
    
    # Browser options
    parser.add_argument(
        '--headful',
        action='store_true',
        help='Run browser in headful mode (visible)'
    )
    parser.add_argument(
        '--browser',
        choices=['chromium', 'firefox', 'webkit'],
        default='chromium',
        help='Browser type to use (default: chromium)'
    )
    
    # Memory options
    parser.add_argument(
        '--persist-memory',
        action='store_true',
        help='Persist session memory to disk'
    )
    parser.add_argument(
        '--clear-memory',
        action='store_true',
        help='Clear session memory'
    )
    
    # Information commands
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show session statistics'
    )
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show task history'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit number of history entries to show (default: 10)'
    )
    
    # Export commands
    parser.add_argument(
        '--export-memory',
        help='Export session memory to file'
    )
    
    # Debug options
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Set environment variables based on CLI args
    if args.headful:
        os.environ['BROWSER_HEADLESS'] = 'false'
    if args.browser:
        os.environ['BROWSER_TYPE'] = args.browser
    if args.persist_memory:
        os.environ['MEMORY_PERSIST'] = 'true'
    
    # Create CLI manager
    cli = CLIManager()
    
    try:
        # Handle different commands
        if args.clear_memory:
            cli.clear_memory()
        elif args.stats:
            cli.show_stats()
        elif args.history:
            cli.show_history(args.limit)
        elif args.export_memory:
            cli.export_memory(args.export_memory)
        elif args.instruction:
            # Execute task
            result = asyncio.run(cli.execute_task(
                args.instruction,
                args.format,
                args.output
            ))
            
            # Display results
            if args.verbose or not args.output:
                print(f"\nTask ID: {result.get('task_id', 'N/A')}")
                print(f"Status: {result.get('status', 'N/A')}")
                print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
                
                if result.get('error_message'):
                    print(f"Error: {result['error_message']}")
                
                if result.get('results'):
                    print(f"\nResults ({len(result['results'])} items):")
                    print("-" * 50)
                    for i, item in enumerate(result['results'][:5], 1):  # Show first 5
                        print(f"{i}. {item.get('title', 'N/A')}")
                        if item.get('price'):
                            print(f"   Price: {item['price']}")
                        if item.get('url'):
                            print(f"   URL: {item['url']}")
                        print()
                    
                    if len(result['results']) > 5:
                        print(f"... and {len(result['results']) - 5} more items")
                else:
                    print("No results found")
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
