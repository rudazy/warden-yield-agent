"""
================================================================================
    RESPONSE FORMATTER NODE
    Generates beautiful, structured output for the user.
    Updated for Warden Protocol Chat Tool compatibility.
================================================================================
"""

from __future__ import annotations
from typing import Any
from langchain_core.messages import AIMessage  # Added this import
from yield_agent.state import (
    AgentState,
    Recommendation,
    RiskTolerance,
    SUPPORTED_CHAINS,
)

# ==============================================================================
# FORMATTING CONSTANTS & HELPERS (Keep existing logic)
# ==============================================================================

DIVIDER_HEAVY = "=" * 70
DIVIDER_LIGHT = "-" * 70
DIVIDER_DOT = "." * 70

RISK_LABELS = {
    RiskTolerance.CONSERVATIVE: "Conservative (Safety First)",
    RiskTolerance.MODERATE: "Moderate (Balanced)",
    RiskTolerance.AGGRESSIVE: "Aggressive (Maximum Yield)",
}

CHAIN_SYMBOLS = {
    "ethereum": "ETH", "arbitrum": "ARB", "optimism": "OP",
    "polygon": "MATIC", "base": "BASE", "avalanche": "AVAX", "bsc": "BNB",
}

def format_currency(value: float, decimals: int = 2) -> str:
    if value >= 1_000_000_000: return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000: return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000: return f"${value / 1_000:.1f}K"
    return f"${value:,.{decimals}f}"

def format_apy(apy: float) -> str:
    return f"{apy:.1f}%" if apy >= 10 else f"{apy:.2f}%"

def format_risk_bar(risk_score: float) -> str:
    filled = int(risk_score)
    label = "LOW" if risk_score <= 3 else "MED" if risk_score <= 6 else "HIGH"
    return f"[{'*' * filled}{'.' * (10 - filled)}] {risk_score:.1f}/10 {label}"

def format_time(seconds: int) -> str:
    return f"{seconds // 60}m" if seconds >= 60 else f"{seconds}s"

# ==============================================================================
# SECTION FORMATTERS (Keep existing logic)
# ==============================================================================

def format_header(query, amount, token, risk_tolerance, num_results):
    risk_label = RISK_LABELS.get(risk_tolerance, "Moderate")
    return f"\n{DIVIDER_HEAVY}\n  YIELD INTELLIGENCE REPORT\n{DIVIDER_HEAVY}\n\n  Query: {query[:50]}...\n  Amount: {format_currency(amount)} {token}\n  Risk Profile: {risk_label}\n  Results: {num_results} found\n\n{DIVIDER_HEAVY}"

def format_recommendation(rec: Recommendation, detailed: bool = True) -> str:
    opp = rec.opportunity
    lines = [f"\n  #{rec.rank}  {opp.protocol}\n      {opp.symbol} on {opp.chain.title()}\n\n{DIVIDER_LIGHT}\n",
             f"      APY: {format_apy(opp.apy):<12} Net APY: {format_apy(rec.net_apy)}",
             f"      TVL: {format_currency(opp.tvl_usd):<12} Risk: {format_risk_bar(opp.risk_score)}\n"]
    if detailed:
        lines.append(f"      REASONING:\n      {rec.why_recommended[:200]}...\n")
        lines.append(f"      EXECUTION STEPS:\n")
        for step in rec.execution_steps[:3]: lines.append(f"      {step}")
    lines.append(f"\n{DIVIDER_LIGHT}")
    return "\n".join(lines)

def format_summary(recommendations):
    lines = ["\n  QUICK COMPARISON\n" + DIVIDER_LIGHT + "\n  Rank  Protocol             Chain      APY      Risk\n  " + "-" * 60]
    for rec in recommendations[:5]:
        opp = rec.opportunity
        lines.append(f"  {rec.rank:<5} {opp.protocol:<20} {opp.chain.title():<10} {format_apy(opp.apy):<8} {'*' * int(opp.risk_score/2)}")
    return "\n".join(lines) + "\n" + DIVIDER_LIGHT

def format_error(error, query):
    return f"\n{DIVIDER_HEAVY}\n  ERROR\n{DIVIDER_HEAVY}\n\n  {error}\n\n{DIVIDER_HEAVY}"

# ==============================================================================
# NODE FUNCTION (The Fix is Here)
# ==============================================================================

def format_response(state: AgentState) -> dict[str, Any]:
    """
    LangGraph node: Format the final response and add it to message history.
    """
    query = state.user_query or "Your yield query"
    
    # 1. Handle Errors
    if state.error:
        formatted = format_error(state.error, query)
        return {
            "formatted_response": formatted,
            "messages": [AIMessage(content=formatted)], # This shows the error in Chat
            "processing_step": "formatting_complete_error",
        }

    # 2. Handle No Results
    recommendations = state.recommendations
    if not recommendations:
        formatted = f"No yield opportunities found for your query: {query}"
        return {
            "formatted_response": formatted,
            "messages": [AIMessage(content=formatted)], # This shows the message in Chat
            "processing_step": "formatting_complete_no_results",
        }

    # 3. Generate the Beautiful Report
    sections = []
    sections.append(format_header(query, state.amount or 0, state.token or "USD", state.risk_tolerance, len(recommendations)))
    sections.append(format_summary(recommendations))
    
    for i, rec in enumerate(recommendations[:3]): # Show top 3 in detail
        sections.append(format_recommendation(rec, detailed=True))
    
    sections.append("\n  DISCLAIMER: This is not financial advice.\n" + DIVIDER_HEAVY)
    
    formatted = "\n".join(sections)

    # 4. RETURN THE MESSAGE (CRITICAL FOR CHAT UI)
    return {
        "formatted_response": formatted,
        "messages": [AIMessage(content=formatted)], # THIS MAKES IT APPEAR IN CHAT
        "processing_step": "formatting_complete",
    }
