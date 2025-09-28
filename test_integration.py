"""
Integration tests for the Local AI Agent
"""

import pytest
import asyncio
import tempfile
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig, ActionResult
from src.agent.llm_adapter import LLMManager, LLMResponse
from src.utils.storage import ExportConfig
from src.memory.session_memory import MemoryFactory


class TestIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock LLM manager
        self.mock_llm_manager = Mock(spec=LLMManager)
        self.mock_llm_manager.is_available.return_value = True
        
        # Configure components
        self.browser_config = BrowserConfig(
            headless=True,
            browser_type="chromium"
        )
        
        self.storage_config = ExportConfig(
            output_dir=os.path.join(self.temp_dir, "exports"),
            json_format=True,
            csv_format=True
        )
        
        self.memory = MemoryFactory.create_memory(
            persist_to_disk=False,
            memory_file=os.path.join(self.temp_dir, "memory.json")
        )
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_search_task_execution(self):
        """Test executing a search task"""
        # Mock LLM response for parsing
        mock_parse_response = LLMResponse(
            content='{"task": "search", "query": "laptops under 50000", "filters": {"price_max": 50000}, "count": 5, "fields": ["title", "price", "url"], "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_parse_response
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            llm_manager=self.mock_llm_manager,
            browser_config=self.browser_config,
            storage_config=self.storage_config,
            memory=self.memory
        )
        
        # Mock browser controller
        with patch('src.agent.orchestrator.BrowserController') as mock_browser_class:
            mock_browser = AsyncMock()
            mock_browser_class.return_value.__aenter__.return_value = mock_browser
            
            # Mock browser actions
            mock_browser.goto.return_value = ActionResult(success=True, data={'url': 'https://example.com'})
            mock_browser.fill.return_value = ActionResult(success=True, data={'selector': 'input', 'value': 'laptops'})
            mock_browser.safe_click.return_value = ActionResult(success=True, data={'selector': 'button'})
            mock_browser.safe_extract.return_value = ActionResult(
                success=True,
                data=[
                    {
                        'text': 'Laptop Model 1',
                        'attributes': {'href': 'https://example.com/1'},
                        'html': '<div>Laptop Model 1 - ₹45,000</div>'
                    },
                    {
                        'text': 'Laptop Model 2',
                        'attributes': {'href': 'https://example.com/2'},
                        'html': '<div>Laptop Model 2 - ₹42,000</div>'
                    }
                ]
            )
            
            # Execute task
            result = await orchestrator.execute("search laptops under ₹50,000 and list top 5 with price and link")
            
            # Assertions
            assert result.task_id is not None
            assert result.status in ["success", "error"]
            assert result.instruction == "search laptops under ₹50,000 and list top 5 with price and link"
            assert isinstance(result.results, list)
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_navigate_task_execution(self):
        """Test executing a navigate task"""
        # Mock LLM response for parsing
        mock_parse_response = LLMResponse(
            content='{"task": "navigate", "query": "go to example.com", "target_url": "https://example.com", "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_parse_response
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            llm_manager=self.mock_llm_manager,
            browser_config=self.browser_config,
            storage_config=self.storage_config,
            memory=self.memory
        )
        
        # Mock browser controller
        with patch('src.agent.orchestrator.BrowserController') as mock_browser_class:
            mock_browser = AsyncMock()
            mock_browser_class.return_value.__aenter__.return_value = mock_browser
            
            # Mock browser actions
            mock_browser.goto.return_value = ActionResult(success=True, data={'url': 'https://example.com'})
            mock_browser.wait.return_value = ActionResult(success=True, data={'wait_time': 3})
            
            # Execute task
            result = await orchestrator.execute("navigate to https://example.com")
            
            # Assertions
            assert result.task_id is not None
            assert result.status in ["success", "error"]
            assert result.instruction == "navigate to https://example.com"
            assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_extract_task_execution(self):
        """Test executing an extract task"""
        # Mock LLM response for parsing
        mock_parse_response = LLMResponse(
            content='{"task": "extract", "query": "extract product information", "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_parse_response
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            llm_manager=self.mock_llm_manager,
            browser_config=self.browser_config,
            storage_config=self.storage_config,
            memory=self.memory
        )
        
        # Mock browser controller
        with patch('src.agent.orchestrator.BrowserController') as mock_browser_class:
            mock_browser = AsyncMock()
            mock_browser_class.return_value.__aenter__.return_value = mock_browser
            
            # Mock browser actions
            mock_browser.goto.return_value = ActionResult(success=True, data={'url': 'https://example.com'})
            mock_browser.safe_extract.return_value = ActionResult(
                success=True,
                data=[
                    {
                        'text': 'Product 1 - ₹1000',
                        'attributes': {'href': 'https://example.com/product1'},
                        'html': '<div>Product 1 - ₹1000</div>'
                    }
                ]
            )
            
            # Execute task
            result = await orchestrator.execute("extract all product information from the current page")
            
            # Assertions
            assert result.task_id is not None
            assert result.status in ["success", "error"]
            assert result.instruction == "extract all product information from the current page"
            assert result.execution_time > 0
    
    def test_memory_persistence(self):
        """Test memory persistence functionality"""
        # Add some test memories
        memory_id1 = self.memory.add_memory(
            instruction="search laptops",
            result={"count": 5, "items": ["laptop1", "laptop2"]},
            success=True,
            task_type="search"
        )
        
        memory_id2 = self.memory.add_memory(
            instruction="navigate to example.com",
            result={"url": "https://example.com", "status": "success"},
            success=True,
            task_type="navigate"
        )
        
        # Test getting recent memories
        recent = self.memory.get_recent_memories(5)
        assert len(recent) == 2
        assert recent[0].instruction == "navigate to example.com"  # Most recent first
        
        # Test getting memories by type
        search_memories = self.memory.get_memories_by_type("search")
        assert len(search_memories) == 1
        assert search_memories[0].instruction == "search laptops"
        
        # Test finding similar memories
        similar = self.memory.find_similar_memories("search for laptops", limit=3)
        assert len(similar) >= 1
        assert similar[0].instruction == "search laptops"
        
        # Test session stats
        stats = self.memory.get_session_stats()
        assert stats['total_tasks'] == 2
        assert stats['successful_tasks'] == 2
        assert stats['failed_tasks'] == 0
        assert stats['success_rate'] == 1.0
    
    def test_storage_functionality(self):
        """Test storage functionality"""
        from src.utils.storage import DataStorage, TaskResult
        from datetime import datetime
        
        # Create storage instance
        storage = DataStorage(self.storage_config)
        
        # Create test task result
        task_result = TaskResult(
            task_id="test_001",
            status="success",
            instruction="test instruction",
            results=[
                {"title": "Item 1", "price": "₹1000", "url": "https://example.com/1"},
                {"title": "Item 2", "price": "₹2000", "url": "https://example.com/2"}
            ],
            metadata={"browser": "chromium"},
            timestamp=datetime.now(),
            execution_time=15.5
        )
        
        # Save task result
        saved_files = storage.save_task_result(task_result)
        assert 'json' in saved_files
        assert 'csv' in saved_files
        
        # Load task result
        loaded_result = storage.load_task_result("test_001")
        assert loaded_result is not None
        assert loaded_result.task_id == "test_001"
        assert loaded_result.status == "success"
        assert len(loaded_result.results) == 2
        
        # List task results
        history = storage.list_task_results()
        assert len(history) == 1
        assert history[0]['task_id'] == "test_001"
    
    def test_error_handling(self):
        """Test error handling in orchestrator"""
        # Mock LLM to raise exception
        self.mock_llm_manager.generate.side_effect = Exception("LLM failed")
        
        # Create orchestrator
        orchestrator = OrchestratorFactory.create_orchestrator(
            llm_manager=self.mock_llm_manager,
            browser_config=self.browser_config,
            storage_config=self.storage_config,
            memory=self.memory
        )
        
        # Execute task that should fail
        result = asyncio.run(orchestrator.execute("test instruction"))
        
        # Assertions
        assert result.status == "error"
        assert result.error_message is not None
        assert result.results == []
        assert result.execution_time > 0


if __name__ == "__main__":
    pytest.main([__file__])
