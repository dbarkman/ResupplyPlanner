# System Name Autocomplete

This document describes the fast in-memory autocomplete system for system names.

## Overview

The autocomplete system loads all system names from the database into memory for sub-millisecond response times. This solves the performance issue where database ILIKE queries were taking 3+ minutes.

## Setup

### 1. Export System Names

First, export all system names from the database to a text file:

```bash
python scripts/export_system_names.py
```

This creates `data/system_names.txt` with all system names, one per line, sorted alphabetically.

### 2. Install Dependencies

Make sure you have FastAPI and uvicorn installed:

```bash
pip install fastapi uvicorn
```

### 3. Run the API Server

Start the FastAPI server:

```bash
python run_api.py
```

The server will start on `http://localhost:8000` and automatically load the system names into memory.

## Testing with curl

### Basic Autocomplete Search

```bash
# Search for systems starting with "Sol"
curl "http://localhost:8000/api/autocomplete?q=Sol&limit=5"

# Search for systems starting with "Diag" (the slow query that was taking 3+ minutes)
curl "http://localhost:8000/api/autocomplete?q=Diag&limit=10"
```

### Service Information

```bash
# Get API info
curl "http://localhost:8000/"

# Get service statistics
curl "http://localhost:8000/api/stats"

# Health check
curl "http://localhost:8000/api/health"

# Test multiple queries
curl "http://localhost:8000/api/test"
```

## Testing with Postman

### Autocomplete Endpoint

- **Method:** GET
- **URL:** `http://localhost:8000/api/autocomplete`
- **Query Parameters:**
  - `q` (required): Search query (e.g., "Sol", "Diag", "HIP")
  - `limit` (optional): Maximum results (default: 10, max: 100)

### Example Response

```json
{
  "query": "Sol",
  "results": [
    "Sol",
    "Sola",
    "Solace",
    "Solana",
    "Solar"
  ],
  "count": 5,
  "limit": 10,
  "response_time_ms": 0.15,
  "success": true
}
```

## Performance

- **Load time:** ~1-5 seconds for 158M system names
- **Memory usage:** ~2.4 GB RAM
- **Search time:** ~0.1-1ms per query
- **Response time:** Sub-millisecond for most queries

## Architecture

### Files

- `scripts/export_system_names.py` - Exports system names from database
- `src/app/autocomplete.py` - In-memory autocomplete service
- `src/app/api.py` - FastAPI endpoints
- `run_api.py` - Server runner script
- `data/system_names.txt` - System names data file (generated)

### Key Components

1. **SystemAutocomplete Class** - Loads names into memory and provides binary search
2. **FastAPI Endpoints** - REST API for web UI integration
3. **Export Script** - One-time database export to text file

## Integration with Web UI

The autocomplete endpoint is designed to work with standard autocomplete UI components:

```javascript
// Example JavaScript usage
fetch('/api/autocomplete?q=Sol&limit=10')
  .then(response => response.json())
  .then(data => {
    // Update autocomplete dropdown with data.results
    console.log(data.results);
  });
```

## Maintenance

### Updating System Names

When new systems are added to the database:

1. Re-run the export script:
   ```bash
   python scripts/export_system_names.py
   ```

2. Restart the API server:
   ```bash
   # Stop the current server (Ctrl+C)
   python run_api.py
   ```

### Monitoring

Use the `/api/stats` endpoint to monitor:
- Total systems loaded
- Memory usage
- Load time
- Service status

## Troubleshooting

### Common Issues

1. **File not found error:** Make sure to run the export script first
2. **Memory issues:** Ensure your server has at least 3GB available RAM
3. **Slow startup:** The initial load takes 1-5 seconds for 158M names

### Performance Tuning

- The system uses binary search for O(log n) performance
- Results are limited to prevent memory issues
- Case-insensitive matching is built-in 