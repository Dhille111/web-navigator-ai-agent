"""
Instruction Parser for converting natural language to structured plans
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .llm_adapter import LLMManager, create_default_llm_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ParsedInstruction:
    """Structured representation of a parsed instruction"""
    task: str
    query: str
    filters: Dict[str, Any]
    count: int
    fields: List[str]
    target_url: Optional[str]
    selectors: Dict[str, str]
    actions: List[Dict[str, Any]]
    raw_instruction: str


class InstructionParser:
    """Parser for converting natural language instructions to structured plans"""
    
    def __init__(self, llm_manager: Optional[LLMManager] = None):
        self.llm_manager = llm_manager or create_default_llm_manager()
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """Load the prompt template for instruction parsing"""
        try:
            with open('src/prompts/instruction_parser.txt', 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
        except FileNotFoundError:
            # Fallback template if file not found
            self.prompt_template = self._get_fallback_template()
            logger.warning("Using fallback prompt template")
    
    def _get_fallback_template(self) -> str:
        """Fallback prompt template"""
        return """
You are an AI agent that parses natural language instructions into structured JSON plans for web automation tasks.

Convert the user's instruction into a JSON object with this structure:
{
  "task": "search|navigate|extract|fill_form|click|screenshot",
  "query": "description of what to do",
  "filters": {"price_max": 50000, "sort": "rating"},
  "count": 5,
  "fields": ["title", "price", "url"],
  "target_url": "https://example.com",
  "selectors": {"search_box": "input[name='q']", "results": ".product-item"},
  "actions": [
    {"action": "goto", "url": "https://example.com"},
    {"action": "fill", "selector": "input[name='q']", "value": "search query"},
    {"action": "click", "selector": "button[type='submit']"},
    {"action": "extract", "selector": ".product-item", "multiple": true}
  ]
}

