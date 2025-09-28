"""
Unit tests for instruction parser
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agent.parser import InstructionParser, ParsedInstruction
from src.agent.llm_adapter import LLMManager, LLMResponse


class TestInstructionParser:
    """Test cases for instruction parser"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Mock LLM manager
        self.mock_llm_manager = Mock(spec=LLMManager)
        self.parser = InstructionParser(self.mock_llm_manager)
    
    def test_parse_search_instruction(self):
        """Test parsing a search instruction"""
        # Mock LLM response
        mock_response = LLMResponse(
            content='{"task": "search", "query": "laptops under 50000", "filters": {"price_max": 50000}, "count": 5, "fields": ["title", "price", "url"], "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_response
        
        # Test parsing
        result = self.parser.parse("search laptops under ₹50,000 and list top 5 with price and link")
        
        # Assertions
        assert result.task == "search"
        assert result.query == "laptops under 50000"
        assert result.filters["price_max"] == 50000
        assert result.count == 5
        assert "title" in result.fields
        assert "price" in result.fields
        assert "url" in result.fields
    
    def test_parse_navigate_instruction(self):
        """Test parsing a navigate instruction"""
        # Mock LLM response
        mock_response = LLMResponse(
            content='{"task": "navigate", "query": "go to example.com", "target_url": "https://example.com", "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_response
        
        # Test parsing
        result = self.parser.parse("navigate to https://example.com")
        
        # Assertions
        assert result.task == "navigate"
        assert result.query == "go to example.com"
        assert result.target_url == "https://example.com"
    
    def test_parse_extract_instruction(self):
        """Test parsing an extract instruction"""
        # Mock LLM response
        mock_response = LLMResponse(
            content='{"task": "extract", "query": "extract product information", "actions": []}',
            model="test-model"
        )
        self.mock_llm_manager.generate.return_value = mock_response
        
        # Test parsing
        result = self.parser.parse("extract all product information from the current page")
        
        # Assertions
        assert result.task == "extract"
        assert result.query == "extract product information"
    
    def test_parse_with_fallback(self):
        """Test parsing with fallback when LLM fails"""
        # Mock LLM to raise exception
        self.mock_llm_manager.generate.side_effect = Exception("LLM failed")
        
        # Test parsing
        result = self.parser.parse("search for laptops")
        
        # Assertions - should use fallback
        assert result.task == "search"  # Fallback should detect "search"
        assert result.query == "search for laptops"
        assert result.raw_instruction == "search for laptops"
    
    def test_extract_json_from_response(self):
        """Test JSON extraction from LLM response"""
        # Test with valid JSON
        json_str = '{"task": "search", "query": "test"}'
        result = self.parser._extract_json(json_str)
        assert result == json_str
        
        # Test with JSON in code block
        code_block = '```json\n{"task": "search", "query": "test"}\n```'
        result = self.parser._extract_json(code_block)
        assert result == '{"task": "search", "query": "test"}'
        
        # Test with mixed content
        mixed_content = 'Here is the JSON:\n{"task": "search", "query": "test"}\nThat\'s it.'
        result = self.parser._extract_json(mixed_content)
        assert result == '{"task": "search", "query": "test"}'
    
    def test_validate_and_enhance(self):
        """Test validation and enhancement of parsed instruction"""
        # Create a minimal parsed instruction
        parsed = ParsedInstruction(
            task="search",
            query="test query",
            filters={},
            count=5,
            fields=["title", "url"],
            target_url=None,
            selectors={},
            actions=[],
            raw_instruction="test instruction"
        )
        
        # Test enhancement
        enhanced = self.parser._validate_and_enhance(parsed)
        
        # Assertions
        assert enhanced.task == "search"
        assert enhanced.query == "test query"
        assert enhanced.selectors  # Should have default selectors
        assert enhanced.actions  # Should have default actions
        assert enhanced.target_url  # Should have default URL
    
    def test_get_default_selectors(self):
        """Test getting default selectors for different task types"""
        # Test search selectors
        search_selectors = self.parser._get_default_selectors("search")
        assert "search_box" in search_selectors
        assert "search_button" in search_selectors
        assert "results" in search_selectors
        
        # Test navigate selectors
        navigate_selectors = self.parser._get_default_selectors("navigate")
        assert "page_content" in navigate_selectors
        
        # Test extract selectors
        extract_selectors = self.parser._get_default_selectors("extract")
        assert "content" in extract_selectors
    
    def test_get_default_actions(self):
        """Test getting default actions for different task types"""
        # Create a test parsed instruction
        parsed = ParsedInstruction(
            task="search",
            query="test query",
            filters={},
            count=5,
            fields=["title", "url"],
            target_url="https://example.com",
            selectors={},
            actions=[],
            raw_instruction="test instruction"
        )
        
        # Test search actions
        actions = self.parser._get_default_actions(parsed)
        assert len(actions) > 0
        assert any(action["action"] == "goto" for action in actions)
        assert any(action["action"] == "fill" for action in actions)
        assert any(action["action"] == "click" for action in actions)
        assert any(action["action"] == "extract" for action in actions)
    
    def test_create_fallback_instruction(self):
        """Test creating fallback instruction when parsing fails"""
        # Test with search instruction
        result = self.parser._create_fallback_instruction("search laptops under 50000")
        assert result.task == "search"
        assert result.query == "search laptops under 50000"
        assert result.raw_instruction == "search laptops under 50000"
        
        # Test with navigate instruction
        result = self.parser._create_fallback_instruction("navigate to example.com")
        assert result.task == "navigate"
        assert result.query == "navigate to example.com"
        
        # Test with extract instruction
        result = self.parser._create_fallback_instruction("extract product data")
        assert result.task == "extract"
        assert result.query == "extract product data"
        
        # Test with unknown instruction
        result = self.parser._create_fallback_instruction("unknown instruction")
        assert result.task == "search"  # Default fallback
        assert result.query == "unknown instruction"


if __name__ == "__main__":
    pytest.main([__file__])
