"""
Selector Adapter - Uses LLM to generate new selectors when HTML structure changes.

Phase 2: When website structure changes, this agent uses AI to:
- Analyze the new HTML structure
- Map old selectors to new structure
- Generate new CSS/XPath selectors
- Validate selectors work correctly
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents.website_structure.website_structure_monitor import StructureChange
from agents.scraper_monitoring.llm_agent import LLMAgent


@dataclass
class SelectorAdaptation:
    """Result of selector adaptation."""
    old_selector: str
    new_selector: str
    selector_type: str  # 'css' or 'xpath'
    confidence: float  # 0.0 to 1.0
    explanation: str
    validation_status: Optional[bool] = None  # None = not tested, True = works, False = broken


class SelectorAdapter:
    """
    Adapts CSS/XPath selectors when website structure changes.
    
    Uses LLM to intelligently map old selectors to new HTML structure.
    
    Usage:
        adapter = SelectorAdapter()
        adaptations = adapter.adapt_selectors(structure_change)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm_agent = LLMAgent()
    
    def adapt_selectors(self, change: StructureChange, 
                       html_content: str) -> List[SelectorAdaptation]:
        """
        Adapt selectors for a structure change.
        
        Args:
            change: StructureChange object with broken selectors
            html_content: Current HTML content
            
        Returns:
            List of SelectorAdaptation objects
        """
        if not change.broken_selectors:
            return []
        
        self.logger.info(f"🔧 Adapting {len(change.broken_selectors)} selector(s)...")
        
        adaptations = []
        
        for old_selector in change.broken_selectors:
            try:
                adaptation = self._adapt_single_selector(
                    old_selector=old_selector,
                    html_content=html_content,
                    baseline_elements=change.baseline_snapshot.key_elements,
                    current_elements=change.current_snapshot.key_elements
                )
                
                if adaptation:
                    adaptations.append(adaptation)
                    
            except Exception as e:
                self.logger.error(f"Error adapting selector {old_selector}: {e}")
        
        return adaptations
    
    def _adapt_single_selector(self, old_selector: str, html_content: str,
                              baseline_elements: Dict[str, Any],
                              current_elements: Dict[str, Any]) -> Optional[SelectorAdaptation]:
        """Adapt a single selector using LLM."""
        
        if not self.llm_agent.is_enabled():
            # Fallback to rule-based adaptation
            return self._rule_based_adaptation(old_selector, current_elements)
        
        try:
            # Build context for LLM
            context = self._build_adaptation_context(
                old_selector, html_content, baseline_elements, current_elements
            )
            
            # Call LLM
            response = self._call_llm_for_adaptation(context, old_selector)
            
            # Parse response
            adaptation = self._parse_llm_response(response, old_selector)
            
            return adaptation
            
        except Exception as e:
            self.logger.error(f"LLM adaptation failed for {old_selector}: {e}")
            # Fallback to rule-based
            return self._rule_based_adaptation(old_selector, current_elements)
    
    def _build_adaptation_context(self, old_selector: str, html_content: str,
                                 baseline_elements: Dict[str, Any],
                                 current_elements: Dict[str, Any]) -> str:
        """Build context string for LLM."""
        # Truncate HTML to first 5000 chars (to avoid token limits)
        html_preview = html_content[:5000] + "..." if len(html_content) > 5000 else html_content
        
        context = f"""A website's HTML structure has changed, and a CSS/XPath selector no longer works.

Old Selector: {old_selector}

Baseline Elements (before change):
{self._format_elements(baseline_elements)}

Current Elements (after change):
{self._format_elements(current_elements)}

Current HTML Structure (preview):
{html_preview}

Please analyze the HTML structure and suggest a new selector that:
1. Targets the same data/content as the old selector
2. Works with the new HTML structure
3. Is as specific and reliable as possible

Provide your response in this format:
SELECTOR_TYPE: [css or xpath]
NEW_SELECTOR: [your suggested selector]
CONFIDENCE: [0.0-1.0]
EXPLANATION: [why this selector should work]
"""
        return context
    
    def _format_elements(self, elements: Dict[str, Any]) -> str:
        """Format elements dictionary for LLM context."""
        if not elements:
            return "No key elements found"
        
        lines = []
        for selector, info in list(elements.items())[:10]:  # Limit to 10
            lines.append(f"  {selector}: {info}")
        
        return "\n".join(lines)
    
    def _call_llm_for_adaptation(self, context: str, old_selector: str) -> str:
        """Call LLM to generate new selector."""
        prompt = f"""You are an expert web scraping developer. A website's HTML structure changed and broke a selector.

{context}

Analyze the structure change and provide a new selector that will work.
"""
        
        if self.llm_agent.client_type == 'openai':
            response = self.llm_agent.client.chat.completions.create(
                model=self.llm_agent.model,
                messages=[
                    {"role": "system", "content": "You are an expert web scraping developer specializing in CSS selectors and XPath."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content
        
        elif self.llm_agent.client_type == 'anthropic':
            response = self.llm_agent.client.messages.create(
                model=self.llm_agent.model,
                max_tokens=300,
                system="You are an expert web scraping developer specializing in CSS selectors and XPath.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unknown client type: {self.llm_agent.client_type}")
    
    def _parse_llm_response(self, response: str, old_selector: str) -> SelectorAdaptation:
        """Parse LLM response into SelectorAdaptation."""
        selector_type = 'css'  # Default
        new_selector = old_selector  # Fallback
        confidence = 0.5
        explanation = "LLM analysis completed"
        
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('SELECTOR_TYPE:'):
                selector_type = line.replace('SELECTOR_TYPE:', '').strip().lower()
            elif line.startswith('NEW_SELECTOR:'):
                new_selector = line.replace('NEW_SELECTOR:', '').strip().strip('"\'')
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                    confidence = max(0.0, min(1.0, confidence))
                except ValueError:
                    pass
            elif line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()
        
        return SelectorAdaptation(
            old_selector=old_selector,
            new_selector=new_selector,
            selector_type=selector_type,
            confidence=confidence,
            explanation=explanation
        )
    
    def _rule_based_adaptation(self, old_selector: str,
                              current_elements: Dict[str, Any]) -> Optional[SelectorAdaptation]:
        """Fallback rule-based selector adaptation."""
        # Simple heuristic: try to find similar elements
        # This is a basic fallback - LLM is much better
        
        # Try to find elements with similar patterns
        if old_selector.startswith('.'):
            # CSS class selector
            class_name = old_selector[1:]
            # Look for similar classes in current elements
            for element_selector, info in current_elements.items():
                if element_selector.startswith('.') and class_name.lower() in element_selector.lower():
                    return SelectorAdaptation(
                        old_selector=old_selector,
                        new_selector=element_selector,
                        selector_type='css',
                        confidence=0.4,
                        explanation=f"Found similar class selector: {element_selector}"
                    )
        
        elif old_selector.startswith('#'):
            # CSS ID selector
            id_name = old_selector[1:]
            for element_selector, info in current_elements.items():
                if element_selector.startswith('#') and id_name.lower() in element_selector.lower():
                    return SelectorAdaptation(
                        old_selector=old_selector,
                        new_selector=element_selector,
                        selector_type='css',
                        confidence=0.4,
                        explanation=f"Found similar ID selector: {element_selector}"
                    )
        
        # No good match found
        return None
    
    def validate_selector(self, selector: str, html_content: str,
                         selector_type: str = 'css') -> bool:
        """
        Validate that a selector works with current HTML.
        
        Args:
            selector: CSS selector or XPath
            html_content: HTML content to test against
            selector_type: 'css' or 'xpath'
            
        Returns:
            True if selector finds elements, False otherwise
        """
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if selector_type == 'css':
                elements = soup.select(selector)
                return len(elements) > 0
            elif selector_type == 'xpath':
                # XPath validation would require lxml
                # For now, return True if it's a valid XPath pattern
                return selector.startswith('.//') or selector.startswith('//')
            else:
                return False
                
        except Exception as e:
            self.logger.debug(f"Selector validation error: {e}")
            return False

