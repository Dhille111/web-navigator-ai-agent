"""
Planner for converting parsed instructions into executable steps
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .parser import ParsedInstruction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Represents a single execution step"""
    action: str  # goto, click, fill, extract, wait, screenshot
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timeout: int = 10
    multiple: bool = False
    retries: int = 3
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StepPlanner:
    """Planner for converting parsed instructions to executable steps"""
    
    def __init__(self):
        self.step_templates = self._load_step_templates()
    
    def _load_step_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load step templates for different task types"""
        return {
            'search': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 2},
                {'action': 'fill', 'timeout': 10},
                {'action': 'click', 'timeout': 10},
                {'action': 'wait', 'timeout': 5},
                {'action': 'extract', 'timeout': 10, 'multiple': True}
            ],
            'navigate': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 3}
            ],
            'extract': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 3},
                {'action': 'extract', 'timeout': 10, 'multiple': True}
            ],
            'fill_form': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 2},
                {'action': 'fill', 'timeout': 10},
                {'action': 'click', 'timeout': 10}
            ],
            'click': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 2},
                {'action': 'click', 'timeout': 10}
            ],
            'screenshot': [
                {'action': 'goto', 'timeout': 15},
                {'action': 'wait', 'timeout': 3},
                {'action': 'screenshot', 'timeout': 5}
            ]
        }
    
    def plan(self, parsed_instruction: ParsedInstruction) -> List[Step]:
        """Convert parsed instruction to executable steps"""
        try:
            steps = []
            
            # Add initial steps based on task type
            if parsed_instruction.actions:
                # Use actions from parsed instruction
                steps = self._convert_actions_to_steps(parsed_instruction.actions)
            else:
                # Generate steps from template
                steps = self._generate_steps_from_template(parsed_instruction)
            
            # Enhance steps with specific selectors and values
            steps = self._enhance_steps(steps, parsed_instruction)
            
            # Add error handling and retry logic
            steps = self._add_error_handling(steps)
            
            logger.info(f"Generated {len(steps)} steps for task: {parsed_instruction.task}")
            return steps
            
        except Exception as e:
            logger.error(f"Failed to plan steps: {e}")
            return self._create_fallback_steps(parsed_instruction)
    
    def _convert_actions_to_steps(self, actions: List[Dict[str, Any]]) -> List[Step]:
        """Convert action dictionaries to Step objects"""
        steps = []
        
        for action in actions:
            step = Step(
                action=action.get('action', 'goto'),
                selector=action.get('selector'),
                value=action.get('value'),
                url=action.get('url'),
                timeout=action.get('timeout', 10),
                multiple=action.get('multiple', False),
                retries=action.get('retries', 3),
                metadata=action.get('metadata', {})
            )
            steps.append(step)
        
        return steps
    
    def _generate_steps_from_template(self, parsed_instruction: ParsedInstruction) -> List[Step]:
        """Generate steps from template based on task type"""
        template = self.step_templates.get(parsed_instruction.task, self.step_templates['search'])
        steps = []
        
        for template_step in template:
            step = Step(
                action=template_step['action'],
                timeout=template_step.get('timeout', 10),
                multiple=template_step.get('multiple', False),
                retries=template_step.get('retries', 3)
            )
            steps.append(step)
        
        return steps
    
    def _enhance_steps(self, steps: List[Step], parsed_instruction: ParsedInstruction) -> List[Step]:
        """Enhance steps with specific selectors and values"""
        enhanced_steps = []
        
        for i, step in enumerate(steps):
            # Set URL for goto actions
            if step.action == 'goto' and not step.url:
                step.url = parsed_instruction.target_url
            
            # Set selector and value for fill actions
            if step.action == 'fill':
                step.selector = self._get_selector(parsed_instruction, 'search_box')
                step.value = parsed_instruction.query
            
            # Set selector for click actions
            if step.action == 'click':
                step.selector = self._get_selector(parsed_instruction, 'search_button')
            
            # Set selector for extract actions
            if step.action == 'extract':
                step.selector = self._get_selector(parsed_instruction, 'results')
                step.multiple = True
            
            # Add metadata
            step.metadata.update({
                'task': parsed_instruction.task,
                'query': parsed_instruction.query,
                'step_number': i + 1
            })
            
            enhanced_steps.append(step)
        
        return enhanced_steps
    
    def _get_selector(self, parsed_instruction: ParsedInstruction, selector_type: str) -> str:
        """Get selector for specific element type"""
        selectors = parsed_instruction.selectors
        
        if selector_type in selectors:
            return selectors[selector_type]
        
        # Fallback selectors
        fallback_selectors = {
            'search_box': 'input[name="q"], input[type="search"], input[placeholder*="search"]',
            'search_button': 'button[type="submit"], input[type="submit"], .search-button',
            'results': '.result, .search-result, .product-item, .item',
            'title': 'h1, h2, h3, .title, .name',
            'price': '.price, .cost, [class*="price"]',
            'link': 'a, .link'
        }
        
        return fallback_selectors.get(selector_type, 'body')
    
    def _add_error_handling(self, steps: List[Step]) -> List[Step]:
        """Add error handling and retry logic to steps"""
        enhanced_steps = []
        
        for step in steps:
            # Add retry logic for critical actions
            if step.action in ['click', 'fill', 'extract']:
                step.retries = max(step.retries, 3)
            
            # Add timeout for navigation actions
            if step.action == 'goto':
                step.timeout = max(step.timeout, 15)
            
            # Add wait steps after critical actions
            if step.action in ['click', 'fill']:
                enhanced_steps.append(step)
                # Add wait step
                wait_step = Step(
                    action='wait',
                    timeout=2,
                    metadata={'purpose': 'wait_after_action'}
                )
                enhanced_steps.append(wait_step)
            else:
                enhanced_steps.append(step)
        
        return enhanced_steps
    
    def _create_fallback_steps(self, parsed_instruction: ParsedInstruction) -> List[Step]:
        """Create fallback steps when planning fails"""
        logger.warning(f"Using fallback steps for task: {parsed_instruction.task}")
        
        fallback_steps = [
            Step(
                action='goto',
                url=parsed_instruction.target_url or 'https://www.google.com',
                timeout=15,
                metadata={'fallback': True}
            ),
            Step(
                action='wait',
                timeout=3,
                metadata={'fallback': True}
            )
        ]
        
        if parsed_instruction.task == 'search':
            fallback_steps.extend([
                Step(
                    action='fill',
                    selector='input[name="q"]',
                    value=parsed_instruction.query,
                    timeout=10,
                    metadata={'fallback': True}
                ),
                Step(
                    action='click',
                    selector='button[type="submit"]',
                    timeout=10,
                    metadata={'fallback': True}
                ),
                Step(
                    action='wait',
                    timeout=5,
                    metadata={'fallback': True}
                ),
                Step(
                    action='extract',
                    selector='body',
                    multiple=True,
                    timeout=10,
                    metadata={'fallback': True}
                )
            ])
        
        return fallback_steps


class StepPlannerFactory:
    """Factory for creating step planners"""
    
    @staticmethod
    def create_planner() -> StepPlanner:
        """Create a step planner"""
        return StepPlanner()


# Example usage
if __name__ == "__main__":
    from .parser import ParsedInstruction
    
    # Create a test parsed instruction
    test_instruction = ParsedInstruction(
        task='search',
        query='laptops under 50000',
        filters={'price_max': 50000},
        count=5,
        fields=['title', 'price', 'url'],
        target_url='https://www.amazon.in',
        selectors={
            'search_box': 'input[name="field-keywords"]',
            'search_button': 'input[type="submit"]',
            'results': '[data-component-type="s-search-result"]'
        },
        actions=[],
        raw_instruction='search laptops under ₹50,000'
    )
    
    # Test planning
    planner = StepPlannerFactory.create_planner()
    steps = planner.plan(test_instruction)
    
    print(f"Generated {len(steps)} steps:")
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step.action} - {step.selector or step.url} - {step.value or ''}")
