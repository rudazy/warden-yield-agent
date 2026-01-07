"""
================================================================================
    INPUT PARSER NODE (Universal Version)
    Extracts structured data using both Regex and Groq AI.
    Handles Warden Protocol Chat Tool (messages) and local queries.
================================================================================
"""

from __future__ import annotations
import re
import os
from typing import Any, Optional
from langchain_groq import ChatGroq
from yield_agent.state import (
    AgentState,
    Intent,
    RiskTolerance,
    SUPPORTED_CHAINS,
)

# ==============================================================================
# EXISTING REGEX LOGIC (Kept as backup)
# ==============================================================================

KNOWN_TOKENS = {"USDC", "USDT", "DAI", "FRAX", "ETH", "WETH", "BTC", "WBTC", "MATIC", "BNB", "AVAX", "ARB", "OP"}
CHAIN_ALIASES = {"eth": "ethereum", "arb": "arbitrum", "op": "optimism", "matic": "polygon", "bnb": "bsc", "avax": "avalanche"}

def parse_amount_and_token(query: str) -> tuple[Optional[float], Optional[str]]:
    query_clean = query.lower()
    amount, token = None, None
    # Quick regex for k/m notation
    query_normalized = re.sub(r"(\d+)k\b", lambda m: str(int(m.group(1)) * 1000), query_clean)
    
    pattern = r"\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*([A-Za-z]{2,10})?"
    match = re.search(pattern, query_normalized)
    if match:
        amount = float(match.group(1).replace(",", ""))
        token_match = match.group(2)
        if token_match and token_match.upper() in KNOWN_TOKENS:
            token = token_match.upper()
    
    if not token:
        for t in KNOWN_TOKENS:
            if t.lower() in query_clean:
                token = t
                break
    return amount, token

def parse_chains(query: str) -> tuple[list[str], Optional[str]]:
    query_lower = query.lower()
    preferred, current = [], None
    for key in SUPPORTED_CHAINS.keys():
        if key in query_lower: preferred.append(key)
    for alias, key in CHAIN_ALIASES.items():
        if alias in query_lower and key not in preferred: preferred.append(key)
    return preferred, current

# ==============================================================================
# NODE FUNCTION (The "Brain")
# ==============================================================================

def parse_input(state: AgentState) -> dict[str, Any]:
    """
    Universal Parser: Handles Warden Chat messages and uses Groq AI.
    """
    # 1. Resolve the Query String
    # Try user_query first, then fallback to messages (Warden tool format)
    query = state.user_query
    if (not query or query == "") and state.messages:
        last_message = state.messages[-1]
        # Handle both Message objects and dictionaries
        if hasattr(last_message, "content"):
            query = last_message.content
        elif isinstance(last_message, dict):
            query = last_message.get("content", "")

    if not query:
        return {"processing_step": "input_empty_error", "error": "No query provided"}

    # 2. Use Groq AI for "Intelligence" (Warden Requirement)
    # This makes the agent "Smart"
    intent = Intent.YIELD_SEARCH
    try:
        llm = ChatGroq(
            model="llama-3.1-70b-versatile", 
            api_key=os.getenv("GROQ_API_KEY")
        )
        # Simple classification via LLM
        response = llm.invoke(f"Classify this DeFi query intent (yield_search, compare, route_only, risk_analysis): {query}")
        intent_str = response.content.lower()
        if "compare" in intent_str: intent = Intent.COMPARE_PROTOCOLS
        elif "route" in intent_str: intent = Intent.ROUTE_ONLY
        elif "risk" in intent_str: intent = Intent.RISK_ANALYSIS
    except Exception as e:
        print(f"LLM Error (falling back to regex): {e}")

    # 3. Use Regex for fast data extraction
    amount, token = parse_amount_and_token(query)
    preferred_chains, current_chain = parse_chains(query)
    
    # 4. Final state update
    target_chains = preferred_chains if preferred_chains else list(SUPPORTED_CHAINS.keys())

    return {
        "user_query": query, # Sync the query back to state
        "amount": amount,
        "token": token or "USDC", # Default to USDC if not found
        "preferred_chains": preferred_chains,
        "current_chain": current_chain,
        "intent": intent,
        "target_chains": target_chains,
        "processing_step": "input_parsed",
    }