Return only valid JSON, no additional text.
        """.strip()
    
    def parse(self, instruction: str) -> ParsedInstruction:
        """Parse a natural language instruction into a structured plan"""
        try:
            # Use LLM to parse the instruction
            full_prompt = f"{self.prompt_template}\n\nInstruction: {instruction}"
            response = self.llm_manager.generate(full_prompt)
            
            # Extract JSON from response
            json_str = self._extract_json(response.content)
            plan_data = json.loads(json_str)
            
            # Create structured instruction
            parsed = ParsedInstruction(
                task=plan_data.get('task', 'search'),
                query=plan_data.get('query', instruction),
                filters=plan_data.get('filters', {}),
                count=plan_data.get('count', 5),
                fields=plan_data.get('fields', ['title', 'url']),
                target_url=plan_data.get('target_url'),
                selectors=plan_data.get('selectors', {}),
                actions=plan_data.get('actions', []),
                raw_instruction=instruction
            )
            
            # Validate and enhance the parsed instruction
            parsed = self._validate_and_enhance(parsed)
            
            logger.info(f"Parsed instruction: {parsed.task} - {parsed.query}")
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse instruction: {e}")
            # Return a fallback parsed instruction
            return self._create_fallback_instruction(instruction)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # If no JSON found, try to extract from code blocks
        code_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        # If still no JSON, return the whole text (might be malformed)
        return text
    
    def _validate_and_enhance(self, parsed: ParsedInstruction) -> ParsedInstruction:
        """Validate and enhance the parsed instruction"""
        # Ensure required fields
        if not parsed.task:
            parsed.task = 'search'
        
        if not parsed.query:
            parsed.query = parsed.raw_instruction
        
        # Add default selectors if missing
        if not parsed.selectors:
            parsed.selectors = self._get_default_selectors(parsed.task)
        
        # Add default actions if missing
        if not parsed.actions:
            parsed.actions = self._get_default_actions(parsed)
        
        # Ensure target URL is set
        if not parsed.target_url:
            parsed.target_url = self._get_default_url(parsed.task)
        
        return parsed
    
    def _get_default_selectors(self, task: str) -> Dict[str, str]:
        """Get default selectors for common tasks"""
        selectors = {
            'search': {
                'search_box': 'input[name="q"], input[name="search"], input[type="search"]',
                'search_button': 'button[type="submit"], input[type="submit"], .search-button',
                'results': '.result, .search-result, .product-item, .item',
                'title': 'h1, h2, h3, .title, .name',
                'price': '.price, .cost, [class*="price"]',
                'link': 'a, .link'
            },
            'navigate': {
                'page_content': 'body, main, .content',
                'navigation': 'nav, .nav, .menu'
            },
            'extract': {
                'content': 'body, main, .content, .article',
                'title': 'h1, .title, .headline',
                'text': 'p, .text, .description'
            }
        }
        
        return selectors.get(task, selectors['search'])
    
    def _get_default_actions(self, parsed: ParsedInstruction) -> List[Dict[str, Any]]:
        """Get default actions based on task type"""
        actions = []
        
        if parsed.task == 'search':
            actions = [
                {'action': 'goto', 'url': parsed.target_url},
                {'action': 'fill', 'selector': 'input[name="q"]', 'value': parsed.query},
                {'action': 'click', 'selector': 'button[type="submit"]'},
                {'action': 'wait', 'timeout': 3},
                {'action': 'extract', 'selector': '.result', 'multiple': True}
            ]
        elif parsed.task == 'navigate':
            actions = [
                {'action': 'goto', 'url': parsed.target_url},
                {'action': 'wait', 'timeout': 2}
            ]
        elif parsed.task == 'extract':
            actions = [
                {'action': 'goto', 'url': parsed.target_url},
                {'action': 'wait', 'timeout': 2},
                {'action': 'extract', 'selector': 'body', 'multiple': False}
            ]
        
        return actions
    
    def _get_default_url(self, task: str) -> str:
        """Get default URL for task type"""
        urls = {
            'search': 'https://www.google.com',
            'navigate': 'https://www.example.com',
            'extract': 'https://www.example.com',
            'fill_form': 'https://www.example.com/contact',
            'click': 'https://www.example.com',
            'screenshot': 'https://www.example.com'
        }
        return urls.get(task, 'https://www.google.com')
    
    def _create_fallback_instruction(self, instruction: str) -> ParsedInstruction:
        """Create a fallback instruction when parsing fails"""
        logger.warning(f"Using fallback parser for instruction: {instruction}")
        
        # Simple keyword-based parsing
        instruction_lower = instruction.lower()
        
        if 'search' in instruction_lower:
            task = 'search'
            query = instruction
        elif 'navigate' in instruction_lower or 'go to' in instruction_lower:
            task = 'navigate'
            query = instruction
        elif 'extract' in instruction_lower or 'get' in instruction_lower:
            task = 'extract'
            query = instruction
        elif 'fill' in instruction_lower or 'form' in instruction_lower:
            task = 'fill_form'
            query = instruction
        else:
            task = 'search'
            query = instruction
        
        return ParsedInstruction(
            task=task,
            query=query,
            filters={},
            count=5,
            fields=['title', 'url'],
            target_url=self._get_default_url(task),
            selectors=self._get_default_selectors(task),
            actions=self._get_default_actions(ParsedInstruction(
                task=task, query=query, filters={}, count=5, fields=['title', 'url'],
                target_url=None, selectors={}, actions=[], raw_instruction=instruction
            )),
            raw_instruction=instruction
        )


class InstructionParserFactory:
    """Factory for creating instruction parsers"""
    
    @staticmethod
    def create_parser(llm_manager: Optional[LLMManager] = None) -> InstructionParser:
        """Create an instruction parser"""
        return InstructionParser(llm_manager)


# Example usage
if __name__ == "__main__":
    parser = InstructionParserFactory.create_parser()
    
    # Test parsing
    test_instructions = [
        "search laptops under ₹50,000 and list top 5 with price and link",
        "navigate to https://example.com and take a screenshot",
        "extract all product information from the current page"
    ]
    
    for instruction in test_instructions:
        try:
            parsed = parser.parse(instruction)
            print(f"Instruction: {instruction}")
            print(f"Parsed: {parsed.task} - {parsed.query}")
            print(f"Actions: {len(parsed.actions)}")
            print("---")
        except Exception as e:
            print(f"Error parsing '{instruction}': {e}")
