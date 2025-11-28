"""
Tool infrastructure for agentic workflows.

Provides:
- Tool base class with standardized execute() interface
- Error handling and performance tracking
- Reusable tool pattern for agent actions

Architecture Reference: docs/architecture-agentic-text2sql.md Section 6.1
"""

from typing import Callable, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Tool:
    """
    Base tool class for agentic workflow.
    Architecture Reference: Section 6.1 (Tool Base Class)
    
    Tools are stateless, reusable components that agents can invoke.
    All tools follow standardized interface: execute(**kwargs) -> Dict
    """
    
    def __init__(self, name: str, description: str, function: Callable):
        """
        Initialize tool.
        
        Args:
            name: Tool identifier
            description: Human-readable description
            function: Callable to execute (receives **kwargs)
        """
        self.name = name
        self.description = description
        self.function = function
        logger.info(f"Tool initialized: {name}")
    
    def execute(self, **kwargs) -> Dict:
        """
        Execute the tool with standardized error handling.
        Architecture Reference: Section 6.1
        
        Returns:
            Dict with standardized format:
            - Success: {success: True, tool: str, result: Any, elapsed: float}
            - Failure: {success: False, tool: str, error: str, elapsed: float}
        """
        start_time = datetime.now()
        logger.info(f"Executing tool '{self.name}' with params: {list(kwargs.keys())}")
        
        try:
            result = self.function(**kwargs)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"Tool '{self.name}' succeeded in {elapsed:.3f}s")
            
            return {
                "success": True,
                "tool": self.name,
                "result": result,
                "elapsed": elapsed
            }
            
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"Tool '{self.name}' failed after {elapsed:.3f}s: {e}", exc_info=True)
            
            return {
                "success": False,
                "tool": self.name,
                "error": str(e),
                "elapsed": elapsed
            }

