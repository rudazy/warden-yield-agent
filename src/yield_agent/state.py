"""
================================================================================
    STATE DEFINITIONS
    Core data structures for the Yield Intelligence Agent
================================================================================
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Optional, Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages

# ==============================================================================
# ENUMS
# ==============================================================================

class RiskTolerance(str, Enum):
    """User's risk appetite for yield strategies."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class ILRisk(str, Enum):
    """Impermanent Loss risk level for liquidity pools."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Intent(str, Enum):
    """Classified user intent types."""
    YIELD_SEARCH = "yield_search"
    COMPARE_PROTOCOLS = "compare"
    ROUTE_ONLY = "route_only"
    RISK_ANALYSIS = "risk_analysis"
    GENERAL_QUESTION = "general"

# ==============================================================================
# CHAIN CONFIGURATION
# ==============================================================================

SUPPORTED_CHAINS: dict[str, dict[str, Any]] = {
    "ethereum": {
        "chain_id": 1,
        "name": "Ethereum",
        "symbol": "ETH",
        "color": "#627EEA",
        "explorer": "https://etherscan.io",
        "defillama_slug": "Ethereum",
        "lifi_key": "ETH",
    },
    "arbitrum": {
        "chain_id": 42161,
        "name": "Arbitrum One",
        "symbol": "ETH",
        "color": "#28A0F0",
        "explorer": "https://arbiscan.io",
        "defillama_slug": "Arbitrum",
        "lifi_key": "ARB",
    },
    "optimism": {
        "chain_id": 10,
        "name": "Optimism",
        "symbol": "ETH",
        "color": "#FF0420",
        "explorer": "https://optimistic.etherscan.io",
        "defillama_slug": "Optimism",
        "lifi_key": "OPT",
    },
    "polygon": {
        "chain_id": 137,
        "name": "Polygon",
        "symbol": "MATIC",
        "color": "#8247E5",
        "explorer": "https://polygonscan.com",
        "defillama_slug": "Polygon",
        "lifi_key": "POL",
    },
    "base": {
        "chain_id": 8453,
        "name": "Base",
        "symbol": "ETH",
        "color": "#0052FF",
        "explorer": "https://basescan.org",
        "defillama_slug": "Base",
        "lifi_key": "BAS",
    },
    "avalanche": {
        "chain_id": 43114,
        "name": "Avalanche",
        "symbol": "AVAX",
        "color": "#E84142",
        "explorer": "https://snowtrace.io",
        "defillama_slug": "Avalanche",
        "lifi_key": "AVA",
    },
    "bsc": {
        "chain_id": 56,
        "name": "BNB Chain",
        "symbol": "BNB",
        "color": "#F0B90B",
        "explorer": "https://bscscan.com",
        "defillama_slug": "BSC",
        "lifi_key": "BSC",
    },
}

# ==============================================================================
# DATA MODELS
# ==============================================================================

class YieldOpportunity(BaseModel):
    pool_id: str = Field(..., description="Unique pool identifier")
    protocol: str = Field(..., description="Protocol name")
    protocol_slug: str = Field(..., description="Protocol slug for URLs")
    chain: str = Field(..., description="Chain identifier")
    pool_name: str = Field(..., description="Human-readable pool name")
    symbol: str = Field(..., description="Pool symbol")
    underlying_tokens: list[str] = Field(default_factory=list)
    reward_tokens: list[str] = Field(default_factory=list)
    apy: float = Field(..., ge=0)
    apy_base: float = Field(default=0, ge=0)
    apy_reward: float = Field(default=0, ge=0)
    apy_7d_avg: Optional[float] = Field(default=None)
    apy_30d_avg: Optional[float] = Field(default=None)
    tvl_usd: float = Field(..., ge=0)
    risk_score: float = Field(..., ge=1, le=10)
    il_risk: ILRisk = Field(default=ILRisk.NONE)
    audited: bool = Field(default=False)
    audit_links: list[str] = Field(default_factory=list)
    protocol_age_days: int = Field(default=0, ge=0)
    pool_url: Optional[str] = Field(default=None)
    last_updated: Optional[str] = Field(default=None)

    class Config:
        use_enum_values = True

class BridgeRoute(BaseModel):
    from_chain: str = Field(...)
    from_chain_id: int = Field(...)
    to_chain: str = Field(...)
    to_chain_id: int = Field(...)
    token: str = Field(...)
    token_address: str = Field(...)
    amount: float = Field(...)
    bridge_name: str = Field(...)
    estimated_time_seconds: int = Field(...)
    gas_cost_usd: float = Field(..., ge=0)
    bridge_fee_usd: float = Field(..., ge=0)
    total_cost_usd: float = Field(..., ge=0)
    estimated_output: float = Field(...)
    slippage_percent: float = Field(default=0.5)
    tx_data: Optional[dict[str, Any]] = Field(default=None)

class GasEstimate(BaseModel):
    chain: str = Field(...)
    chain_id: int = Field(...)
    gas_price_slow: float = Field(...)
    gas_price_standard: float = Field(...)
    gas_price_fast: float = Field(...)
    swap_cost_usd: float = Field(...)
    deposit_cost_usd: float = Field(...)
    base_fee: Optional[float] = Field(default=None)
    priority_fee: Optional[float] = Field(default=None)
    last_updated: str = Field(...)

class Recommendation(BaseModel):
    rank: int = Field(..., ge=1)
    opportunity: YieldOpportunity = Field(...)
    input_amount: float = Field(...)
    input_token: str = Field(...)
    earnings_30d: float = Field(...)
    earnings_1y: float = Field(...)
    requires_bridge: bool = Field(default=False)
    bridge_route: Optional[BridgeRoute] = Field(default=None)
    net_apy: float = Field(...)
    total_entry_cost_usd: float = Field(default=0)
    why_recommended: str = Field(...)
    warnings: list[str] = Field(default_factory=list)
    execution_steps: list[str] = Field(default_factory=list)

# ==============================================================================
# AGENT STATE
# ==============================================================================

class AgentState(BaseModel):
    """
    Complete state of the Yield Intelligence Agent.
    Updated to support LangGraph conversation history.
    """
    # --------------------------------------------------------------------------
    # INPUT FIELDS
    # --------------------------------------------------------------------------
    # Added messages field to support UI chat tools
    messages: Annotated[list[Any], add_messages] = Field(default_factory=list)
    
    # Made user_query optional to prevent validation errors
    user_query: str = Field(default="", description="Original natural language query")
    
    amount: Optional[float] = Field(default=None, description="Amount to invest")
    token: Optional[str] = Field(default=None, description="Token symbol")
    current_chain: Optional[str] = Field(default=None, description="User current chain")
    risk_tolerance: RiskTolerance = Field(
        default=RiskTolerance.MODERATE, description="User risk tolerance"
    )
    preferred_chains: list[str] = Field(
        default_factory=list, description="Preferred chains, empty means all"
    )
    excluded_protocols: list[str] = Field(
        default_factory=list, description="Protocols to exclude"
    )
    min_tvl: float = Field(default=100_000, description="Minimum TVL requirement")

    # --------------------------------------------------------------------------
    # PROCESSING & DATA FIELDS
    # --------------------------------------------------------------------------
    intent: Optional[Intent] = Field(default=None, description="Classified intent")
    target_chains: list[str] = Field(default_factory=list)
    processing_step: str = Field(default="initialized")
    yield_opportunities: list[YieldOpportunity] = Field(default_factory=list)
    bridge_routes: list[BridgeRoute] = Field(default_factory=list)
    gas_estimates: list[GasEstimate] = Field(default_factory=list)

    # --------------------------------------------------------------------------
    # OUTPUT FIELDS
    # --------------------------------------------------------------------------
    recommendations: list[Recommendation] = Field(default_factory=list)
    reasoning: str = Field(default="")
    execution_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    formatted_response: str = Field(default="")

    # --------------------------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------------------------
    error: Optional[str] = Field(default=None)
    error_details: Optional[dict[str, Any]] = Field(default=None)

    class Config:
        use_enum_values = True

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def merge_opportunities(existing, new):
    seen_ids = {opp.pool_id for opp in existing}
    merged = list(existing)
    for opp in new:
        if opp.pool_id not in seen_ids:
            merged.append(opp)
            seen_ids.add(opp.pool_id)
    return merged

def merge_warnings(existing, new):
    return list(dict.fromkeys(existing + new))

def get_chain_by_id(chain_id):
    for key, config in SUPPORTED_CHAINS.items():
        if config["chain_id"] == chain_id:
            return {"key": key, **config}
    return None

def get_chain_by_name(name):
    name_lower = name.lower()
    if name_lower in SUPPORTED_CHAINS:
        return {"key": name_lower, **SUPPORTED_CHAINS[name_lower]}
    for key, config in SUPPORTED_CHAINS.items():
        if config["name"].lower() == name_lower:
            return {"key": key, **config}
    return None
