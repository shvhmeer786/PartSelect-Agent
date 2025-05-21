"""
Utility functions for intent classification.
Provides methods that combine rule-based and LLM-based intent classification.
"""

import os
import logging
from typing import Optional
from .validators import extract_intent, IntentType, is_in_scope
from .tools import IntentClassificationTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_intent(
    query: str, 
    use_llm_fallback: bool = True,
    deepseek_api_key: Optional[str] = None
) -> IntentType:
    """
    Classify user intent using a hybrid approach:
    1. First, try rule-based classification
    2. If that returns out_of_scope and use_llm_fallback is True, try LLM-based classification
    
    Args:
        query: User query text
        use_llm_fallback: Whether to use LLM as fallback when rule-based returns out_of_scope
        deepseek_api_key: API key for Deepseek LLM, if None will try to get from environment
        
    Returns:
        The classified intent
    """
    # Step 1: Try rule-based classification first (faster and cheaper)
    rule_based_intent = extract_intent(query)
    
    # If rule-based gives a conclusive result (not out_of_scope), return it
    if rule_based_intent != 'out_of_scope':
        logger.info(f"Rule-based intent classification: '{query}' -> {rule_based_intent}")
        return rule_based_intent
    
    # Step 2: If rule-based is inconclusive and LLM fallback is enabled, try the LLM
    if use_llm_fallback:
        # Get the Deepseek API key if not provided
        if not deepseek_api_key:
            deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if not deepseek_api_key:
            logger.warning("No Deepseek API key available for LLM fallback classification")
            return rule_based_intent
        
        try:
            # Create and use the LLM classification tool
            llm_tool = IntentClassificationTool(deepseek_api_key=deepseek_api_key)
            llm_intent = llm_tool._run(query)
            
            logger.info(f"LLM fallback intent classification: '{query}' -> {llm_intent}")
            return llm_intent
            
        except Exception as e:
            logger.error(f"Error using LLM fallback for intent classification: {e}")
    
    # Default to rule-based result if LLM fallback is disabled or fails
    return rule_based_intent

def is_query_in_scope(
    query: str,
    use_llm_fallback: bool = True,
    deepseek_api_key: Optional[str] = None
) -> bool:
    """
    Determine if a query is in scope using both rule-based and LLM approaches.
    
    Args:
        query: User query text
        use_llm_fallback: Whether to use LLM as fallback for ambiguous queries
        deepseek_api_key: API key for Deepseek LLM, if None will try to get from environment
        
    Returns:
        True if the query is in scope, False otherwise
    """
    # First check with rule-based approach
    if is_in_scope(query):
        return True
    
    # If rule-based says it's out of scope but we want LLM fallback
    if use_llm_fallback:
        intent = classify_intent(query, use_llm_fallback, deepseek_api_key)
        # If LLM classified it as anything other than out_of_scope, consider it in scope
        return intent != 'out_of_scope'
    
    return False 