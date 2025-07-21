"""
FastAPI application with autocomplete endpoints for system names.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import time
import logging

from .autocomplete import autocomplete_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Resupply Planner API",
    description="API for Elite: Dangerous Fleet Carrier Route Planner",
    version="1.0.0"
)

# Add CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Load system names into memory when the application starts."""
    try:
        logger.info("Starting up autocomplete service...")
        autocomplete_service.load_names()
        logger.info("Autocomplete service ready!")
    except Exception as e:
        logger.error(f"Failed to load autocomplete service: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "Resupply Planner API",
        "version": "1.0.0",
        "endpoints": {
            "autocomplete": "/api/autocomplete",
            "stats": "/api/stats",
            "health": "/api/health"
        }
    }


@app.get("/api/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Search query (system name prefix)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results")
) -> Dict[str, Any]:
    """
    Search for system names that start with the given query.
    
    Args:
        q: The search query (prefix to match)
        limit: Maximum number of results to return (1-100)
        
    Returns:
        JSON response with matching system names and metadata
    """
    start_time = time.time()
    
    try:
        # Perform the search
        results = autocomplete_service.search(q, limit)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "query": q,
            "results": results,
            "count": len(results),
            "limit": limit,
            "response_time_ms": round(response_time, 2),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get statistics about the autocomplete service.
    
    Returns:
        JSON response with service statistics
    """
    try:
        stats = autocomplete_service.get_stats()
        return {
            "service": "system_autocomplete",
            "stats": stats,
            "success": True
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        JSON response with service health status
    """
    try:
        stats = autocomplete_service.get_stats()
        return {
            "status": "healthy" if stats["loaded"] else "unhealthy",
            "loaded": stats["loaded"],
            "total_systems": stats["total_systems"],
            "memory_mb": round(stats["estimated_memory_mb"], 1),
            "success": True
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "success": False
        }


# Test endpoint for development
@app.get("/api/test")
async def test_autocomplete() -> Dict[str, Any]:
    """
    Test endpoint with some example queries.
    
    Returns:
        JSON response with test results
    """
    test_queries = ["Sol", "Diag", "HIP", "Col", "Barn"]
    results = {}
    
    for query in test_queries:
        start_time = time.time()
        matches = autocomplete_service.search(query, 5)
        response_time = (time.time() - start_time) * 1000
        
        results[query] = {
            "matches": matches,
            "count": len(matches),
            "response_time_ms": round(response_time, 2)
        }
    
    return {
        "test_queries": results,
        "success": True
    } 