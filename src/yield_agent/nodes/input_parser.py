"""
================================================================================
    INPUT PARSER NODE
    Extracts structured data from natural language queries
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
# CONSTANTS & HELPERS
# ==============================================================================

KNOWN_TOKENS = {"USDC", "USDT", "DAI", "FRAX", "ETH", "WETH", "BTC", "WBTC", "MATIC", "BNB", "AVAX", "ARB", "OP"}
CHAIN_ALIASES = {"eth": "ethereum", "arb": "arbitrum", "op": "optimism", "matic": "polygon", "bnb": "bsc", "avax": "avalanche"}

def parse_amount_and_token(query: str) -> tuple[Optional[float], Optional[str]]:
    query_clean = query.lower()
    query_normalized = re.sub(r"(\d+)k\b", lambda m: str(int(m.group(1)) * 1000), query_clean)
    amount, token = None, None
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

def parse_risk_tolerance(query: str) -> RiskTolerance:
    query_lower = query.lower()
    if any(k in query_lower for k in ["safe", "low risk", "conservative"]): return RiskTolerance.CONSERVATIVE
    if any(k in query_lower for k in ["aggressive", "high risk", "degen"]): return RiskTolerance.AGGRESSIVE
    return RiskTolerance.MODERATE

def parse_intent(query: str) -> Intent:
    query_lower = query.lower()
    if any(k in query_lower for k in ["compare", "vs"]): return Intent.COMPARE_PROTOCOLS
    if any(k in query_lower for k in ["bridge", "move"]): return Intent.ROUTE_ONLY
    if any(k in query_lower for k in ["risk", "audit"]): return Intent.RISK_ANALYSIS
    return Intent.YIELD_SEARCH

def parse_exclusions(query: str) -> list[str]:
    return []

# ==============================================================================
# MAIN NODE FUNCTION
# ==============================================================================

def parse_input(state: AgentState) -> dict[str, Any]:
    # 1. Resolve Query from State or Messages (Warden Chat Tool support)
    query = state.user_query
    if (not query or query == "") and state.messages:
        last_message = state.messages[-1]
        if hasattr(last_message, "content"): query = last_message.content
        elif isinstance(last_message, dict): query = last_message.get("content", "")

    if not query:
        return {"processing_step": "input_empty_error", "error": "No query provided"}

    # 2. Use Groq AI for Intelligence
    intent = parse_intent(query)
    try:
        llm = ChatGroq(model="llama-3.1-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
        response = llm.invoke(f"Classify intent (yield_search, compare, route_only, risk_analysis): {query}")
        intent_str = response.content.lower()
        if "compare" in intent_str: intent = Intent.COMPARE_PROTOCOLS
        elif "route" in intent_str: intent = Intent.ROUTE_ONLY
        elif "risk" in intent_str: intent = Intent.RISK_ANALYSIS
    except Exception: pass

    # 3. Extract Data
    amount, token = parse_amount_and_token(query)
    preferred_chains, current_chain = parse_chains(query)
    risk_tolerance = parse_risk_tolerance(query)
    exclusions = parse_exclusions(query)
    target_chains = preferred_chains if preferred_chains else list(SUPPORTED_CHAINS.keys())

    return {
        "user_query": query,
        "amount": amount,
        "token": token or "USDC",
        "preferred_chains": preferred_chains,
        "current_chain": current_chain,
        "risk_tolerance": risk_tolerance,
        "intent": intent,
        "excluded_protocols": exclusions,
        "target_chains": target_chains,
        "processing_step": "input_parsed",
    }
