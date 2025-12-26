# Endpoint Registration Instructions

## Current Status

The new engine API endpoints have been created but are not yet registered with the FastAPI application.

## Files Created

1. **app/api/endpoints/handwriting_endpoints.py** - Handwriting exam submission endpoint
2. **app/api/endpoints/practice_endpoints.py** - Topic practice session endpoint  
3. **app/api/schemas/handwriting_schemas.py** - Request/response schemas
4. **app/api/schemas/practice_schemas.py** - Request/response schemas

## Imports Added

The gateway.py file has been updated with imports:
```python
from app.api.endpoints.handwriting_endpoints import router as handwriting_router
from app.api.endpoints.practice_endpoints import router as practice_router
```

## What Needs to be Done

The FastAPI application entry point needs to include these routers. Based on the running server command:
```
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

There should be an `app.main` module (or similar) where the FastAPI app is created.

## Registration Code Needed

Wherever the FastAPI `app` instance is created, add:

```python
# Import the routers
from app.api.endpoints.handwriting_endpoints import router as handwriting_router  
from app.api.endpoints.practice_endpoints import router as practice_router

# Register the routers
app.include_router(handwriting_router)
app.include_router(practice_router)
```

Alternatively, if using the gateway router pattern, you could include them in the gateway router:

```python
# In app/api/gateway.py, add at the end of the file:
from app.api.endpoints.handwriting_endpoints import router as handwriting_router
from app.api.endpoints.practice_endpoints import router as practice_router

# Note: These are already imported, just need to be included in the router export
```

## Verification

After registration, restart the server and visit:
```
http://localhost:8000/docs
```

You should see:
- `POST /api/v1/exams/handwriting/submit`
- `GET /api/v1/exams/handwriting/status/{trace_id}`
- `POST /api/v1/practice/create`
- `GET /api/v1/practice/session/{session_id}`
- `POST /api/v1/practice/session/{session_id}/submit`

## Note

The exact location to add the router registration depends on your FastAPI app initialization structure. Look for where the gateway router is being included in the main app.
