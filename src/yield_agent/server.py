"""
================================================================================
    YIELD AGENT API SERVER
    FastAPI server exposing the LangGraph agent via REST API
================================================================================
"""

import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from yield_agent.graph import create_yield_agent, run_agent_async
from yield_agent.state import AgentState, RiskTolerance


# ==============================================================================
# API KEY AUTHENTICATION
# ==============================================================================

API_KEY = os.getenv("AGENT_API_KEY", "yield-agent-secret-key")


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify the API key from request header."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================


class AgentRequest(BaseModel):
    """Request model for agent invocation."""
    query: str
    amount: Optional[float] = None
    token: Optional[str] = None
    current_chain: Optional[str] = None
    risk_tolerance: Optional[str] = "moderate"
    preferred_chains: Optional[list[str]] = []
    excluded_protocols: Optional[list[str]] = []
    min_tvl: Optional[float] = 100000


class AgentResponse(BaseModel):
    """Response model from agent."""
    success: bool
    response: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent: str
    version: str


# ==============================================================================
# FASTAPI APP
# ==============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent on startup."""
    print("Initializing Yield Intelligence Agent...")
    app.state.agent = create_yield_agent()
    print("Agent ready!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Cross-Chain Yield Intelligence Agent",
    description="AI agent that finds and ranks the best DeFi yield opportunities across multiple blockchain networks",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# ENDPOINTS
# ==============================================================================


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic info."""
    return HealthResponse(
        status="online",
        agent="Cross-Chain Yield Intelligence Agent",
        version="1.0.0",
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        agent="Cross-Chain Yield Intelligence Agent",
        version="1.0.0",
    )


@app.post("/invoke", response_model=AgentResponse, dependencies=[Depends(verify_api_key)])
async def invoke_agent(request: AgentRequest):
    """
    Invoke the yield intelligence agent with a natural language query.
    
    Requires X-API-Key header for authentication.
    """
    try:
        response = await run_agent_async(
            query=request.query,
            amount=request.amount,
            token=request.token,
            current_chain=request.current_chain,
            risk_tolerance=request.risk_tolerance,
            preferred_chains=request.preferred_chains,
            excluded_protocols=request.excluded_protocols,
            min_tvl=request.min_tvl,
        )
        
        return AgentResponse(
            success=True,
            response=response,
        )
    except Exception as e:
        return AgentResponse(
            success=False,
            response="",
            error=str(e),
        )


@app.post("/chat", response_model=AgentResponse, dependencies=[Depends(verify_api_key)])
async def chat(request: AgentRequest):
    """
    Chat endpoint - alias for /invoke.
    
    Requires X-API-Key header for authentication.
    """
    return await invoke_agent(request)


# ==============================================================================
# RUN SERVER
# ==============================================================================


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
