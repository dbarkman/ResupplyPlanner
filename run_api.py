#!/usr/bin/env python3

"""
Run the FastAPI server for testing autocomplete endpoints.
"""

import uvicorn
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.app.api import app

if __name__ == "__main__":
    print("Starting Resupply Planner API server...")
    print("Available endpoints:")
    print("  GET  /                    - API info")
    print("  GET  /api/autocomplete    - Search system names")
    print("  GET  /api/stats           - Service statistics")
    print("  GET  /api/health          - Health check")
    print("  GET  /api/test            - Test queries")
    print()
    print("Example curl commands:")
    print("  curl 'http://localhost:8000/api/autocomplete?q=Sol&limit=5'")
    print("  curl 'http://localhost:8000/api/stats'")
    print("  curl 'http://localhost:8000/api/test'")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    ) 