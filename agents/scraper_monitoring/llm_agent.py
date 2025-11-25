"""
LLM Agent - Uses AI to analyze errors and suggest intelligent fixes.

This is optional - the system works without it, but it adds intelligence
for understanding context and generating code fixes.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, skip

from agents.scraper_monitoring.pattern_analyzer import FailurePattern
from agents.scraper_monitoring.scraper_monitor import ScraperExecution


@dataclass
class LLMAnalysis:
    """Result of LLM analysis."""
    root_cause: str
    confidence: float  # 0.0 to 1.0
    suggested_fix: str
    code_changes: Optional[str] = None  # Suggested code changes
    explanation: str = ""  # Human-readable explanation


class LLMAgent:
    """
    Uses Large Language Models (GPT-4/Claude) to analyze errors intelligently.
    
    This agent:
    - Understands error context
    - Suggests intelligent fixes
    - Can generate code changes
    - Explains its reasoning
    
    This is OPTIONAL - set ENABLE_LLM_AGENT=false to disable.
    Without LLM, the system uses rule-based suggestions.
    
    Usage:
        agent = LLMAgent()
        if agent.is_enabled():
            analysis = agent.analyze_error(failure_pattern)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM agent.
        
        Args:
            api_key: API key (or set OPENAI_API_KEY or ANTHROPIC_API_KEY env var)
            model: Model to use ('gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku')
                   If None, auto-detects based on available API key
        """
        self.logger = logging.getLogger(__name__)
        
        # Check if LLM agent is enabled
        self.enabled = os.getenv('ENABLE_LLM_AGENT', 'true').lower() == 'true'
        
        if not self.enabled:
            self.logger.info("LLM Agent is disabled (set ENABLE_LLM_AGENT=true to enable)")
            return
        
        # Get API key - prefer Anthropic if both are available
        anthropic_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        openai_key = api_key or os.getenv('OPENAI_API_KEY')
        
        # Auto-detect which API to use
        if anthropic_key and not openai_key:
            # Only Anthropic available
            self.api_key = anthropic_key
            self.model = model or "claude-3-sonnet-20240229"  # Good default for Anthropic
            self.client_type = 'anthropic'
        elif openai_key and not anthropic_key:
            # Only OpenAI available
            self.api_key = openai_key
            self.model = model or "gpt-4"
            self.client_type = 'openai'
        elif anthropic_key and openai_key:
            # Both available - prefer Anthropic if model not specified
            if model and 'gpt' in model.lower():
                self.api_key = openai_key
                self.model = model
                self.client_type = 'openai'
            elif model and 'claude' in model.lower():
                self.api_key = anthropic_key
                self.model = model
                self.client_type = 'anthropic'
            else:
                # Default to Anthropic if both available
                self.api_key = anthropic_key
                self.model = model or "claude-3-sonnet-20240229"
                self.client_type = 'anthropic'
                self.logger.info("Both API keys found - using Anthropic (Claude)")
        else:
            # No API key found
            self.logger.warning(
                "LLM Agent enabled but no API key found. "
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable. "
                "Disabling LLM agent - will use rule-based suggestions instead."
            )
            self.enabled = False
            return
        
        # Initialize API client
        self._init_client()
    
    def _init_client(self):
        """Initialize the LLM API client."""
        try:
            if self.client_type == 'openai':
                try:
                    import openai
                    self.client = openai.OpenAI(api_key=self.api_key)
                    self.logger.info(f"✅ LLM Agent initialized with OpenAI ({self.model})")
                except ImportError:
                    self.logger.warning("openai package not installed. Install with: pip install openai")
                    self.enabled = False
            elif self.client_type == 'anthropic':
                try:
                    import anthropic
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                    self.logger.info(f"✅ LLM Agent initialized with Anthropic ({self.model})")
                except ImportError:
                    self.logger.warning("anthropic package not installed. Install with: pip install anthropic")
                    self.enabled = False
            else:
                self.logger.warning(f"Unknown client type: {self.client_type}. Disabling LLM agent.")
                self.enabled = False
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if LLM agent is enabled and ready."""
        return self.enabled and hasattr(self, 'client')
    
    def analyze_error(self, pattern: FailurePattern, 
                     recent_executions: Optional[List[ScraperExecution]] = None) -> LLMAnalysis:
        """
        Use LLM to analyze an error pattern and suggest fixes.
        
        Args:
            pattern: FailurePattern to analyze
            recent_executions: Recent execution history for context
            
        Returns:
            LLMAnalysis with root cause, fix suggestion, and explanation
        """
        if not self.is_enabled():
            # Fallback to rule-based analysis
            return self._rule_based_analysis(pattern)
        
        try:
            self.logger.info(f"🤖 Analyzing error pattern with LLM: {pattern.pattern_type}")
            
            # Build context for LLM
            context = self._build_context(pattern, recent_executions)
            
            # Call LLM
            response = self._call_llm(context)
            
            # Parse response
            analysis = self._parse_llm_response(response, pattern)
            
            self.logger.info(f"✅ LLM analysis complete (confidence: {analysis.confidence:.2f})")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            # Fallback to rule-based
            return self._rule_based_analysis(pattern)
    
    def _build_context(self, pattern: FailurePattern,
                      recent_executions: Optional[List[ScraperExecution]]) -> str:
        """Build context string for LLM."""
        context_parts = [
            f"Scraper: {pattern.scraper_name}",
            f"Error Type: {pattern.error_type}",
            f"Error Message: {pattern.error_message}",
            f"Pattern Type: {pattern.pattern_type}",
            f"Frequency: {pattern.frequency} occurrences",
            f"First Seen: {pattern.first_seen.isoformat()}",
            f"Last Seen: {pattern.last_seen.isoformat()}",
        ]
        
        if recent_executions:
            context_parts.append("\nRecent Execution History:")
            for ex in recent_executions[:5]:  # Last 5 executions
                context_parts.append(
                    f"  - {ex.timestamp.isoformat()}: "
                    f"{'SUCCESS' if ex.success else 'FAILED'} "
                    f"({ex.error_type or 'N/A'})"
                )
        
        return "\n".join(context_parts)
    
    def _call_llm(self, context: str) -> str:
        """Call the LLM API."""
        prompt = f"""You are an expert Python developer analyzing web scraper failures.

Context:
{context}

Please analyze this error pattern and provide:
1. Root cause analysis (what's likely causing this error)
2. Confidence level (0.0 to 1.0) in your analysis
3. Suggested fix (what should be done to fix it)
4. Explanation (why this fix should work)

Format your response as:
ROOT_CAUSE: [your analysis]
CONFIDENCE: [0.0-1.0]
SUGGESTED_FIX: [your suggestion]
EXPLANATION: [your explanation]
"""
        
        if self.client_type == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python developer specializing in web scraping."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent, factual responses
                max_tokens=500
            )
            return response.choices[0].message.content
        
        elif self.client_type == 'anthropic':
            # Anthropic API format
            system_message = "You are an expert Python developer specializing in web scraping."
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent, factual responses
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unknown client type: {self.client_type}")
    
    def _parse_llm_response(self, response: str, pattern: FailurePattern) -> LLMAnalysis:
        """Parse LLM response into LLMAnalysis object."""
        # Extract fields from response
        root_cause = ""
        confidence = 0.5  # Default
        suggested_fix = pattern.suggested_fix or "Review error and implement fix."
        explanation = ""
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('ROOT_CAUSE:'):
                root_cause = line.replace('ROOT_CAUSE:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                except ValueError:
                    pass
            elif line.startswith('SUGGESTED_FIX:'):
                suggested_fix = line.replace('SUGGESTED_FIX:', '').strip()
            elif line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()
        
        # If fields not found, use fallback
        if not root_cause:
            root_cause = f"Error pattern: {pattern.pattern_type} with {pattern.frequency} occurrences"
        
        if not explanation:
            explanation = f"Based on {pattern.frequency} occurrences of {pattern.error_type}"
        
        return LLMAnalysis(
            root_cause=root_cause,
            confidence=confidence,
            suggested_fix=suggested_fix,
            explanation=explanation
        )
    
    def _rule_based_analysis(self, pattern: FailurePattern) -> LLMAnalysis:
        """Fallback rule-based analysis when LLM is not available."""
        # Use the suggested fix from pattern analyzer
        suggested_fix = pattern.suggested_fix or "Review error and implement fix."
        
        # Generate simple root cause based on error type
        root_cause_map = {
            'HTTP_404_NOT_FOUND': "The requested URL or endpoint no longer exists or has been moved.",
            'HTTP_429_RATE_LIMIT': "Too many requests sent in a short time period.",
            'PARSING_SELECTOR_ERROR': "The HTML structure of the target website has changed.",
            'WEBSITE_STRUCTURE_CHANGE': "The website's HTML structure has been updated.",
            'RATE_LIMITING': "Request rate exceeds the server's rate limits.",
        }
        
        root_cause = root_cause_map.get(pattern.error_type, 
                                        f"Recurring error: {pattern.error_type}")
        
        return LLMAnalysis(
            root_cause=root_cause,
            confidence=pattern.confidence,
            suggested_fix=suggested_fix,
            explanation=f"This error has occurred {pattern.frequency} times since {pattern.first_seen.date()}."
        )

