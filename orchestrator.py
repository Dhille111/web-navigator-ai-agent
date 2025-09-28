"""
Orchestrator for coordinating the AI agent's execution flow
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .llm_adapter import LLMManager, create_default_llm_manager
from .parser import InstructionParser, InstructionParserFactory
from .planner import StepPlanner, StepPlannerFactory, Step
from .browser_controller import BrowserController, BrowserControllerFactory, BrowserConfig
from .extractor import ContentExtractor, ExtractorFactory
from ..utils.storage import DataStorage, StorageFactory, TaskResult, ExportConfig
from ..memory.session_memory import SessionMemory, MemoryFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    status: str  # success, error, partial
    instruction: str
    results: List[Dict[str, Any]]
    execution_time: float
    error_message: Optional[str] = None
    logs: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []
        if self.metadata is None:
            self.metadata = {}


class Orchestrator:
    """Main orchestrator for coordinating AI agent execution"""
    
    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        browser_config: Optional[BrowserConfig] = None,
        storage_config: Optional[ExportConfig] = None,
        memory: Optional[SessionMemory] = None
    ):
        self.llm_manager = llm_manager or create_default_llm_manager()
        self.browser_config = browser_config or BrowserConfig()
        self.storage_config = storage_config or ExportConfig()
        
        # Initialize components
        self.parser = InstructionParserFactory.create_parser(self.llm_manager)
        self.planner = StepPlannerFactory.create_planner()
        self.extractor = ExtractorFactory.create_extractor()
        self.storage = StorageFactory.create_storage(self.storage_config)
        self.memory = memory or MemoryFactory.create_memory()
        
        # Execution state
        self.current_task_id: Optional[str] = None
        self.execution_logs: List[Dict[str, Any]] = []
    
    async def execute(self, instruction: str, task_id: Optional[str] = None) -> ExecutionResult:
        """Execute a natural language instruction"""
        start_time = time.time()
        task_id = task_id or str(uuid.uuid4())
        self.current_task_id = task_id
        
        try:
            self._log("info", f"Starting execution of task {task_id}", {"instruction": instruction})
            
            # Get context from memory
            context = self.memory.get_context_for_instruction(instruction)
            self._log("info", "Retrieved context from memory", {"context_keys": list(context.keys())})
            
            # Parse instruction
            parsed_instruction = self.parser.parse(instruction)
            self._log("info", "Parsed instruction", {
                "task": parsed_instruction.task,
                "query": parsed_instruction.query,
                "actions_count": len(parsed_instruction.actions)
            })
            
            # Plan execution steps
            steps = self.planner.plan(parsed_instruction)
            self._log("info", "Planned execution steps", {"steps_count": len(steps)})
            
            # Execute steps
            results = await self._execute_steps(steps, parsed_instruction)
            
            # Process results
            processed_results = self._process_results(results, parsed_instruction)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create execution result
            execution_result = ExecutionResult(
                task_id=task_id,
                status="success" if results else "error",
                instruction=instruction,
                results=processed_results,
                execution_time=execution_time,
                logs=self.execution_logs.copy(),
                metadata={
                    "parsed_instruction": {
                        "task": parsed_instruction.task,
                        "query": parsed_instruction.query,
                        "filters": parsed_instruction.filters,
                        "count": parsed_instruction.count,
                        "fields": parsed_instruction.fields
                    },
                    "steps_executed": len(steps),
                    "results_count": len(processed_results)
                }
            )
            
            # Save to memory
            self.memory.add_memory(
                instruction=instruction,
                result=processed_results,
                success=execution_result.status == "success",
                task_type=parsed_instruction.task,
                metadata={"execution_time": execution_time, "task_id": task_id}
            )
            
            # Save to storage
            task_result = TaskResult(
                task_id=task_id,
                status=execution_result.status,
                instruction=instruction,
                results=processed_results,
                metadata=execution_result.metadata,
                timestamp=datetime.now(),
                execution_time=execution_time
            )
            self.storage.save_task_result(task_result)
            
            self._log("info", f"Completed task {task_id}", {
                "status": execution_result.status,
                "results_count": len(processed_results),
                "execution_time": execution_time
            })
            
            return execution_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self._log("error", f"Task {task_id} failed", {"error": error_msg})
            
            # Save error to memory
            self.memory.add_memory(
                instruction=instruction,
                result={"error": error_msg},
                success=False,
                task_type="error",
                metadata={"execution_time": execution_time, "task_id": task_id}
            )
            
            return ExecutionResult(
                task_id=task_id,
                status="error",
                instruction=instruction,
                results=[],
                execution_time=execution_time,
                error_message=error_msg,
                logs=self.execution_logs.copy()
            )
        
        finally:
            self.current_task_id = None
            self.execution_logs.clear()
    
    async def _execute_steps(self, steps: List[Step], parsed_instruction) -> List[Dict[str, Any]]:
        """Execute planned steps using browser automation"""
        results = []
        
        async with BrowserController(self.browser_config) as browser:
            for i, step in enumerate(steps):
                try:
                    self._log("info", f"Executing step {i+1}/{len(steps)}", {
                        "action": step.action,
                        "selector": step.selector,
                        "value": step.value,
                        "url": step.url
                    })
                    
                    # Execute step with retry logic
                    step_result = await self._execute_step_with_retry(browser, step)
                    
                    if step_result.success:
                        self._log("info", f"Step {i+1} completed successfully")
                        
                        # Extract data if this is an extract step
                        if step.action == "extract" and step_result.data:
                            extracted_data = self._extract_data_from_step_result(step_result, parsed_instruction)
                            if extracted_data:
                                results.extend(extracted_data)
                    else:
                        self._log("warning", f"Step {i+1} failed", {"error": step_result.error})
                        
                        # Continue with next step unless it's a critical step
                        if step.action in ["goto", "click"]:
                            self._log("error", f"Critical step {i+1} failed, stopping execution")
                            break
                    
                except Exception as e:
                    self._log("error", f"Step {i+1} execution error", {"error": str(e)})
                    continue
        
        return results
    
    async def _execute_step_with_retry(self, browser: BrowserController, step: Step) -> Any:
        """Execute a single step with retry logic"""
        last_error = None
        
        for attempt in range(step.retries):
            try:
                if step.action == "goto":
                    return await browser.goto(step.url, step.timeout)
                elif step.action == "click":
                    return await browser.safe_click(step.selector, step.timeout)
                elif step.action == "fill":
                    return await browser.fill(step.selector, step.value, step.timeout)
                elif step.action == "extract":
                    return await browser.safe_extract(step.selector, step.multiple, step.timeout)
                elif step.action == "wait":
                    return await browser.wait(step.timeout)
                elif step.action == "screenshot":
                    return await browser.screenshot()
                else:
                    raise ValueError(f"Unknown action: {step.action}")
                    
            except Exception as e:
                last_error = e
                if attempt < step.retries - 1:
                    self._log("warning", f"Step failed, retrying ({attempt+1}/{step.retries})", {"error": str(e)})
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    self._log("error", f"Step failed after {step.retries} attempts", {"error": str(e)})
        
        # Return failed result
        from .browser_controller import ActionResult
        return ActionResult(
            success=False,
            error=str(last_error),
            metadata={"action": step.action, "attempts": step.retries}
        )
    
    def _extract_data_from_step_result(self, step_result, parsed_instruction) -> List[Dict[str, Any]]:
        """Extract structured data from step result"""
        try:
            if not step_result.data:
                return []
            
            # Use extractor to process the data
            if isinstance(step_result.data, list):
                # Multiple elements extracted
                extracted_data = self.extractor.extract_from_playwright_data(
                    step_result.data,
                    parsed_instruction.selectors
                )
            else:
                # Single element extracted
                extracted_data = self.extractor.extract_from_playwright_data(
                    [step_result.data],
                    parsed_instruction.selectors
                )
            
            # Convert to dictionary format
            results = []
            for data in extracted_data:
                result_dict = data.to_dict()
                
                # Filter by price if specified
                if parsed_instruction.filters.get('price_max'):
                    max_price = parsed_instruction.filters['price_max']
                    if result_dict.get('price'):
                        # Extract numeric price for comparison
                        import re
                        price_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', result_dict['price'])
                        if price_match:
                            price_value = float(price_match.group(1).replace(',', ''))
                            if price_value > max_price:
                                continue
                
                results.append(result_dict)
            
            # Sort results if specified
            if parsed_instruction.filters.get('sort') == 'rating':
                results = self.extractor.sort_by_rating(results)
            elif parsed_instruction.filters.get('sort') == 'price':
                results = self.extractor.sort_by_price(results)
            
            # Limit results
            limit = parsed_instruction.count or 5
            results = self.extractor.limit_results(results, limit)
            
            return results
            
        except Exception as e:
            self._log("error", "Failed to extract data from step result", {"error": str(e)})
            return []
    
    def _process_results(self, results: List[Dict[str, Any]], parsed_instruction) -> List[Dict[str, Any]]:
        """Process and clean up results"""
        try:
            if not results:
                return []
            
            # Remove duplicates
            results = self.extractor.deduplicate(results)
            
            # Apply filters
            if parsed_instruction.filters:
                if 'price_max' in parsed_instruction.filters:
                    max_price = parsed_instruction.filters['price_max']
                    results = self.extractor.filter_by_price(results, max_price=max_price)
                
                if 'price_min' in parsed_instruction.filters:
                    min_price = parsed_instruction.filters['price_min']
                    results = self.extractor.filter_by_price(results, min_price=min_price)
            
            # Sort results
            if parsed_instruction.filters.get('sort') == 'rating':
                results = self.extractor.sort_by_rating(results)
            elif parsed_instruction.filters.get('sort') == 'price':
                results = self.extractor.sort_by_price(results)
            
            # Limit results
            limit = parsed_instruction.count or 5
            results = self.extractor.limit_results(results, limit)
            
            return results
            
        except Exception as e:
            self._log("error", "Failed to process results", {"error": str(e)})
            return results
    
    def _log(self, level: str, message: str, data: Dict[str, Any] = None):
        """Log execution information"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "task_id": self.current_task_id,
            "data": data or {}
        }
        
        self.execution_logs.append(log_entry)
        
        if level == "error":
            logger.error(f"[{self.current_task_id}] {message}", extra=data)
        elif level == "warning":
            logger.warning(f"[{self.current_task_id}] {message}", extra=data)
        else:
            logger.info(f"[{self.current_task_id}] {message}", extra=data)
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """Get task execution history"""
        return self.storage.list_task_results()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self.memory.get_session_stats()
    
    def clear_memory(self):
        """Clear session memory"""
        self.memory.clear_memories()
        self._log("info", "Cleared session memory")


class OrchestratorFactory:
    """Factory for creating orchestrator instances"""
    
    @staticmethod
    def create_orchestrator(
        llm_manager: Optional[LLMManager] = None,
        browser_config: Optional[BrowserConfig] = None,
        storage_config: Optional[ExportConfig] = None,
        memory: Optional[SessionMemory] = None
    ) -> Orchestrator:
        """Create an orchestrator instance"""
        return Orchestrator(llm_manager, browser_config, storage_config, memory)


# Example usage
async def main():
    """Example usage of the orchestrator"""
    orchestrator = OrchestratorFactory.create_orchestrator()
    
    # Execute a task
    result = await orchestrator.execute("search laptops under ₹50,000 and list top 5 with price and link")
    
    print(f"Task ID: {result.task_id}")
    print(f"Status: {result.status}")
    print(f"Results: {len(result.results)}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    if result.results:
        for i, item in enumerate(result.results[:3], 1):
            print(f"{i}. {item.get('title', 'N/A')} - {item.get('price', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
